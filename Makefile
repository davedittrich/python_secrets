# Makefile for python_secrets

SHELL=bash
VERSION=$(shell cat VERSION)
REQUIRED_VENV:=python_secrets
VENV_DIR=$(HOME)/.virtualenvs/$(REQUIRED_VENV)
PROJECT:=$(shell basename `pwd`)

.PHONY: default
default: all

.PHONY: all
all: install-active

.PHONY: help
help:
	@echo 'usage: make [VARIABLE=value] [target [target..]]'
	@echo ''
	@echo 'test - generic target for both "test-tox" and "test-bats"'
	@echo 'test-tox - run tox tests'
	@echo 'test-bats - run Bats unit tests'
	@echo 'test-bats-runtime - run Bats runtime integration/system tests'
	@echo 'release - produce a pypi production release'
	@echo 'release-test - produce a pypi test release'
	@echo 'release-prep - final documentation preparations for release'
	@echo 'sdist - run "python3 setup.py sdist"'
	@echo 'bdist_wheel - build a universal binary wheel'
	@echo 'twine-check - run "twine check"'
	@echo 'clean - remove build artifacts'
	@echo 'spotless - deep clean'
	@echo 'build-packet-cafe - Build and bring up packet_cafe containers'
	@echo 'up-packet-cafe - Bring up packet_cafe containers'
	@echo 'down-packet-cafe - Bring up packet_cafe containers'
	@echo 'clean-packet-cafe - remove packet_cafe contents'
	@echo 'spotless-packet-cafe - Remove all packet_cafe files and containers'
	@echo 'install - install pip package'
	@echo 'install-active - run "python3 -m pip install -U ."'
	@echo 'docs-tests - generate bats test output for documentation'
	@echo 'docs-help - generate "lim help" output for documentation'
	@echo 'docs - build Sphinx docs'


#HELP test - run 'tox' for testing
.PHONY: test
test: test-tox
	@echo '[+] test: All tests passed'

# [Makefile-test-tox]
# The following target rules are optimized by splitting up `tox` tests so they
# fail early on syntax and security checks before running more lengthy unit
# tests against Python versions (with coverage reporting).  This is designed to
# more easily focus on code quality first and foremost.
.PHONY: test-tox
test-tox:
	@if [ -f .python_secrets_environment ]; then (echo '[!] Remove .python_secrets_environment prior to testing'; exit 1); fi
	touch docs/psec_help.txt
	@# See also comment in tox.ini file.
	tox -e pep8
	tox -e bandit,docs,bats
	tox -e clean,py39,py310,py311,pypi,report
	echo '[+] test-tox: All tests passed'
# ![Makefile-test-tox]

.PHONY: test-bats
test-bats: bats-libraries
	@if [ "$(TRAVIS)" != "true" ]; then \
		if ! type bats 2>/dev/null >/dev/null; then \
			echo "[-] Skipping bats tests"; \
		else \
			source test-environment.bash; \
			echo "[+] Running bats tests: $(shell cd tests && echo [0-9][0-9]*.bats)"; \
			PYTHONWARNINGS="ignore" bats --tap tests/[0-9][0-9]*.bats && \
			echo '[+] test-bats: All tests passed'; \
		fi \
	 fi

.PHONY: test-bats-runtime
test-bats-runtime: bats-libraries
	@echo "[+] Running bats runtime tests: $(shell cd tests && echo runtime_[0-9][0-9]*.bats)"; \
	(source test-environment.bash; \
	 PYTHONWARNINGS="ignore" bats --tap tests/runtime_[0-9][0-9]*.bats && \
	 echo '[+] test-bats-runtime: All tests passed')

.PHONY: no-diffs
no-diffs:
	@echo 'Checking Git for uncommitted changes'
	git diff --quiet HEAD

#HELP release - package and upload a release to pypi
.PHONY: release
release: clean docs sdist bdist_wheel twine-check
	twine upload $(shell cat dist/.LATEST_*) -r pypi

#HELP release-prep - final documentation preparations for release
.PHONY: release-prep
release-prep: install-active clean sdist docs-help docs-tests
	@echo 'Check in help text docs and HISTORY.rst?'

#HELP release-test - upload to "testpypi"
.PHONY: release-test
release-test: clean test docs-tests docs twine-check
	$(MAKE) no-diffs
	twine upload $(shell cat dist/.LATEST_*) -r testpypi

