build:
	python setup.py sdist

build-clean:
	rm -rf ./dist ./build ./edmtool.egg-info

install-dev:
	pip install .[dev]

install-local:
	pip install -e . --force-reinstall

format:
	yapf -i -r ./edmtool

test:
	python -m unittest discover -s edmtool/tests -p 'test_*.py'

venv:
	virtualenv .venv --system-site-packages
