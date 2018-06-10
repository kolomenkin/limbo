help:
	$(info The following make commands are available:)
	$(info test              - run tests and check code formatting)
	@:

test: $(install_local_output)
	PYTHONPATH=. py.test
	flake8
