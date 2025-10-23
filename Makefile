.PHONY: fmt lint type test check help

fmt:
	ruff format .

lint:
	ruff check .

type:
	mypy --strict workflow-cookbook

test:
	pytest -q tests workflow-cookbook/tests

check: lint type test

help:
	@printf 'fmt   Format code with ruff format.\n'
	@printf 'lint  Run Ruff lint checks.\n'
	@printf 'type  Run mypy strict type checks.\n'
	@printf 'test  Run pytest suites.\n'
	@printf 'check Run lint, type, and test targets.\n'
