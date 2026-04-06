from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from Software.QA.scripts.criteria_mapper import build_criterion_summary, write_reports


def main() -> int:
    report = build_criterion_summary()
    json_path, _ = write_reports(report)
    written_report = json.loads(json_path.read_text(encoding="utf-8"))

    p0_failures: list[str] = []
    non_p0_failures: list[str] = []

    for row in written_report["criteria"]:
        if row["status"] != "FAIL":
            continue
        if row["severity"] == "P0":
            p0_failures.append(row["id"])
        else:
            non_p0_failures.append(row["id"])

    trend = written_report.get("trend", {})
    p0_regressed = bool(trend.get("p0_pass_rate_regressed", False))

    print(
        json.dumps(
            {
                "p0_failures": p0_failures,
                "non_p0_failures": non_p0_failures,
                "p0_pass_rate_regressed": p0_regressed,
            },
            indent=2,
        )
    )

    if p0_failures:
        print("Acceptance gate FAILED: one or more P0 automatable criteria failed.")
        return 1
    if p0_regressed:
        print("Acceptance gate FAILED: P0 pass-rate regressed versus previous baseline.")
        return 1
    if non_p0_failures:
        print("Acceptance gate WARNING: only P1/P2 automatable criteria failed.")
        return 0

    print("Acceptance gate PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
