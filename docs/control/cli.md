# CLI 控制

用命令列直接控制米家設備，由底層到高層有三個層次。看到「token」代表[本地](../concepts/local-vs-cloud.md)、「QR」代表雲端。

## CLI 工具對照

| 工具 | 連線／協定 | 認證 | 能力 | 語言 |
|---|---|---|---|---|
| [`python-miio`](https://github.com/rytilahti/python-miio)（`miiocli`） | 本地 miIO/LAN | 裝置 token（`miiocli cloud` 可拉） | 讀寫屬性、raw 指令、逐裝置操作 | Python |
| `mijiaAPI` | 雲端 MIoT | QR 登入 | 雲端裝置／場景控制 SDK（多數 MCP 基於它） | Python |
| [`mijia-control`](https://github.com/handsomejustin/mijia-control)（MijiaPilot CLI） | 雲端（經 mijiaAPI） | QR 登入 | `device list/show/get/set/action`、`scene run`、`home`、BLE、Web UI | Python |

## `python-miio`（本地、經典）

```bash
pip install python-miio
miiocli cloud                                   # 取得裝置 IP + token（見 認證與 Token）
miiocli device --ip <IP> --token <TOKEN> info   # 直控某台裝置
```

- **優點**：本地、低延遲、無雲端依賴。
- **缺點**：新設備本地協議可能被鎖；小米雲端登入偶爾改版導致抓 token 卡關（見 [認證與 Token](../concepts/auth-token.md) 的 fallback）。

## MijiaPilot 的 CLI

[MijiaPilot（`mijia-control`）](../solutions/mijiapilot.md) 是一個「CLI + MCP + HomeKit」三合一專案，其 CLI 走雲端：

```bash
mijia-control login                 # QR 登入
mijia-control device list
mijia-control device set  <did> <prop> <value>
mijia-control scene  run  <scene>
```

適合想要一套指令同時涵蓋控制、場景、BLE 感測器的人。細節見[方案比較 → MijiaPilot](../solutions/mijiapilot.md)。

## 想更進一步

- 要讓 CLI 動作變成「一句話觸發」的工作流，包成 [Agent Skill](mcp.md#agent-skills)。
- 要 Claude 即時控制，改用 [MCP](mcp.md)。
