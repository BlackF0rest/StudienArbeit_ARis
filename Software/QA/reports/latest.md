# Acceptance Criteria Report

Generated at: 2026-04-12T14:31:32.302642+00:00

## Criteria Summary

| Criterion | Severity | Status | Reason |
|---|---|---|---|
| API-001 | P0 | FAIL | status_endpoint: missing result; messages_get_post_delete: missing result; teleprompter_send_current_history: missing result; teleprompter_reset: missing result; test-run-errors: API test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' | Integration smoke test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' |
| API-002 | P0 | SKIPPED | No automated test mapping configured |
| INT-001 | P0 | FAIL | teleprompter_send_current_history: missing result; scenario_a_send_then_current: missing result; test-run-errors: API test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' | Integration smoke test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' |
| INT-002 | P1 | FAIL | scenario_a_send_then_current: missing result; scenario_b_reset_defaults: missing result; test-run-errors: API test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' | Integration smoke test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' |
| REG-001 | P1 | FAIL | messages_get_post_delete: missing result; scenario_c_messages_roundtrip: missing result; test-run-errors: API test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' | Integration smoke test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' |
| SMK-001 | P0 | FAIL | scenario_a_send_then_current: missing result; scenario_b_reset_defaults: missing result; scenario_c_messages_roundtrip: missing result; test-run-errors: API test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' | Integration smoke test run failed: Backend exited early: Traceback (most recent call last):
  File "/workspace/StudienArbeit_ARis/Software/Backend/run.py", line 3, in <module>
    from app import create_app
  File "/workspace/StudienArbeit_ARis/Software/Backend/app.py", line 5, in <module>
    from flask import Flask, g, jsonify, request
ModuleNotFoundError: No module named 'flask' |
| MAN-001 | P1 | SKIPPED | Manual verification required |
| MAN-002 | P1 | SKIPPED | Manual verification required |
| MAN-003 | P1 | SKIPPED | Manual verification required |
| MAN-004 | P2 | SKIPPED | Manual verification required |

## Manual verification required

- API-002: No automated test mapping configured
- MAN-001: Manual verification required
- MAN-002: Manual verification required
- MAN-003: Manual verification required
- MAN-004: Manual verification required

## Manual criteria checklist (owner/date required)

| Criterion | Severity | Disposition | Clear? | Owner | Date | Notes |
|---|---|---|---|---|---|---|
| MAN-001 | P1 | UNSET | no | UNASSIGNED | UNSET |  |
| MAN-002 | P1 | UNSET | no | UNASSIGNED | UNSET |  |
| MAN-003 | P1 | UNSET | no | UNASSIGNED | UNSET |  |
| MAN-004 | P2 | UNSET | no | UNASSIGNED | UNSET |  |

## Trend

- Previous report timestamp: 2026-04-12T10:03:16.848289+00:00
- Current P0 pass-rate: 0.00%
- Previous P0 pass-rate: 0.00%
- P0 pass-rate regressed: no
- Status changes: none

## Ready for companion decision gate

- Required evidence (JSON): `/workspace/StudienArbeit_ARis/Software/QA/reports/latest.json` (exists=True, ci_artifact_link=n/a)
- Required evidence (Markdown): `/workspace/StudienArbeit_ARis/Software/QA/reports/latest.md` (exists=True, ci_artifact_link=n/a)
- Evidence complete: yes
- P0 automatable failures: API-001, INT-001, SMK-001
- P0 pass-rate regressed: no
- Manual P1 checks lacking clear disposition: MAN-001, MAN-002, MAN-003
- Hard policy: Companion sprint starts only when all P0 automatable checks pass and manual P1 checks have clear disposition.
- Companion sprint start allowed: no
