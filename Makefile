# =================================
CODE_DIR_ROOT=./

FLAKE8_CONFIG=./.flake8
PYLINT_CONFIG=./.pylintrc
MYPY_CONFIG=./mypy.ini

# =================================

help:
	$(info The following make commands are available:)
	$(info test              - run tests and check code formatting)
	@:

.PHONY: test

test:
	python -m pytest -v
	flake8 --config=${FLAKE8_CONFIG}

test_server:
	PYTHONPATH=. python ./tests/test_server.py ${SERVER}

speedtest:
	PYTHONPATH=. python ./utils/speedtest.py ${SERVER}

check-md:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --network none -v "${CURDIR}:/markdown:ro" \
		06kellyjac/markdownlint-cli:0.21.0-alpine \
			//markdown/

check-yaml:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --network none -v "$(CURDIR):/data:ro" \
		cytopia/yamllint:1.20 \
		//data/

check-pep8:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --network none -v "${CURDIR}:/apps:ro" \
		-w //apps/ \
		alpine/flake8:3.7.9 \
		 --config=${FLAKE8_CONFIG} -- ${CODE_DIR_ROOT}

check-pep8-local:
	flake8 --config=${FLAKE8_CONFIG}

check-lint:
# cytopia/pylint:latest
# DIGEST: sha256:9437cb377e90b73121a94eb3743b9d0769a2021c7a7e5a6e423957a17f831216
# OS/ARCH: linux/amd64
# pushed on 2020-02-15
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --network none -v "${CURDIR}:/data:ro" \
		-w //data/ \
		cytopia/pylint@sha256:9437cb377e90b73121a94eb3743b9d0769a2021c7a7e5a6e423957a17f831216 \
		--rcfile=${PYLINT_CONFIG} -- ${CODE_DIR_ROOT}*.py

check-lint-local:
	pylint --rcfile=./.pylintrc -- ./*.py

check-mypy:
	mypy --config-file ${MYPY_CONFIG} --strict -- ${CODE_DIR_ROOT}
