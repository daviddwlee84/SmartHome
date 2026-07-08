# 開源 HomeKit

想把米家（或任何非 HomeKit 設備）帶進 Apple Home，有三個開源層級可選。

## 對照

| 專案 | 語言 | 層級 | 適用 |
|---|---|---|---|
| [Homebridge](https://homebridge.io/) | Node.js | 外掛平台 | 外掛生態最大；「只想把幾台設備丟進 Apple Home」 |
| [HAP-python](https://github.com/ikalchev/HAP-python) / HAP-NodeJS | Python / Node | 底層 HAP 協議 | 要自己寫橋接時用 |
| [HA HomeKit Bridge](../solutions/home-assistant.md) | （HA 內建） | 一鍵曝露 | 已有 Home Assistant，把全部設備一鍵送進 Apple Home |

## 建議

- **沒有中樞、少量設備** → Homebridge + [`homebridge-miot`](apple-home.md)。
- **要自幹橋接／嵌進自己的程式** → HAP-python（[MijiaPilot](../solutions/mijiapilot.md) 就是用它）。
- **已有 Home Assistant** → 直接用它的 HomeKit Bridge，不必另外裝 Homebridge。

延伸：若設備支援 [Matter](../concepts/matter.md)，這些橋接都可以省掉。
