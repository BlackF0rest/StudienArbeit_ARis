from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Any

from Software.QA.tests.api.test_api_endpoints import run_api_tests
from Software.QA.tests.integration.test_smoke_scenarios import run_smoke_scenarios

BASE_DIR = Path(__file__).resolve().parents[1]
CRITERIA_FILE = BASE_DIR / "acceptance_criteria.yaml"
REPORT_DIR = BASE_DIR / "reports"
HISTORY_DIR = REPORT_DIR / "history"


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line == "criteria:":
            continue

        if line.startswith("- "):
            if current:
                criteria.append(current)
            current = {}
            line = line[2:].strip()
            if line:
                key, value = line.split(":", 1)
                current[key.strip()] = _coerce_scalar(value.strip())
            continue

        if current is None:
            continue

        key, value = line.split(":", 1)
        current[key.strip()] = _coerce_scalar(value.strip())

    if current:
        criteria.append(current)

    return {"criteria": criteria}


def _coerce_scalar(raw: str) -> Any:
    cleaned = raw.strip()
    if cleaned.lower() == "true":
        return True
    if cleaned.lower() == "false":
        return False
    if cleaned.startswith('"') and cleaned.endswith('"'):
        return cleaned[1:-1]
    return cleaned


def _calculate_p0_pass_rate(criteria_rows: list[dict[str, Any]]) -> float | None:
    p0_automated = [row for row in criteria_rows if row["severity"] == "P0" and row["status"] in {"PASS", "FAIL"}]
    if not p0_automated:
        return None
    p0_passed = sum(1 for row in p0_automated if row["status"] == "PASS")
    return p0_passed / len(p0_automated)


