# Makefile for python_secrets

REQUIRED_VENV:=dimsenv
VENV_DIR=$(HOME)/dims/envs/$(REQUIRED_VENV)
ENVNAME:=$(shell basename $(VIRTUAL_ENV))
PROJECT:=$(shell basename `pwd`)

#HELP test - run 'python setup.py test'
.PHONY: test
test:
	python setup.py test

#HELP release - package and upload a release"
.PHONY: release
#release: sdist bdist_wheel docs
release: clean sdist bdist_egg bdist_wheel
	scp -P8422 dist/python_dimscli*.{whl,egg} dist/python-dimscli*.tar.gz source.devops.dims:/data/src/

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

#HELP clean - remove build artifacts
.PHONY: clean
clean:
	rm -rf dist build *.egg-info
	find . -name '*.pyc' -exec rm {} ';'
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

#HELP docs - build Sphinx docs (NOT INTEGRATED YET FROM OPENSTACK CODE BASE)
.PHONY: docs
docs:
	(cd docs && make clean html)
