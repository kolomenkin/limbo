# =================================
CODE_DIR_ROOT=./

FLAKE8_CONFIG=./.flake8
PYLINT_CONFIG=./.pylintrc
MYPY_CONFIG=./mypy.ini

# =================================

help:
	$(info The following make commands are available:)
	$(info test              - run unit tests)
	@:

test:
	python -m pytest -v

test_server:
	PYTHONPATH=. python ./tests/test_server.py ${SERVER}

speedtest:
	PYTHONPATH=. python ./utils/speedtest.py ${SERVER}

# =================================

check-all-docker: check-md check-yaml check-make check-pep8

check-all-local: check-pep8-local check-mypy check-lint-local

# =================================

check-md:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --tty --network=none --volume="${CURDIR}:/markdown:ro" \
		--workdir=//markdown/ \
		06kellyjac/markdownlint-cli:0.21.0-alpine \
		-- ./

check-yaml:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --tty --network=none --volume="$(CURDIR):/data:ro" \
		--workdir=//data/ \
		cytopia/yamllint:1.20 \
		-- ./

check-pep8:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --tty --network=none --volume="${CURDIR}:/apps:ro" \
		--workdir=//apps/ \
		alpine/flake8:3.7.9 \
		 --config=${FLAKE8_CONFIG} -- ${CODE_DIR_ROOT}

check-pep8-local:
	flake8 --config=${FLAKE8_CONFIG} -- ./

check-lint:
# cytopia/pylint:latest
# DIGEST: sha256:9437cb377e90b73121a94eb3743b9d0769a2021c7a7e5a6e423957a17f831216
# OS/ARCH: linux/amd64
# pushed on 2020-02-15
# Using two slashes at the beginning of the paths for Windows bash shell
# =================================================================================================
# WARNING! DON'T USE THIS TARGET! PYLINT CAN'T WORK CORRECTLY WITHOUT ALL DEPENDENCIES INSTALLED!
# =================================================================================================
	docker run --rm --tty --network=none --volume="${CURDIR}:/data:ro" \
		--workdir=//data/ \
		cytopia/pylint@sha256:9437cb377e90b73121a94eb3743b9d0769a2021c7a7e5a6e423957a17f831216 \
		--rcfile=${PYLINT_CONFIG} -- ${CODE_DIR_ROOT}*.py ${CODE_DIR_ROOT}utils/*.py ${CODE_DIR_ROOT}tests/*.py

check-lint-local:
	pylint \
		--rcfile=${PYLINT_CONFIG} -- ${CODE_DIR_ROOT}*.py ${CODE_DIR_ROOT}utils/*.py ${CODE_DIR_ROOT}tests/*.py

check-mypy:
	mypy --config-file=${MYPY_CONFIG} --strict -- ${CODE_DIR_ROOT}

check-make:
# cytopia/checkmake:latest
# DIGEST: sha256:512ddae39012238b41598ebc1681063112aba1bd6a2eb8be3e74704e01d91581
# OS/ARCH: linux/amd64
# pushed on 2020-02-16
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --tty --network=none --volume="${CURDIR}:/data:ro" \
		--workdir=//data/ \
		cytopia/checkmake@sha256:512ddae39012238b41598ebc1681063112aba1bd6a2eb8be3e74704e01d91581 \
		--config=./checkmake.ini Makefile
