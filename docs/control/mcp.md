# MCP 與 Agent Skills

讓 LLM／Agent（例如 Claude Code）直接控制米家。過去一年米家的 MCP 生態爆發，有**兩條路**：直接的米家 MCP server，或透過 [Home Assistant](../solutions/home-assistant.md) 的內建 MCP。

## MCP server 對照

| 專案 | 登入 | 連線 | 代表工具 | 涵蓋 | Claude Code |
|---|---|---|---|---|---|
| [`javen-yan/miot-mcp`](https://github.com/javen-yan/miot-mcp) | QR | 雲端 | `control_by_intent`、`set_brightness`、`set_color_temperature`、`execute_scene` | 廣 | ✅ |
| [MijiaPilot 內建](../solutions/mijiapilot.md) | QR | 雲端 | `list_devices`、`set_property`、`run_action`、`run_scene` | 廣 | ✅（明確支援） |
| [`oujiafan/mcp-mijia`](https://github.com/oujiafan/mcp-mijia) | QR | 雲端 | 裝置控制、Xiaozhi／AI 助理整合 | 中 | ✅ |
| [`gehaiyi/xiaomi-home-mcp`](https://github.com/gehaiyi/xiaomi-home-mcp) | QR | 雲端 | 輕量裝置控制 | 中 | ✅ |
| [HA 內建 MCP Server](https://www.home-assistant.io/integrations/mcp/) | 經 HA | 依 HA | 曝露 HA 內所有實體與服務 | 最廣（不限品牌） | ✅ |

> 直接的米家 MCP 多走[雲端 QR 登入](../concepts/auth-token.md)、把 session 存在本機（如 `~/.miot-mcp/`）。想要品牌無關、一次控制所有設備，走 HA 內建 MCP。

!!! danger "miot-mcp / mijiaAPI 會走第三方 proxy"
    `miot-mcp` 內建的 `mijiaAPI` 把你的 `serviceToken`/`ssecurity` 和每條裝置指令送到 **`api.mijia.tech`（非小米官方、作者自架）**，等於受信任的 MITM，且拿不到 local token。在意隱私就別用它當控制層——改用 HA 內建 MCP（走官方），或見[登入疑難排解](../concepts/login-troubleshooting.md)。

## 在 Claude Code 接上 MCP

大致流程（以 `miot-mcp` 為例）：

1. 安裝並啟動 server（Python 3.10+，`poetry install`）。
2. 首次啟動掃 QR 登入，session 存本機。
3. 在 Claude Code 的 MCP 設定指向這個 server。
4. 之後就能用自然語言：「把客廳燈調暖白」。

## Agent Skills

MCP 和 Agent Skill 定位不同，別搞混：

| 面向 | MCP | Agent Skill |
|---|---|---|
| 用途 | **即時控制**設備 | **打包一段工作流** |
| 機制 | server 提供 tools，Claude 直接呼叫 | `SKILL.md` + 腳本，shell out 到 `miiocli` 或 curl HA REST |
| 何時用 | 要 Claude 動態操作裝置 | 要一鍵「睡眠模式」這種固定流程 |

- **即時控制裝置** → 用 MCP（正解）。
- **固定工作流**（例如「離家模式：關燈、關插座、掃地機回充」）→ 寫成 Skill，內部去打 [CLI](cli.md) 或 HA 的 REST API。

兩者可並用：Skill 負責「劇本」，MCP／CLI 負責「執行」。
