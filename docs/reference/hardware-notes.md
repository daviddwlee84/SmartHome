# 硬體慣例與選型

「哪個型號能做什麼」的慣例與冷知識——踩過的坑整理成選型表，買/接東西前先查這頁。

## IR 發射器：誰能本地噴、誰只能雲端

!!! warning "投影機／電視／音箱多半是 IR 接收端，不是萬能發射器"
    要「用一台設備發 IR 去控別的家電」，得是 **IR blaster**。投影機、電視本身只收自己遙控的 IR，不能拿來當萬能遙控。小愛音箱雖有些型號帶 IR，但**只能雲端驅動**。

| 型號 | 能發 IR？ | **本地**可控 (miIO)？ | 備註 |
|---|---|---|---|
| `chuangmi.ir.v2` / `chuangmi.remote.v2`（小米萬能遙控器） | ✅ 任意碼 | ✅ `learn`/`play`/`play_pronto` | **本地 IR 首選、便宜** |
| `lumi.acpartner.v1/v2/v3`（舊版空調伴侶） | ✅（`FE` 格式，偏冷氣） | ✅ `learn`/`send_ir_code` | 兼 Zigbee 網關（見下） |
| `lumi.acpartner.mcn02`（新版空調伴侶 2） | 只冷氣 | ❌ 無本地 learn | 本地 IR 學不了 |
| `xiaomi.wifispeaker.*`（小愛音箱，含帶 IR 的 lx5a/L05G/你的 l05c） | ✅（有 IR 硬體者） | ❌ **只能雲端** | `WifiSpeaker` 無本地 IR API；IR 只走 Mi Home／語音 |

→ 要**本地**控電視：買一顆 `chuangmi.ir.v2`。要**現在就控**（免硬體）：`mi-tokens ir-send` 走雲端。都見 [本地 IR 控制](../control/ir.md)。

## Zigbee 網關：哪些設備兼網關

| 型號 | 是 Zigbee 網關？ | 本地路徑 |
|---|---|---|
| `lumi.acpartner.v3`（舊版空調伴侶） | ✅ | HA 內建 `xiaomi_aqara`（需 LAN developer key） |
| `lumi.acpartner.v1/v2` | ✅（硬體） | `xiaomi_aqara` 官方列 v2 不支援；可用 python-miio 設 developer key 試 |
| 多模網關 `ZNDMWG03LM` / `DMWG03LM` / `ZNDMWG04LM` … | ✅ Zigbee+BLE+Mesh | [`AlexxIT/XiaomiGateway3`](https://github.com/AlexxIT/XiaomiGateway3)（本地） |
| `lumi.acpartner.mcn02` | ✅（走 miot-spec） | 走 `al-one/hass-xiaomi-miot`（雲／本地） |

!!! note "常見誤解"
    **`XiaomiGateway3` 只支援多模網關，不支援空調伴侶**。空調伴侶（`lumi.acpartner.*`）的 Zigbee 子裝置要走 `xiaomi_aqara`。

## 其他慣例（踩過的坑）

- **小米路由器 LAN 一律 `192.168.31.x`** → 多個家會撞號；跨家要先把其中一家改子網。見 [HA 中樞](../solutions/home-assistant.md)。
- **雲端回的 `localip` 常過期**（實測投影機報 `26.26.26.1`、實際在 `.189`）；本地控制要用 MAC 從 ARP 查即時 IP（`mi-tokens verify` 已自動做）。
- **`miir.*` 是雲端虛擬遙控**（無 token）；帳號的 IR `controller_id`（如你 TV 的 `10982`）**不是**公開 IRDB 的 `matchid`，不能直接查碼。見 [本地 IR 控制](../control/ir.md)。
- **python-miio 的 locale 沒有 `tw`**；台灣帳號用 `al-one/hass-xiaomi-miot`（含 tw）或 `mi-tokens`（掃 tw/sg）。見 [登入疑難排解](../concepts/login-troubleshooting.md)。
