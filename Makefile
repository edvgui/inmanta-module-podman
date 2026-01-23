SHELL = bash

isort = isort inmanta_plugins tests
black_preview = black --preview inmanta_plugins tests
black = black inmanta_plugins tests
flake8 = flake8 inmanta_plugins tests
pyupgrade = pyupgrade --py39-plus $$(find inmanta_plugins tests -type f -name '*.py')

.PHONY: install
install:
	uv pip install -U -r requirements.dev.txt -c requirements.txt -e .

.PHONY: format
format:
	$(isort)
	$(black_preview)
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