#HELP sdist - build a source package
.PHONY: sdist
sdist: clean-docs docs
	rm -f dist/.LATEST_SDIST
	python3 setup.py sdist
	ls -t dist/*.tar.gz 2>/dev/null | head -n 1 > dist/.LATEST_SDIST
	ls -l dist/*.tar.gz

#HELP bdist_egg - build an egg package
.PHONY: bdist_egg
bdist_egg:
	rm -f dist/.LATEST_EGG
	python3 setup.py bdist_egg
	ls -t dist/*.egg 2>/dev/null | head -n 1 > dist/.LATEST_EGG
	ls -lt dist/*.egg

#HELP bdist_wheel - build a wheel package
.PHONY: bdist_wheel
bdist_wheel:
	rm -f dist/.LATEST_WHEEL
	python3 setup.py bdist_wheel
	ls -t dist/*.whl 2>/dev/null | head -n 1 > dist/.LATEST_WHEEL
	ls -lt dist/*.whl

#HELP twine-check
.PHONY: twine-check
twine-check: sdist bdist_egg bdist_wheel
	twine check $(shell cat dist/.LATEST_*)

#HELP clean - remove build artifacts
.PHONY: clean
clean: clean-docs
	python3 setup.py clean
	rm -rf dist build *.egg-info
	find . -name '*.pyc' -delete

.PHONY: clean-docs
clean-docs:
	cd docs && make clean

.PHONY: spotless
spotless: clean
	rm -rf htmlcov

#HELP install - install in required Python virtual environment (default $(REQUIRED_VENV))
.PHONY: install
install:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Required virtual environment '$(REQUIRED_VENV)' not found."; \
		exit 1; \
	fi
	@if [ ! -e "$(VENV_DIR)/bin/python3" ]; then \
		echo "Cannot find $(VENV_DIR)/bin/python3"; \
		exit 1; \
	else \
		echo "Installing into $(REQUIRED_VENV) virtual environment"; \
		$(VENV_DIR)/bin/python3 -m pip uninstall -y $(PROJECT); \
		$(VENV_DIR)/bin/python3 setup.py install; \
	fi

#HELP install-active - install in the active Python virtual environment
.PHONY: i
.PHONY: install-active
i install-active: bdist_wheel
	python3 -m pip uninstall -y $(PROJECT)
	@# python3 -m pip install -U "$(shell cat dist/.LATEST_WHEEL)" | grep -v ' already '
	python3 setup.py install

#HELP docs-tests - generate bats test output for documentation
.PHONY: docs-tests
PR=pr --omit-header --omit-pagination --page-width 80
docs-tests:
	$(MAKE) -B docs/test-tox.txt
	$(MAKE) -B docs/test-bats.txt
	$(MAKE) -B docs/test-bats-runtime.txt

docs/test-tox.txt:
	(echo '$$ make test-tox' && $(MAKE) test-tox) |\
	       $(PR) | tee docs/test-tox.txt

docs/test-bats.txt:
	$(MAKE) test-bats | $(PR) | tee docs/test-bats.txt

docs/test-bats-runtime.txt:
	(echo '$$ make test-bats-runtime' && $(MAKE) test-bats-runtime) |\
	       $(PR) | tee docs/test-bats-runtime.txt

#HELP docs - build Sphinx docs (NOT INTEGRATED YET FROM OPENSTACK CODE BASE)
.PHONY: docs
docs: docs/psec_help.txt
	cd docs && make html

docs/psec_help.txt: install-active
	PYTHONPATH=$(shell pwd) python3 -m psec help | tee docs/psec_help.txt

#HELP examples - produce some example output for docs
.PHONY: examples
examples:
	@PYTHONPATH=$(shell pwd) python3 -m psec --help

# Git submodules and subtrees are both a huge PITA. This is way simpler.

.PHONY: bats-libraries
bats-libraries: bats bats-support bats-assert

bats:
	@[ -d tests/libs/bats ] || \
		(mkdir -p tests/libs/bats; git clone http://github.com/sstephenson/bats tests/libs/bats)


bats-support:
	@[ -d tests/libs/bats-support ] || \
		(mkdir -p tests/libs/bats-support; git clone https://github.com/ztombol/bats-support tests/libs/bats-support)

bats-assert:
	@[ -d tests/libs/bats-assert ] || \
		(mkdir -p tests/libs/bats-assert; git clone https://github.com/ztombol/bats-assert tests/libs/bats-assert)

#EOF
