# =================================
CODE_DIR_ROOT = ./

FLAKE8_CONFIG       = ./.config/.flake8
PYLINT_CONFIG       = ./.config/.pylintrc
MYPY_CONFIG         = ./.config/mypy.ini

MARKDOWNLINT_CONFIG = ./.config/.markdownlint.yaml
YAMLLINT_CONFIG     = ./.config/.yamllint.yaml
CHECKMAKE_CONFIG    = ./.config/checkmake.ini

PYTEST_CONFIG       = ./pytest.ini

# =================================

help:
	$(info The following make commands are available:)
	$(info test              - run unit tests)
	@:

test:
	pytest --verbose --strict-config -c=${PYTEST_CONFIG}

test_server:
	PYTHONPATH=. python ./tests/test_server.py ${SERVER}

speedtest:
	PYTHONPATH=. python ./utils/speedtest.py ${SERVER}

# =================================

check-all-docker: check-md check-yaml check-make check-pep8

check-all-local: check-pep8-local check-mypy check-lint

# =================================

check-md:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --tty --network=none --volume="${CURDIR}:/markdown:ro" \
		--workdir=//markdown/ \
		06kellyjac/markdownlint-cli:0.21.0-alpine \
            --config=${MARKDOWNLINT_CONFIG} \
			-- ./

check-yaml:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --tty --network=none --volume="$(CURDIR):/data:ro" \
		--workdir=//data/ \
		cytopia/yamllint:1.20 \
            -c=${YAMLLINT_CONFIG} \
			--strict \
			-- ./

check-pep8:
# Using two slashes at the beginning of the paths for Windows bash shell
	docker run --rm --tty --network=none --volume="${CURDIR}:/apps:ro" \
		--workdir=//apps/ \
		alpine/flake8:3.7.9 \
			--config=${FLAKE8_CONFIG} \
			-- ${CODE_DIR_ROOT}

check-pep8-local:
	flake8 --config=${FLAKE8_CONFIG} -- ./

check-lint:
	pylint \
		--rcfile=${PYLINT_CONFIG} \
		-- ${CODE_DIR_ROOT}*.py ${CODE_DIR_ROOT}utils/*.py ${CODE_DIR_ROOT}tests/*.py

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
			--config=${CHECKMAKE_CONFIG} \
			Makefile
