# Makefile for python_secrets

REQUIRED_VENV:=python_secrets
VENV_DIR=$(HOME)/.virtualenvs/$(REQUIRED_VENV)
PROJECT:=$(shell basename `pwd`)

#HELP test - run 'tox' for testing
.PHONY: test
test: test-tox test-bats

.PHONY: test-tox
test-tox:
	tox

.PHONY: test-bats
test-bats:
	[ "$(TRAVIS)" != "true" ] && bats tests || true

#HELP release - package and upload a release to pypi
.PHONY: release
release: clean sdist bdist_egg bdist_wheel test twine-check
	twine upload dist/* -r pypi

#HELP release-test - upload to "testpypi"
.PHONY: release-test
release-test: clean bdist_wheel test
	twine upload dist/* -r testpypi

#HELP bdist_egg - build an egg package
.PHONY: bdist_egg
bdist_egg:
	python setup.py bdist_egg
	ls -l dist/*.egg

#HELP bdist_wheel - build a wheel package
.PHONY: bdist_wheel
bdist_wheel:
	python setup.py bdist_wheel
	ls -l dist/*.whl

#HELP sdist - build a source package
.PHONY: sdist
sdist: docs
	python setup.py sdist
	ls -l dist/*.tar.gz

#HELP twine-check
.PHONY: twine-check
twine-check: bdist_egg
	twine check $(shell ls dist/*.egg | head -n 1)

#HELP clean - remove build artifacts
.PHONY: clean
clean:
	rm -rf dist build *.egg-info
	find . -name '*.pyc' -delete
	(cd docs && make clean)

#HELP install - install in required Python virtual environment (default $(REQUIRED_VENV))
.PHONY: install
install:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Required virtual environment '$(REQUIRED_VENV)' not found."; \
		exit 1; \
	fi
	@if [ ! -e "$(VENV_DIR)/bin/python" ]; then \
		echo "Cannot find $(VENV_DIR)/bin/python"; \
		exit 1; \
	else \
		echo "Installing into $(REQUIRED_VENV) virtual environment"; \
		$(VENV_DIR)/bin/pip uninstall -y $(PROJECT); \
		$(VENV_DIR)/bin/python setup.py install; \
	fi

#HELP install-active - install in the active Python virtual environment
.PHONY: install
install-active:
	python setup.py install && python -m pip install -U .

#HELP docs - build Sphinx docs (NOT INTEGRATED YET FROM OPENSTACK CODE BASE)
.PHONY: docs
docs:
	(cd docs && make clean html)
