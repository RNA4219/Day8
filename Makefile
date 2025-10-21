.PHONY: fmt lint type test check

fmt:
@echo "No formatting step configured."

lint:
ruff check .

type:
mypy --strict workflow-cookbook

test:
pytest -q workflow-cookbook/tests

check: lint type test
