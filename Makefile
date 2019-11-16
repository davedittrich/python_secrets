# Makefile for python_secrets

SHELL=bash
REQUIRED_VENV:=python_secrets
VENV_DIR=$(HOME)/.virtualenvs/$(REQUIRED_VENV)
PROJECT:=$(shell basename `pwd`)

#HELP test - run 'tox' for testing
.PHONY: test
test: test-tox
	@echo '[+] All tests succeeded'

.PHONY: test-tox
test-tox:
	@if [ -f .python_secrets_environment ]; then (echo '[!] Remove .python_secrets_environment prior to testing'; exit 1); fi
	tox

.PHONY: test-bats
test-bats: bats-libraries
	@if [ "$(TRAVIS)" != "true" ]; then \
		if ! type bats 2>/dev/null >/dev/null; then \
			echo "[-] Skipping bats tests"; \
		else \
			echo "[+] Running bats unit tests:"; \
			(cd tests && ls -1 [0-9][0-9]*.bats); \
			bats --tap tests/[0-9][0-9]*.bats; \
		fi \
	 fi

.PHONY: test-bats-runtime
test-bats-runtime: bats-libraries
	@echo "[+] Running bats runtime tests:"
	@cd tests && ls -1 runtime_[0-9][0-9]*.bats
	bats --tap tests/runtime_*.bats || true

.PHONY: no-diffs
no-diffs:
	@echo 'Checking Git for uncommitted changes'
	git diff --quiet HEAD

#HELP release - package and upload a release to pypi
.PHONY: release
release: sdist bdist_egg bdist_wheel twine-check
	twine upload dist/* -r pypi

#HELP release-test - upload to "testpypi"
.PHONY: release-test
release-test: clean test docs-tests docs sdist twine-check
	$(MAKE) no-diffs
	twine upload dist/* -r testpypi

#HELP bdist_egg - build an egg package
.PHONY: bdist_egg
bdist_egg:
	rm -f dist/.LATEST_EGG
	python setup.py bdist_egg
	(cd dist && ls -t *.egg 2>/dev/null | head -n 1) > dist/.LATEST_EGG
	ls -lt dist/*.egg

#HELP bdist_wheel - build a wheel package
.PHONY: bdist_wheel
bdist_wheel:
	rm -f dist/.LATEST_WHEEL
	python setup.py bdist_wheel
	(cd dist && ls -t *.whl 2>/dev/null | head -n 1) > dist/.LATEST_WHEEL
	ls -lt dist/*.whl

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
	(cd docs && make clean && rm -f psec_help.txt)

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
.PHONY: install-active
install-active:
	python -m pip install -U .
	psec help | tee docs/psec_help.txt

#HELP docs-tests - generate bats test output for documentation
.PHONY: docs-tests
PR=pr --omit-header --omit-pagination --page-width 80
docs-tests:
	(echo '$$ make test-tox' && $(MAKE) test-tox) |\
	       $(PR) | tee docs/test-tox.txt
	$(MAKE) test-bats | $(PR) | tee docs/test-bats.txt


#HELP docs - build Sphinx docs (NOT INTEGRATED YET FROM OPENSTACK CODE BASE)
.PHONY: docs
docs:
	(cd docs && make clean html)

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
