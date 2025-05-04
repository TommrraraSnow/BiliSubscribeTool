# Bilibili Subscription Tool

[中文](README.md) | English

This tool provides a pipeline to export your Bilibili following list from one account and automatically follow them on another account. Due to Bilibili's system limitations, following too many accounts at once may temporarily lock the follow function.

Notice: This tool is open-source in MIT, but it requires a thired-party lib [bilibili-api](https://github.com/Nemo2011/bilibili-api), which is not in MIT. For comercial use, pleace request their permission.

## Features

- Export your Bilibili following list to JSON
- Automatically follow users from the JSON list
- Dual credential support for different operations

## Installation

```bash
uv sync
```

## Configuration

1. Rename `RENAME_THIS_TO_config.toml` to `config.toml`
2. Fill in your Bilibili credentials (see [credential guide](https://github.com/Nemo2011/bilibili-api/blob/master/docs/get_credential.md))

## Usage

1. Export followings:

```bash
uv run download_follow.py
```

2. Auto follow:

```bash
uv run auto_follow.py
```

## License

MIT

Note: While this tool is open source under MIT license, the third-party library [bilibili-api](https://github.com/Nemo2011/bilibili-api) used in this project is not MIT licensed. Please apply separately for commercial use.
