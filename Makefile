help:
	$(info The following make commands are available:)
	$(info test              - run tests and check code formatting)
	@:

test:
	PYTHONPATH=. py.test
	flake8

test_server:
	PYTHONPATH=. python ./tests/test_server.py
