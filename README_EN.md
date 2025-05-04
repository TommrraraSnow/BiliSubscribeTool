# Bilibili Subscription Tool

[中文](README.md) | English

## Features

- Export your Bilibili following list to JSON
- Automatically follow users from a JSON list
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
