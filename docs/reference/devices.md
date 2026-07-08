# 我的裝置

逐台記錄你手上的米家設備與它的控制路徑。**先放模板**——把你的型號填進來（或把清單給我，我幫你補 Matter／本地／HomeKit 判定）。

!!! tip "怎麼拿到 model id 與 token"
    用 `miiocli cloud` 或抽取工具列出裝置，會有 `model`（如 `yeelink.light.xxxx`）與 token。見[認證與 Token](../concepts/auth-token.md)。

| 裝置 | 型號（model id） | 連線 | 本地可控？ | token 取得 | Matter？ | 現用控制路徑 |
|---|---|---|---|---|---|---|
| _（範例）客廳燈_ | `yeelink.light.xxxx` | WiFi | ？ | ✅ | ❌ | HA / homebridge-miot |
| _（範例）溫濕度計_ | `miaomiaoce.sensor_ht.xxx` | BLE | ❌（雲端／網關） | — | ❌ | HA + 網關 |
| | | | | | | |
| | | | | | | |
| | | | | | | |

## 判定小抄

- **連線**：WiFi（可能本地）、BLE／紅外線（[雲端限定](../concepts/local-vs-cloud.md)）。
- **本地可控**：WiFi + 支援 miIO 且 token 有效才算；新韌體可能鎖。
- **Matter**：看型號與韌體，支援就能[免橋接](../concepts/matter.md)直進 Apple／Google。
