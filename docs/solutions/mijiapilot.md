# MijiaPilot（一體式）

[`handsomejustin/mijia-control`](https://github.com/handsomejustin/mijia-control)（MijiaPilot）是最貼「用 CLI/MCP/Agent 控制米家」這個問題的單一專案：**一個專案同時給你 CLI + MCP + HomeKit + Web UI + BLE**。

## 它包含什麼

- **CLI**：`mijia-control` — 登入、[裝置清單／讀寫／動作](../control/cli.md)、場景執行、BLE。
- **MCP server**：內建，工具 `list_devices` / `set_property` / `run_action` / `run_scene`，[明確支援 Claude Code](../control/mcp.md)。
- **HomeKit 橋接**：內建 HAP-python，把設備曝露給 [Apple Home / Siri](../ecosystem/apple-home.md)。
- **Web UI**：裝置控制、場景、自動化、能耗、即時更新。
- **BLE**：本地掃描 Xiaomi BLE 感測器並觸發自動化。
- **REST API**：JWT 認證、Swagger 文件。

## 連線與認證

- 以 Python（Flask + HAP-python + bleak）在**本機**跑，但透過 `mijiaAPI` 走[雲端 QR 登入](../concepts/auth-token.md)控制裝置。
- 綁定小米帳號用 QR，API client 用 JWT token。

## 適合誰

- 想要**一套現成的東西**同時涵蓋 CLI、MCP、HomeKit，而**不想架整套 Home Assistant**。
- 想直接讓 [Claude Code](../control/mcp.md) 控制米家。

## 相對 HA 的取捨

| | MijiaPilot | [Home Assistant](home-assistant.md) |
|---|---|---|
| 安裝 | 輕量、單一專案 | 完整平台、要養機 |
| 覆蓋／生態 | 米家為主 | 最廣、跨品牌 |
| 穩健度 | 中（社群專案） | 高 |
| 上手 | 快 | 較費工 |

想要最省事又給 Claude 用，MijiaPilot 是甜蜜點；要長期、跨品牌、最穩，還是 [HA](home-assistant.md)。
