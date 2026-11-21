"""Combined bridge writes must remain visible to a warmed M5 dedup index."""
from dataclasses import asdict

import numpy as np
import pytest

from lingshu.core.core import MemoryLayer, SpacetimeMemoryEngine
from lingshu.nn.hex_hier import HexHierNet, OBJ
from lingshu.nn.hex_text import ingest_perception_cards, query_visual_memory


def _network(*, uniform=False):
    net = HexHierNet(n_kernels=1, stacked=False)
    vector = np.zeros_like(net.get_vec())
    vector[0] = 1
    if not uniform:
        head = vector[7:].reshape(net.head.shape)
        for index, color in enumerate(("red", "green", "blue")):
            head[OBJ.index("circle|" + color), index + 1] = 100
    net.set_vec(vector)
    return net


def _ingest(engine, color, *, uniform=False):
    lattice = np.zeros((1, 4, 4, 3))
    lattice[0, -1, -1, {"red": 0, "green": 1, "blue": 2}[color]] = 1
    result = ingest_perception_cards(
        engine, _network(uniform=uniform), lattice, image_id="combined",
        time_window=(1.0, 100.0), timestamp=50.0,
        p_threshold=0.99 if uniform else 0.25,
        min_margin=0.5 if uniform else 0.03,
    )
    assert result["node_ids"] == ["m55_card_combined_r8"]
    return engine.store.get_node(result["node_ids"][0])


def _warm(engine):
    index = engine.store._dedup_index_for("image", engine._strip_zero_width)
    assert engine.store._dedup_indices["image"] is index


def _exact_match(engine, node):
    candidate, similarity = engine._dedup_search_fast(
        "image", engine._strip_zero_width(node.content), frozenset(),
        node.condition_space, 1.0,
    )
    return candidate, similarity


def _answer(engine):
    return query_visual_memory(engine, "图像里有什么", image_id="combined")


def test_warm_index_sees_new_card_and_same_id_rewrite():
    engine = SpacetimeMemoryEngine(":memory:")
    try:
        _warm(engine)
        old = _ingest(engine, "blue")
        candidate, similarity = _exact_match(engine, old)
        assert candidate is not None and candidate.id == old.id and similarity == 1.0
        assert "蓝圆形" in _answer(engine)["answer"]

        _warm(engine)
        current = _ingest(engine, "green")
        assert current.id == old.id and current.content != old.content
        candidate, similarity = _exact_match(engine, current)
        assert candidate is not None and candidate.id == current.id and similarity == 1.0
        assert _exact_match(engine, old)[0] is None, "old card content survived in the dedup index"
        answer = _answer(engine)
        assert answer["found"] and "绿圆形" in answer["answer"] and "蓝" not in answer["answer"]

        duplicate = engine.add_perception(
            current.content, modality="image", tags=current.tags,
            condition_space=current.condition_space,
        )
        assert duplicate.id == current.id and getattr(duplicate, "merged", False)
        assert engine.store.get_node(current.id).semantic_coordinates["color"] == "green"
    finally:
        engine.close()


def test_cross_connection_rewrite_and_rollback_preserve_latest_card(tmp_path):
    database = str(tmp_path / "combined.db")
    reader = SpacetimeMemoryEngine(database)
    writer = SpacetimeMemoryEngine(database)
    try:
        old = _ingest(reader, "blue")
        _warm(reader)
        current = _ingest(writer, "green")
        candidate, similarity = _exact_match(reader, current)
        assert candidate is not None and candidate.id == current.id and similarity == 1.0
        assert _exact_match(reader, old)[0] is None
        assert "绿圆形" in _answer(reader)["answer"]

        with pytest.raises(RuntimeError, match="abort combined card write"):
            with reader.store._tx():
                tentative = _ingest(reader, "red")
                assert "红圆形" in _answer(reader)["answer"]
                assert "绿圆形" in _answer(writer)["answer"]
                _warm(reader)
                assert _exact_match(reader, tentative)[0] is not None
                raise RuntimeError("abort combined card write")
        assert "绿圆形" in _answer(reader)["answer"]
        assert "绿圆形" in _answer(writer)["answer"]
        assert _exact_match(reader, tentative)[0] is None
        assert _exact_match(reader, current)[0] is not None
    finally:
        writer.close()
        reader.close()


def test_layer_change_refusal_preserves_accepted_card_and_index():
    engine = SpacetimeMemoryEngine(":memory:")
    try:
        old = _ingest(engine, "blue")
        assert old.layer == MemoryLayer.KNOWLEDGE
        original = asdict(old)
        _warm(engine)

        # An uncertain card requests CONTEXT at the same deterministic ID.
        # The existing #127 rule rejects that layer change atomically; the
        # bridge must not delete or silently replace the accepted fact.
        with pytest.raises(PermissionError, match=r"禁止同 id 换层.*#127"):
            _ingest(engine, "blue", uniform=True)

        assert asdict(engine.store.get_node(old.id)) == original
        candidate, similarity = _exact_match(engine, old)
        assert candidate is not None and candidate.id == old.id and similarity == 1.0
        result = _answer(engine)
        assert result["found"] is True and "蓝圆形" in result["answer"]
    finally:
        engine.close()
