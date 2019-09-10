from setuptools import setup, find_packages
from qcli import __version__

with open('README.md') as file:
    long_description = file.read()

setup(
    name='quake-cli-tools',
    version=__version__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/JoshuaSkelly/quake-cli-tools',
    author='Joshua Skelton',
    author_email='joshua.skelton@gmail.com',
    license='MIT',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'bsp2svg=qcli.bsp2svg.cli:main',
            'bsp2wad=qcli.bsp2wad.cli:main',
            'pak=qcli.pak.cli:main',
            'qmount=qcli.qmount.cli:main',
            'wad=qcli.wad.cli:main',
            'unpak=qcli.unpak.cli:main',
            'unwad=qcli.unwad.cli:main',
        ],
    },
    keywords=[''],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ]
)
