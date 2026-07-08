# 我的裝置

用 `mi-tokens extract`（見[認證與 Token](../concepts/auth-token.md)）抽出的裝置概況。**這裡是匿名分類摘要**——完整含 token/IP/MAC/名稱那份在本機 gitignore 的 `.secrets/devices.md`，不會進 git。

!!! tip "怎麼重抓"
    `uv run --group tokens python tools/mi_tokens.py extract`（官方 QR）會把每台的 model、token、本地 IP 寫進 `.secrets/devices.md`。

## 概況

- **約 50 台**，橫跨 **tw（台灣）＋ cn（中國）兩個伺服器區**、多個 LAN 子網。
- 約一半是 **WiFi、有 token → 可本地 miIO 直控**（前提：你的機器在同一個 LAN）；另一半是 IR 虛擬遙控、Zigbee/BLE 走網關、或不在當前網段的雲端裝置。

## 分類

| 類別 | 約數 | 本地可控？ | 代表 model | 控制路徑 |
|---|---|---|---|---|
| 攝影機 | 2 | ✅ WiFi | `chuangmi.camera.*` | miIO / HA |
| 掃地機 | 3 | ✅ WiFi | `viomi/dreame/mijia.vacuum.*` | miIO / HA |
| WiFi 燈 | 3 | ✅ | `yeelink.light.ceiling22`, `leishi.light.eps127` | miIO / HA |
| 小愛音箱 | 3 | ✅ | `xiaomi.wifispeaker.l05*` | miIO / HA |
| 空調伴侶（兼 Zigbee 網關） | 3 | ✅＋當網關 | `lumi.acpartner.mcn02/v2` | miIO + XiaomiGateway3 |
| 窗簾馬達 | 5 | 部分 ✅ | `lumi.curtain.hmcn02/04` | miIO / HA |
| WiFi 牆壁開關 | ~16 | WiFi，多數沒回 IP | `zimi.switch.dhkg02/05` | 雲端／同網段時本地 |
| IR 虛擬遙控 | 6 | ❌ 無 token | `miir.*`（電視/冷氣/風扇…） | 純雲端 |
| 感測器・門磁・情境遙控 | 3 | ❌ 走網關 | `miaomiaoce.sensor_ht`, `isa.magnet`, `yeelink.remote` | 網關／雲端 |
| 其他 WiFi（插座/寵物飲水/印表/投影/路由/時鐘） | ~7 | ✅ | `chuangmi.plug`, `xiaomi.pet_waterer`, `fengmi.projector` | miIO / HA |

## 對這批裝置的結論

- **雙區＋多網段**：本地 miIO 只在同一 LAN 有效；你人在哪個網就只能本地控那個網，其餘走雲端。
- **IR `miir.*` 沒有 token 是正常的**——它們是 IR blaster 上的虛擬遙控，只能雲端觸發。
- **`lumi.acpartner.*` 兼 Zigbee 網關**——沒 IP 的感測器／門磁／部分開關掛在它底下，可用 [`XiaomiGateway3`](../solutions/home-assistant.md) 走本地。
- **這種規模最適合 [Home Assistant 中樞](../solutions/index.md)**：`al-one/hass-xiaomi-miot`（涵蓋 tw）＋ `XiaomiGateway3`，把兩區正規化，再一次接 [MCP/Claude](../control/mcp.md)、[Siri](../ecosystem/apple-home.md)、[Google](../ecosystem/google-home.md)。

## 判定小抄

- **連線**：WiFi（有 token → 可能本地）、BLE／紅外線（[雲端限定](../concepts/local-vs-cloud.md)）。
- **本地可控**：WiFi + 有 token + 你在同一 LAN；跨網段／公網 IP 的裝置本地碰不到。
- **Matter**：看型號與韌體，支援就能[免橋接](../concepts/matter.md)直進 Apple／Google。
