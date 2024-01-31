SHELL = bash

isort = isort inmanta_plugins tests
black = black inmanta_plugins tests
flake8 = flake8 inmanta_plugins tests
pyupgrade = pyupgrade --py39-plus $$(find inmanta_plugins tests -type f -name '*.py')

test_env_vars:
	@ python -c 'import yaml, pathlib; print(" ".join(f"{k}='{v}'" for k, v in yaml.safe_load(pathlib.Path(".ci-integration-tests.yml").read_text())["env_vars"].items()))'

.PHONY: install
install:
	pip install -U setuptools pip wheel
	pip install -U --upgrade-strategy=eager -c requirements.txt -r requirements.dev.txt -e .

.PHONY: format
format:
	$(isort)
	$(black)
	$(flake8)
	$(pyupgrade)

.PHONY: pep8
pep8:
	$(flake8)

RUN_MYPY_PLUGINS=python -m mypy --html-report mypy/out/inmanta_plugins -p inmanta_plugins.podman

.PHONY: mypy
mypy-plugins:
	@ echo "Running mypy on the module plugins\n..."
	@ $(RUN_MYPY_PLUGINS)

mypy-tests:
	@ echo "Running mypy on the module tests\n..."
	@ $(RUN_MYPY_TESTS)
