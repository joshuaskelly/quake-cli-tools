.PHONY: install uninstall reinstall test clean bsp2svg bsp2wad image2spr pak qmount spr2image unpak unwad wad

prepare:
	pip3 install -r requirements-dev.txt
	pip3 install -r requirements.txt

format:
	python3 -m black ./

install:
	pip3 install .

uninstall:
	pip3 uninstall quake-cli-tools -y

reinstall: uninstall install

publish:
	python3 setup.py sdist
	twine upload dist/*

publish-test:
	python3 setup.py sdist
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

package:
	python3 package.py

build: bsp2svg bsp2wad image2spr pak qmount spr2image unpak unwad wad

bsp2svg:
	pyinstaller --name=bsp2svg --onefile ./qcli/bsp2svg/cli.py

bsp2wad:
	pyinstaller --name=bsp2wad --onefile ./qcli/bsp2wad/cli.py

image2spr:
	pyinstaller --name=image2spr --onefile ./qcli/image2spr/cli.py --exclude=numpy

pak:
	pyinstaller --name=pak --onefile ./qcli/pak/cli.py

qmount:
	pyinstaller --name=qmount --onefile ./qcli/qmount/cli.py

spr2image:
	pyinstaller --name=spr2image --onefile ./qcli/spr2image/cli.py --exclude=numpy

unpak:
	pyinstaller --name=unpak --onefile ./qcli/unpak/cli.py

unwad:
	pyinstaller --name=unwad --onefile ./qcli/unwad/cli.py --exclude=numpy

wad:
	pyinstaller --name=wad --onefile ./qcli/wad/cli.py --exclude=numpy

clean:
	find . -name "*.pyc" -delete
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -rf *.spec
	rm -rf *.zip
