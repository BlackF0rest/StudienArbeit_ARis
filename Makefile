PYTHON ?= python

qa-smoke:
	$(PYTHON) -m Software.QA.tests.integration.test_smoke_scenarios

qa-acceptance:
	$(PYTHON) -m Software.QA.scripts.run_acceptance_gate

qa-report:
	$(PYTHON) -m Software.QA.scripts.criteria_mapper
