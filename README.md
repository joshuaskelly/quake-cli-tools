[![quake-cli-tools](https://raw.githubusercontent.com/joshuaskelly/quake-cli-tools/master/.media/logo.svg?sanitize=true)](https://github.com/JoshuaSkelly/quake-cli-tools)

# quake-cli-tools

[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)]() [![PyPI version](https://badge.fury.io/py/quake-cli-tools.svg)](https://pypi.python.org/pypi/quake-cli-tools) [![Discord](https://img.shields.io/badge/discord-chat-7289DA.svg)](https://discord.gg/KvwmdXA)

`quake-cli-tools` is a suite of command-line tools designed for creating Quake content.

## Tools

- **File Packaging and Extraction**:
  - **pak**: Package files into a PAK file.
  - **wad**: Add files to a WAD file.
  - **unpak**: Extract files from a PAK file.
  - **unwad**: Extract files from a WAD file.
- **File Conversion**:
  - **bsp2svg**: Convert a BSP file into an SVG format.
  - **bsp2wad**: Generate a WAD file from a BSP file.
  - **image2spr**: Convert image files into an SPR format.
  - **spr2image**: Extract frames from an SPR file.
- **File System Utilities**:
  - **qmount**: Mount a PAK file as a virtual drive.

## Installation

```sh
make install
```

## Usage

To execute the tools locally, use the following command pattern in your command prompt:

```sh
python3 ./qcli/<tool-name>/cli.py ...
```

> **Note**: Add the `-h` (or `--help`) parameter to any command to obtain detailed information about its options.

## Building

Follow these steps to build binaries for all tools, which will be placed in the `dist` directory:

1. Install project and development dependencies:
   ```sh
   make prepare
   ```
1. Build all binaries:
   ```sh
   make build
   ```
1. Package the binaries:
   ```sh
   make package
   ```

## Contributing

Interested in contributing to `quake-cli-tools`? Whether it's bug fixes or new features, your contributions are welcome! Please start by creating an issue to discuss what you're working on.

1. Fork this repository.
1. Create your feature branch:
   ```sh
   git checkout -b feature/add-cool-new-tool
   ```
1. Modify the codebase, then format it:
   ```sh
   make format
   ```
1. Stage the modified files:
   ```sh
   git add .
   ```
1. Commit your changes:
   ```sh
   git commit -m 'feat: add a must-have new tool'
   ```
1. Push to the branch:
   ```sh
   git push origin feature/add-cool-new-tool
   ```
1. Submit a Pull Request.
1. Create an [issue](https://github.com/joshuaskelly/quake-cli-tools/issues/new).

## License

`quake-cli-tools` is [MIT licensed](LICENSE).
