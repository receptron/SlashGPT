.PHONY: test
test:
	python -m pytest

.PHONY: lint
lint:
	black . --check
	# Using `--profile black` to resolve conflict with black
	isort . --check --profile black
	yamllint .
	# Ignoring
	# - E501: max line length
	# - E203 and W203: They go against PEP8: https://black.readthedocs.io/en/stable/faq.html#why-are-flake8-s-e203-and-w503-violated
	flake8 . --ignore=E501,E203,W503
	# Using the following options:
	# --explicit-package-bases: to make mypy work without __init__.py: https://mypy.readthedocs.io/en/stable/running_mypy.html#mapping-file-paths-to-modules
	# --ignore-missing-imports; to make mypi work without __init__.py: https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-ignore-missing-imports
	# --install-types --non-interactive: to install missing stub packages for 3rd party libraries for better type checking: https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-install-types
	mypy . --explicit-package-bases --ignore-missing-imports --install-types --non-interactive


.PHONY: format
format:
	black .
	# Using `--profile black` to resolve conflict with black
	isort . --profile black

.PHONY: before_commit
before_commit:
	make test
	make format
	make lint

## docker: run docker development environment with full requirements
.PHONY: docker
docker:
	docker build --build-arg BUILD=full -t slashgpt .
	docker run -it -v "$(PWD):/SlashGPT/SlashGPT" slashgpt python -m pdb SlashGPT.py

## dev: run debugging environment in poetry
.PHONY: dev
dev:
	poetry run python -m pdb SlashGPT.py
