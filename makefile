.PHONY: install uninstall reinstall test clean bsp2svg bsp2wad image2spr pak qmount spr2image unpak unwad wad

install:
	pip install .

uninstall:
	pip uninstall quake-cli-tools -y

reinstall: uninstall install

publish:
	python setup.py sdist
	twine upload dist/*

publish-test:
	python setup.py sdist
	python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

package:
	python package.py

build: bsp2svg bsp2wad image2spr pak qmount spr2image unpak unwad wad

bsp2svg:
	pyinstaller --name=bsp2svg ./qcli/bsp2svg/cli.py

bsp2wad:
	pyinstaller --name=bsp2wad ./qcli/bsp2wad/cli.py

image2spr:
	pyinstaller --name=image2spr ./qcli/image2spr/cli.py --exclude=numpy

pak:
	pyinstaller --name=pak ./qcli/pak/cli.py

qmount:
	pyinstaller --name=qmount ./qcli/qmount/cli.py

spr2image:
	pyinstaller --name=spr2image ./qcli/spr2image/cli.py --exclude=numpy

unpak:
	pyinstaller --name=unpak ./qcli/unpak/cli.py

unwad:
	pyinstaller --name=unwad ./qcli/unwad/cli.py

wad:
	pyinstaller --name=wad ./qcli/wad/cli.py

test:
	python -m unittest discover -s tests

clean:
	find . -name "*.pyc" -delete
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -rf *.spec
	rm -rf *.zip