def _load_manual_tracking(criteria_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    tracked: list[dict[str, str]] = []
    default_owner = os.environ.get("QA_MANUAL_DEFAULT_OWNER", "UNASSIGNED")
    default_date = os.environ.get("QA_MANUAL_DEFAULT_DATE", "UNSET")
    allowed_dispositions = {"PASS", "FAIL", "WAIVED", "BLOCKED"}

    for row in criteria_rows:
        if not row["id"].startswith("MAN-"):
            continue

        key = row["id"].replace("-", "_")
        disposition = os.environ.get(f"QA_{key}_DISPOSITION", "UNSET").upper()
        owner = os.environ.get(f"QA_{key}_OWNER", default_owner)
        date = os.environ.get(f"QA_{key}_DATE", default_date)
        notes = os.environ.get(f"QA_{key}_NOTES", "")

        tracked.append(
            {
                "id": row["id"],
                "severity": row["severity"],
                "disposition": disposition,
                "disposition_clear": "yes" if disposition in allowed_dispositions else "no",
                "owner": owner,
                "date": date,
                "notes": notes,
            }
        )

    return tracked


def _status_diffs(current_rows: list[dict[str, Any]], previous_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    previous_status = {row["id"]: row["status"] for row in previous_rows}
    diffs: list[dict[str, str]] = []
    for row in current_rows:
        old = previous_status.get(row["id"])
        if old is None or old == row["status"]:
            continue
        diffs.append({"id": row["id"], "previous": old, "current": row["status"]})
    return diffs


def attach_trend_metadata(report: dict[str, Any], previous_report: dict[str, Any] | None) -> dict[str, Any]:
    current_rate = _calculate_p0_pass_rate(report["criteria"])
    trend: dict[str, Any] = {
        "previous_report": None,
        "p0_pass_rate": current_rate,
        "previous_p0_pass_rate": None,
        "p0_pass_rate_regressed": False,
        "status_changes": [],
    }

    if previous_report is None:
        report["trend"] = trend
        return report

    previous_rate = _calculate_p0_pass_rate(previous_report.get("criteria", []))
    trend["previous_report"] = previous_report.get("generated_at")
    trend["previous_p0_pass_rate"] = previous_rate
    trend["status_changes"] = _status_diffs(report["criteria"], previous_report.get("criteria", []))

    if current_rate is not None and previous_rate is not None and current_rate < previous_rate:
        trend["p0_pass_rate_regressed"] = True

    report["trend"] = trend
    return report


def _evaluate_readiness(report: dict[str, Any], json_path: Path, md_path: Path) -> dict[str, Any]:
    criteria_rows = report["criteria"]
    p0_automatable_failures = [
        row["id"] for row in criteria_rows if row["severity"] == "P0" and row["status"] == "FAIL"
    ]
    p0_regressed = bool(report.get("trend", {}).get("p0_pass_rate_regressed", False))

    manual_rows = report.get("manual_tracking", [])
    manual_p1_unclear = [
        row["id"] for row in manual_rows if row["severity"] == "P1" and row["disposition_clear"] != "yes"
    ]

    evidence = {
        "json_report": {
            "path": str(json_path),
            "exists": True,
            "ci_artifact_link": os.environ.get("QA_LATEST_JSON_ARTIFACT_URL", ""),
        },
        "markdown_report": {
            "path": str(md_path),
            "exists": True,
            "ci_artifact_link": os.environ.get("QA_LATEST_MD_ARTIFACT_URL", ""),
        },
    }

    evidence_complete = all(
        item["exists"] or bool(item["ci_artifact_link"])
        for item in [evidence["json_report"], evidence["markdown_report"]]
    )
    policy_requirements_met = not p0_automatable_failures and not p0_regressed and not manual_p1_unclear

    return {
        "evidence": evidence,
        "evidence_complete": evidence_complete,
        "p0_automatable_failures": p0_automatable_failures,
        "p0_pass_rate_regressed": p0_regressed,
        "manual_p1_without_clear_disposition": manual_p1_unclear,
        "companion_sprint_start_allowed": evidence_complete and policy_requirements_met,
        "policy": (
            "Companion sprint starts only when all P0 automatable checks pass "
            "and manual P1 checks have clear disposition."
        ),
    }


def build_criterion_summary() -> dict[str, Any]:
    data = parse_simple_yaml(CRITERIA_FILE)
    test_run_errors: list[str] = []
    api_results: dict[str, Any] = {}
    smoke_results: dict[str, Any] = {}

    try:
        api_results = {result.name: result for result in run_api_tests()}
    except Exception as exc:  # pragma: no cover - defensive guard for offline/dev envs
        test_run_errors.append(f"API test run failed: {exc}")

    try:
        smoke_results = {result.name: result for result in run_smoke_scenarios()}
    except Exception as exc:  # pragma: no cover - defensive guard for offline/dev envs
        test_run_errors.append(f"Integration smoke test run failed: {exc}")

    criterion_map = {
        "API-001": ["status_endpoint", "messages_get_post_delete", "teleprompter_send_current_history", "teleprompter_reset"],
        "API-002": ["debug_diagnostics_endpoint"],
        "INT-001": ["teleprompter_send_current_history", "scenario_a_send_then_current"],
        "INT-002": ["scenario_a_send_then_current", "scenario_b_reset_defaults"],
        "REG-001": ["messages_get_post_delete", "scenario_c_messages_roundtrip"],
        "SMK-001": [
            "scenario_a_send_then_current",
            "scenario_b_reset_defaults",
            "scenario_c_messages_roundtrip",
            "scenario_d_hid_gesture_normalization",
        ],
    }

    all_results = {**api_results, **smoke_results}
    summary: list[dict[str, Any]] = []

    for criterion in data["criteria"]:
        criterion_id = criterion["id"]
        if not criterion.get("automatable", False):
            summary.append(
                {
                    "id": criterion_id,
                    "severity": criterion["severity"],
                    "status": "SKIPPED",
                    "reason": "Manual verification required",
                    "tests": [],
                }
            )
            continue

        mapped_tests = criterion_map.get(criterion_id, [])
        if not mapped_tests:
            summary.append(
                {
                    "id": criterion_id,
                    "severity": criterion["severity"],
                    "status": "SKIPPED",
                    "reason": "No automated test mapping configured",
                    "tests": [],
                }
            )
            continue

        failed = [name for name in mapped_tests if not all_results.get(name) or not all_results[name].passed]
        if failed:
            reasons = [all_results[name].reason if name in all_results else "missing result" for name in failed]
            reason_text = "; ".join(f"{test}: {reason}" for test, reason in zip(failed, reasons))
            if test_run_errors:
                reason_text = f"{reason_text}; test-run-errors: {' | '.join(test_run_errors)}"
            summary.append(
                {
                    "id": criterion_id,
                    "severity": criterion["severity"],
                    "status": "FAIL",
                    "reason": reason_text,
                    "tests": mapped_tests,
                }
            )
        else:
            summary.append(
                {
                    "id": criterion_id,
                    "severity": criterion["severity"],
                    "status": "PASS",
                    "reason": "All mapped tests passed",
                    "tests": mapped_tests,
                }
            )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "criteria": summary,
        "manual_tracking": _load_manual_tracking(summary),
        "test_results": {
            "api": [result.__dict__ for result in api_results.values()],
            "integration": [result.__dict__ for result in smoke_results.values()],
        },
        "test_run_errors": test_run_errors,
    }
    return report


def write_reports(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    json_path = REPORT_DIR / "latest.json"
    md_path = REPORT_DIR / "latest.md"

    previous_report: dict[str, Any] | None = None
    if json_path.exists():
        previous_report = json.loads(json_path.read_text(encoding="utf-8"))

    report = attach_trend_metadata(report, previous_report)
    report["readiness"] = _evaluate_readiness(report, json_path, md_path)

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Acceptance Criteria Report",
        "",
        f"Generated at: {report['generated_at']}",
        "",
        "## Criteria Summary",
        "",
        "| Criterion | Severity | Status | Reason |",
        "|---|---|---|---|",
    ]
    for row in report["criteria"]:
        lines.append(f"| {row['id']} | {row['severity']} | {row['status']} | {row['reason']} |")

    lines.extend(["", "## Manual verification required", ""])
    manual_rows = [row for row in report["criteria"] if row["status"] == "SKIPPED"]
    if manual_rows:
        for row in manual_rows:
            lines.append(f"- {row['id']}: {row['reason']}")
    else:
        lines.append("- None")

    lines.extend(["", "## Manual criteria checklist (owner/date required)", ""])
    lines.append("| Criterion | Severity | Disposition | Clear? | Owner | Date | Notes |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in report["manual_tracking"]:
        lines.append(
            f"| {row['id']} | {row['severity']} | {row['disposition']} | {row['disposition_clear']} | "
            f"{row['owner']} | {row['date']} | {row['notes']} |"
        )

    lines.extend(["", "## Trend", ""])
    trend = report["trend"]
    if trend["previous_report"] is None:
        lines.append("- Baseline run: no previous report available.")
    else:
        lines.append(f"- Previous report timestamp: {trend['previous_report']}")
        lines.append(f"- Current P0 pass-rate: {trend['p0_pass_rate']:.2%}")
        lines.append(f"- Previous P0 pass-rate: {trend['previous_p0_pass_rate']:.2%}")
        lines.append(f"- P0 pass-rate regressed: {'yes' if trend['p0_pass_rate_regressed'] else 'no'}")
        if trend["status_changes"]:
            lines.append("- Status changes:")
            for diff in trend["status_changes"]:
                lines.append(f"  - {diff['id']}: {diff['previous']} -> {diff['current']}")
        else:
            lines.append("- Status changes: none")

    lines.extend(["", "## Ready for companion decision gate", ""])
    readiness = report["readiness"]
    json_evidence = readiness["evidence"]["json_report"]
    md_evidence = readiness["evidence"]["markdown_report"]
    lines.append(
        f"- Required evidence (JSON): `{json_evidence['path']}`"
        f" (exists={json_evidence['exists']}, ci_artifact_link={json_evidence['ci_artifact_link'] or 'n/a'})"
    )
    lines.append(
        f"- Required evidence (Markdown): `{md_evidence['path']}`"
        f" (exists={md_evidence['exists']}, ci_artifact_link={md_evidence['ci_artifact_link'] or 'n/a'})"
    )
    lines.append(f"- Evidence complete: {'yes' if readiness['evidence_complete'] else 'no'}")
    lines.append(f"- P0 automatable failures: {', '.join(readiness['p0_automatable_failures']) or 'none'}")
    lines.append(f"- P0 pass-rate regressed: {'yes' if readiness['p0_pass_rate_regressed'] else 'no'}")
    lines.append(
        "- Manual P1 checks lacking clear disposition: "
        f"{', '.join(readiness['manual_p1_without_clear_disposition']) or 'none'}"
    )
    lines.append(f"- Hard policy: {readiness['policy']}")
    lines.append(
        "- Companion sprint start allowed: "
        f"{'yes' if readiness['companion_sprint_start_allowed'] else 'no'}"
    )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archived_json = HISTORY_DIR / f"{timestamp}.json"
    archived_md = HISTORY_DIR / f"{timestamp}.md"
    shutil.copy2(json_path, archived_json)
    shutil.copy2(md_path, archived_md)

    keep_count = int(os.environ.get("QA_REPORT_HISTORY_LIMIT", "10"))
    history_json_files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    for stale_json in history_json_files[keep_count:]:
        stale_md = stale_json.with_suffix(".md")
        stale_json.unlink(missing_ok=True)
        stale_md.unlink(missing_ok=True)

    return json_path, md_path


def main() -> int:
    report = build_criterion_summary()
    json_path, md_path = write_reports(report)
    print(f"Wrote reports: {json_path} and {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
