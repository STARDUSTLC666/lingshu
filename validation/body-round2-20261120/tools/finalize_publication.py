"""Read/append one immutable final-evidence block to existing PR/intake bodies."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent / "final-publication"
CAPTURE = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
TARGET = "FuRongJun-1999/lingshu"
BOUNTY = "FuRongJun-1999/dsh-bounty"
ITEMS = {
    1477: (2791, "e821bbb1fac57fa638640e3caf153caf7f1b1973", "audit-circular"),
    1478: (2792, "41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50", "audit-core"),
    1479: (2793, "13952c82874fb9ee19a4f1b660e3144134367a53", "audit-world"),
    1480: (2794, "a357dbbe96905848fd81b7249814576fb2743674", "audit-numeric/r2"),
}
START = "<!-- body-round2-final-evidence:v1 -->"
END = "<!-- /body-round2-final-evidence:v1 -->"


def gh(*args):
    return subprocess.check_output(["gh", *args], encoding="utf-8", errors="strict")


def read_target(repository, number, kind):
    endpoint = f"repos/{repository}/issues/{number}"
    result = json.loads(gh("api", endpoint))
    result["_kind"] = kind
    result["_repository"] = repository
    if kind == "pr":
        pr = json.loads(gh("api", f"repos/{repository}/pulls/{number}"))
        result["_head"] = pr["head"]["sha"]
        result["_merged"] = pr["merged"]
    return result


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def snapshots():
    targets = [(TARGET, pr, "pr") for pr in ITEMS] + [(BOUNTY, issue, "intake") for issue, _, _ in ITEMS.values()]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda values: read_target(*values), targets))
    for row in rows:
        save_json(ROOT / CAPTURE / "before" / f"{row['_kind']}-{row['number']}.json", row)
    return rows


def final_block(pr, commit):
    issue, head, folder = ITEMS[pr]
    base = f"https://github.com/STARDUSTLC666/lingshu/tree/{commit}/validation/body-round2-20261120"
    head_note = f"本项当前源提交 `{head}`；对应 bounty 仍是原 issue #{issue}，没有另建或拆分申报。"
    if pr == 1478:
        head_note += (" 本地最初测量源为 `bae2eaea9fb77e9e451f1b220d17f9096d06ee78`，"
                      "原已验证提交为 `89c005b7fdd48f64c603d34c280a4d18a93956f7`；这些历史数据不改标成新提交。"
                      "当前 `41dc5e0` 合并维护者已采纳的旧修复，冲突解决仅更新 core 指纹；新生行衰减函数不变，"
                      "整个 core 模块与已测组合源 `5226860` 字节一致。"
                      "新 head 的独立三环境完整 gate 每腿 **5638 passed / 40 skipped / 98 subtests**、"
                      "102/102 脚本和实际脑端 23/23，标题也通过。"
                      "[新 head CI](https://github.com/FuRongJun-1999/lingshu/actions/runs/44781318899)。")
    return (f"{START}\n\n## 最终组合验证与不可变证据（2026-11-21）\n\n"
            f"{head_note}\n\n"
            f"[最终完整证据总索引]({base})；[本项工件]({base}/{folder})；"
            f"[结果与边界总表]({base}/FINAL_VALIDATION.md)。证据提交 `{commit}`。\n\n"
            "- 冻结的十二项组合源 `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`：独立重建核对十个生产文件、"
            "29 个变更函数；本轮 165 项守卫通过，27 个具名变异由指定语义断言检出。各 PR 的精确 head CI 原始记录亦保留。\n"
            "- 完整组合 Linux [run 44764384747](https://github.com/STARDUSTLC666/lingshu/actions/runs/44764384747)："
            "三个环境各 **5827 passed / 40 skipped / 98 subtests**，各 102/102 脚本及实际固定脑端 23/23。\n"
            "- 完整组合 Windows 实测 **5838 passed / 1 failed / 28 skipped / 98 subtests**，102/102 脚本通过，"
            "原驱动 `gate_ok=false` 保持不变。唯一失败是既有 symlink 能力 P1 的 POSIX 断言，精确旧基线也在本机独立复现；"
            "不将它改写成全绿。另做历史物理守卫 43 passed、原 symlink 测试体 3/3 和串行计时 4 passed，均不叠加主计数。\n"
            "- 额外 Linux [基准/变异 run 44778606930](https://github.com/STARDUSTLC666/lingshu/actions/runs/44778606930)："
            "三个环境各完成四项 A/B 基准及同 27 个具名变异；实际源哈希、原始样本、stdout/stderr、JUnit 和内层工件长度/哈希已独立核对。"
            "早期 run 44766869622 的测量和旧索引问题作为中间记录保留。\n"
            "- 成本按前文及原始 JSON 如实保留，包括增加的 Python traced peak；共享主机数据只描述本次测量，"
            "不主张统一提速、统计显著性或 RSS。仍缺 17 个原始模型/像素资产用例，未伪造资产；长期真实部署效果仍未验证。"
            "各环境和补充运行有重叠，不能把计数相加当独立覆盖。\n\n"
            f"{END}")


def updated_body(row, pr, commit):
    body = row["body"].replace("\r\n", "\n")
    assert body.count(START) == body.count(END) and body.count(START) <= 1
    if START in body:
        a, b = body.index(START), body.index(END) + len(END)
        body = body[:a] + body[b:]
    replacements = {
        "完整组合回归与远端三环境 CI 将另附精确提交证据。": "完整组合回归与远端三环境 CI 已完成，精确提交证据见文末。",
        "完整组合回归和精确 head 的三环境 CI 将补独立证据链接。": "完整组合回归和精确 head 三环境 CI 的独立证据见文末。",
        "后续补精确 head 三环境 CI 与包含上一批修复的组合回归证据。": "精确 head 三环境 CI 与包含上一批修复的组合回归证据见文末。",
        "- 未验：长期真实部署效果；完整十二项组合Windows/Linux和额外Linux三环境基准正在另行执行，当前不以未完成任务充作通过，结束后补不可变证据。":
        "- 未验：长期真实部署效果和仍缺原始资产的17个用例。完整组合Windows/Linux及额外Linux基准的实际结果、失败与跳过见文末最终证据。",
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    if pr == 1478 and row["_kind"] == "intake":
        body = body.replace("，精确提交 `89c005b7fdd48f64c603d34c280a4d18a93956f7`。",
                            "，原测量/验证提交 `89c005b7fdd48f64c603d34c280a4d18a93956f7`；当前同步提交 `41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50`。")
        body = body.replace("- 精确head的三环境完整CI（3.12常规/依赖下界、3.13）与标题均SUCCESS；每腿 **5624",
                            "- 历史89c005提交的三环境完整CI（3.12常规/依赖下界、3.13）与标题均SUCCESS；每腿 **5624")
    return body.rstrip() + "\n\n" + final_block(pr, commit) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-only", action="store_true")
    parser.add_argument("--evidence-commit")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows = snapshots()
    if args.snapshot_only:
        for row in rows:
            print(json.dumps({"kind": row["_kind"], "number": row["number"], "head": row.get("_head"),
                              "state": row["state"], "body": row["body"]}, ensure_ascii=False))
        return
    assert args.evidence_commit and re.fullmatch(r"[0-9a-f]{40}", args.evidence_commit)
    # Confirm immutable evidence is publicly retrievable before any body mutation.
    gh("api", f"repos/STARDUSTLC666/lingshu/contents/validation/body-round2-20261120/FINAL_VALIDATION.md?ref={args.evidence_commit}", "--jq", ".sha")
    by_pr = {row["number"]: row for row in rows if row["_kind"] == "pr"}
    for pr, (_, expected_head, _) in ITEMS.items():
        assert by_pr[pr]["_head"] == expected_head
        checks = json.loads(gh("pr", "view", str(pr), "--repo", TARGET, "--json", "headRefOid,statusCheckRollup,state"))
        assert checks["headRefOid"] == expected_head
        selected = [job for job in checks["statusCheckRollup"] if job["name"].startswith(("gate (", "PR 标题"))]
        assert len(selected) == 4 and all(job["status"] == "COMPLETED" and job["conclusion"] == "SUCCESS" for job in selected)
        save_json(ROOT / CAPTURE / f"pr-{pr}-checks.json", checks)
    receipts_path = ROOT / CAPTURE / "receipts.json"
    receipts = []
    for row in rows:
        pr = row["number"] if row["_kind"] == "pr" else next(pr for pr, values in ITEMS.items() if values[0] == row["number"])
        marker = re.search(r"<!-- intake:v1 (.*?) -->", row["body"])
        if row["_kind"] == "intake":
            assert marker and json.loads(marker.group(1))["pr"] == by_pr[pr]["html_url"]
        body = updated_body(row, pr, args.evidence_commit)
        body_path = ROOT / CAPTURE / f"{row['_kind']}-{row['number']}-body.md"
        body_path.write_text(body, encoding="utf-8")
        if not args.apply:
            print(json.dumps({"prepared": str(body_path), "chars": len(body)}, ensure_ascii=False))
            continue
        latest = read_target(row["_repository"], row["number"], row["_kind"])
        assert latest["body"] == row["body"] and latest["title"] == row["title"], "remote body drift; re-read before mutation"
        payload_path = body_path.with_suffix(".payload.json")
        save_json(payload_path, {"body": body})
        write_error = None
        if latest["body"].replace("\r\n", "\n") != body:
            try:
                gh("api", "--method", "PATCH", f"repos/{row['_repository']}/issues/{row['number']}", "--input", str(payload_path), "--jq", ".number")
            except subprocess.CalledProcessError as exc:
                write_error = str(exc)
        after = read_target(row["_repository"], row["number"], row["_kind"])
        save_json(ROOT / CAPTURE / "after" / f"{row['_kind']}-{row['number']}.json", after)
        verified = after["body"].replace("\r\n", "\n") == body and after["title"] == row["title"]
        if marker:
            verified = verified and marker.group(0) in after["body"]
        if row["_kind"] == "pr":
            verified = verified and after["_head"] == ITEMS[pr][1]
        receipt = {"kind": row["_kind"], "number": row["number"], "repository": row["_repository"],
                   "url": after["html_url"], "pr": pr, "source_head": ITEMS[pr][1],
                   "evidence_commit": args.evidence_commit, "state_observed": after["state"],
                   "merged_observed": after.get("_merged"), "title": after["title"],
                   "body_sha256_lf": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                   "final_marker_count": after["body"].count(START), "intake_marker": json.loads(marker.group(1)) if marker else None,
                   "labels_observed": [label["name"] for label in after["labels"]],
                   "write_error": write_error, "readback_verified": verified,
                   "observed_at": datetime.now(timezone.utc).isoformat()}
        receipts.append(receipt)
        save_json(receipts_path, {"all_eight_verified": len(receipts) == 8 and all(r["readback_verified"] for r in receipts), "targets": receipts})
        print(json.dumps(receipt, ensure_ascii=False), flush=True)
        assert verified, "uncertain body write was read back; do not blindly retry"
    if args.apply:
        assert len(receipts) == 8 and all(row["readback_verified"] for row in receipts)
        save_json(ROOT / "latest-verified.json", {"receipt_path": str(receipts_path), "evidence_commit": args.evidence_commit})


if __name__ == "__main__":
    main()
