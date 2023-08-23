.PHONY: lint
lint:
	black . --check
	isort . --check

.PHONY: format
format:
	black .
	isort .
