# Smart Home

用 **CLI / MCP / Agent Skills** 控制米家（Xiaomi Mijia），並與 Apple Home（Siri）、Google Home、開源 HomeKit 聯動的整合筆記。

## 📖 完整筆記

內容已整理成文件站：**<https://daviddwlee84.github.io/SmartHome/>**

- [方案比較（HA vs MijiaPilot vs 點對點）](https://daviddwlee84.github.io/SmartHome/solutions/)
- [本地 vs 雲端控制](https://daviddwlee84.github.io/SmartHome/concepts/local-vs-cloud/)
- [用 CLI / MCP / Agent Skills 控制](https://daviddwlee84.github.io/SmartHome/control/cli/)
- [連結彙整](https://daviddwlee84.github.io/SmartHome/reference/links/)

## 本地開發

```bash
uv sync --extra docs
uv run mkdocs serve   # http://127.0.0.1:8000
```

文件原始碼在 `docs/`，站台設定在 `mkdocs.yml`。
