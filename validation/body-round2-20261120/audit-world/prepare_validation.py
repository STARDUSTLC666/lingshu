from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

root = Path(r"[workspace]/lingshu/work\lingshu-body-collision-velocity-20261120")
doc = root / "docs/intake/body-export-v0.1/_export_manifest.json"
raw = doc.read_text(encoding="utf-8")
data = json.loads(raw)
record = next(a for a in data["blocks"]["world"]["files"] if a["file"] == "scene_simulator.py")
source = (root / "lingshu/world/scene_simulator.py").read_bytes().replace(b"\r\n", b"\n")
newhash = hashlib.sha256(source).hexdigest()[:len(record["sha256"])]
assert raw.count('"sha256": "' + record["sha256"] + '"') == 1
doc.write_text(raw.replace('"sha256": "' + record["sha256"] + '"',
                           '"sha256": "' + newhash + '"', 1), encoding="utf-8", newline="\n")

tests = [a.get("name") for a in ET.parse(Path(__file__).with_name("fixed-guard.xml")).findall(".//testcase")]
good = {"test_adding_a_distant_box_keeps_the_same_closed_form_trajectory[0]",
        "test_adding_a_distant_box_keeps_the_same_closed_form_trajectory[1]",
        "test_real_collision_still_reseeds_at_the_correct_contact_surface",
        "test_initial_overlap_still_reseeds_after_penetration_correction",
        "test_kinematic_velocity_still_records_collision_corrected_displacement",
        "test_fully_overlapping_static_boxes_keep_existing_contact_velocity"}
good.update(a for a in tests if a.startswith("test_start_contact_keeps_existing_reseed_semantics["))
def mutation(name, test, assertion, old, new):
    return {"name": name, "test": test, "assertion": assertion,
            "changes": [{"file": "lingshu/world/scene_simulator.py", "class": "SceneSimulator",
                         "method": "_resolve_collisions", "old": old, "new": new}]}
spec = {"guard": "tests/test_scene_collision_freeflight_velocity.py", "total": len(tests),
        "sources": ["lingshu/world/scene_simulator.py"],
        "baseline_failures": [a for a in tests if a not in good],
        "mutations": [
            mutation("replace_endpoint_with_average_again", "test_noncontact_keeps_instantaneous_endpoint_velocity",
                     "SCENE_ENDPOINT_IS_NOT_MEAN", "if eid not in contacted:", "if False:"),
            mutation("reseed_unmodified_endpoint", "test_noncontact_keeps_original_physics_state",
                     "SCENE_NO_CONTACT_RESEEDED", "                if eid not in contacted:\n                    continue",
                     "                if eid not in contacted:\n                    self._reseed_physics(eid)\n                    continue"),
            mutation("skip_reseed_for_real_contacts", "test_real_collision_still_reseeds_at_the_correct_contact_surface",
                     "SCENE_CONTACT_WAS_NOT_RESEEDED", "if eid not in contacted:", "if True:"),
            mutation("drop_contact_reseed", "test_real_collision_still_reseeds_at_the_correct_contact_surface",
                     "SCENE_CONTACT_WAS_NOT_RESEEDED", "            self._reseed_physics(eid)", "            pass"),
            mutation("keep_precollision_kinematic_velocity", "test_kinematic_velocity_still_records_collision_corrected_displacement",
                     "SCENE_KINEMATIC_DISPLACEMENT_CHANGED", "                e.velocity = moved", "                pass")
        ]}
position_only = mutation("use_position_equality_instead_of_contact", "test_fully_overlapping_static_boxes_keep_existing_contact_velocity",
                         "SCENE_STATIC_CONTACT_VELOCITY_CHANGED", "if eid not in contacted:", "if e.pos == proposed[eid]:")
position_only["changes"].insert(0, {"file": "lingshu/world/scene_simulator.py", "class": "SceneSimulator",
                                  "method": "_resolve_collisions", "old": "        start = self._tick_start_pos",
                                  "new": "        start = self._tick_start_pos\n        proposed = {eid: self.entities[eid].pos for eid in ids}"})
spec["mutations"].append(position_only)
target = root / "tests/fixtures/scene_collision_freeflight_velocity_mutations.json"
target.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"manifest_hash": newhash, "guard_total": len(tests), "baseline_failures": len(spec["baseline_failures"])}, indent=2))
