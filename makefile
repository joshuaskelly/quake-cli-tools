.PHONY: install uninstall reinstall test clean

install:
	pip install .

uninstall:
	pip uninstall quake-cli-tools -y

reinstall: uninstall install

publish:
	python setup.py sdist
	twine upload dist/*

test:
	python -m unittest discover -s tests

clean:
	find . -name "*.pyc" -delete
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
