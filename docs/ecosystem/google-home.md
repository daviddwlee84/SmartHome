# Google Home

這條是三大聯動裡**最簡單**的：米家**原生支援** Google。

## 兩種接法

| 方式 | 原生？ | 需求 | 區域坑 |
|---|---|---|---|
| 官方帳號綁定（Works with Google） | ✅ | 米家帳號 + Google Home App | 米家區與 Google 帳號區不一致會失敗 |
| [HA Google Assistant](../solutions/home-assistant.md) | 否（經 HA） | Home Assistant（＋設定） | 由 HA 統一處理 |

## 官方綁定步驟

1. 開 Google Home App（或米家 App）→「Works with Google」／連結帳號。
2. 登入你的小米帳號授權。
3. 裝置同步進 Google，就能用 Google Assistant 控制。

官方說明見 Xiaomi 支援文件 KA-12902。

!!! warning "最常見的坑：分區"
    綁定失敗、或綁了但裝置不出現，幾乎都是[帳號分區](../concepts/account-region.md)不一致。確認小米帳號的伺服器區與 Google 帳號地區相符。

## 什麼時候改走 HA

如果你已經用 [Home Assistant](../solutions/home-assistant.md) 當[中樞](../solutions/index.md)，可以用 HA 的 Google Assistant 整合自己接，好處是連非米家設備也一起進 Google、規則自訂更彈性。
