# Apple Home / Siri

**壞消息先講**：米家設備**原生基本不進 HomeKit**（少數例外是官方網關在 Mi Home App 裡吐出 HomeKit 配對碼）。所以標準做法是**橋接**——把米家設備透過一層轉譯曝露成 HomeKit 配件，Siri 就能控。

## Siri 橋接方式

| 方式 | 需 token？ | 依賴 | 原生程度 |
|---|---|---|---|
| [`merdok/homebridge-miot`](https://github.com/merdok/homebridge-miot) | ✅ | Homebridge（Node.js） | 橋接 |
| HAP-python 自建 | 依實作 | [MijiaPilot 內建](../solutions/mijiapilot.md) | 橋接 |
| [HA HomeKit Bridge](../solutions/home-assistant.md) | 否（HA 已接管） | Home Assistant | 橋接（一鍵曝露全部） |
| [Matter](../concepts/matter.md) | 否 | 支援 Matter 的裝置／網關 | **原生**（免橋接） |

## 幾條路怎麼選

- 只想把**幾台**設備丟進 Apple Home → [Homebridge + `homebridge-miot`](open-source-homekit.md)（需 token）。
- 已經有 [Home Assistant](../solutions/home-assistant.md) → 直接開它的 **HomeKit Bridge**，把全部設備一鍵曝露，最省事。
- 用 [MijiaPilot](../solutions/mijiapilot.md) → 它內建 HAP-python 橋接。
- 買的是**新款、標示 Matter** 的設備 → 走 [Matter](../concepts/matter.md) 原生配對，不需要以上任何橋接。

!!! note "原生 HomeKit 的少數例外"
    部分米家網關會在 Mi Home App 裡提供 HomeKit 配對碼（官方支援文件 KA-07355）。這條路可不可行高度依型號與地區，別當通例。
