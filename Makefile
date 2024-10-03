# Makefile for python_secrets

SHELL=bash
VERSION=$(shell cat VERSION)
PROJECT:=$(shell basename `pwd`)

.PHONY: default
default: all

.PHONY: all
all: install

.PHONY: help
help:
	@echo 'usage: make [VARIABLE=value] [target [target..]]'
	@echo ''
	@echo 'build - build project packages'
	@echo 'twine-check - run "twine check"'
	@echo 'clean - remove build artifacts'
	@echo 'spotless - deep clean'
	@echo 'test - generic target for both "test-tox" and "test-bats"'
	@echo 'test-tox - run tox tests'
	@echo 'test-bats - run Bats unit tests'
	@echo 'test-bats-runtime - run Bats runtime integration/system tests'
	@echo 'release - produce a pypi production release'
	@echo 'release-test - produce a pypi test release'
	@echo 'release-prep - final documentation preparations for release'
	@echo 'install - build project with Poetry and install with Pip'
	@echo 'update-packages - update dependencies with Poetry'
	@echo 'docs-tests - generate bats test output for documentation'
	@echo 'docs-help - generate "psec help" output for documentation'
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
	tox run -m static
	tox run -m tests
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
release: clean docs build twine-check
	(cd dist && twine upload $$(cat .LATEST_*) -r pypi)

#HELP release-prep - final documentation preparations for release
.PHONY: release-prep
release-prep: install clean build docs-help docs-tests
	@echo 'Check in help text docs and HISTORY.rst?'

#HELP release-test - upload to "testpypi"
.PHONY: release-test
release-test: clean test docs-tests docs twine-check
	$(MAKE) no-diffs
	(cd dist && twine upload $$(cat .LATEST_*) -r testpypi)

#HELP build - build project packages
.PHONY: build
build:
	@rm -f dist/.LATEST_TARGZ dist/.LATEST_WHEEL
	poetry dynamic-versioning -vv
	poetry build
	@(cd dist && ls -t *.tar.gz 2>/dev/null | head -n 1 > .LATEST_TARGZ)
	@(cd dist && ls -t *.whl 2>/dev/null | head -n 1 > .LATEST_WHEEL)

#HELP twine-check
.PHONY: twine-check
twine-check: build
	(cd dist && twine check $$(cat .LATEST_*))

#HELP clean - remove build artifacts
.PHONY: clean
clean: clean-docs
	rm -rf dist build *.egg-info
	find . -name '*.pyc' -delete

.PHONY: clean-docs
clean-docs:
	cd docs && make clean

.PHONY: spotless
spotless: clean
	rm -rf htmlcov
	rm -f psec/_version.py
	rm -rf .tox/
	python -m pip uninstall -y $(PROJECT)

#HELP install - build project with Poetry and install with Pip'
.PHONY: i
.PHONY: install
i install: spotless build
	(cd dist && python -m pip install $$(cat .LATEST_WHEEL))

#HELP update-packages - update dependencies with Poetry
.PHONY: update-packages
update-packages:
	poetry update

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

docs/psec_help.txt: install
	PYTHONPATH=$(shell pwd) python -m psec help | tee docs/psec_help.txt

#HELP examples - produce some example output for docs
.PHONY: examples
examples:
	@PYTHONPATH=$(shell pwd) python -m psec --help

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
