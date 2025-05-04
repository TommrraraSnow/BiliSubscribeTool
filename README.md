# Bilibili 关注工具

中文 | [English](README_EN.md)

## 功能

- 导出Bilibili关注列表到JSON文件
- 从JSON列表自动关注用户
- 支持不同操作的独立凭证配置

## 安装

```bash
uv sync
```

## 配置

1. 将 `RENAME_THIS_TO_config.toml`重命名为 `config.toml`
2. 填写你的Bilibili凭证(参考[凭证指南](https://github.com/Nemo2011/bilibili-api/blob/master/docs/get_credential.md))

## 使用

1. 导出关注列表:

```bash
uv run download_follow.py
```

2. 自动关注:

```bash
uv run auto_follow.py
```

## 许可证

MIT
