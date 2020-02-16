help:
	$(info The following make commands are available:)
	$(info test              - run tests and check code formatting)
	@:

test:
	PYTHONPATH=. py.test
	flake8

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
		//data

