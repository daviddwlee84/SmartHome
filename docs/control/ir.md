# 本地 IR 控制（含把 `miir.*` 雲端碼抽回本地）

米家 App 有個「學習遙控器 → 記下某顆按鍵 → 之後重播」的功能。這件事**可以完全本地做**（`python-miio` 直打 miIO，不經雲端）——前提是 IR blaster 的**型號對**、且碼的**格式對得上**。這頁回答你的核心問題：**能不能把雲端 `miir.*` 裡錄好的碼抽出來、自己重播？**

!!! info "先講結論"
    - **能抽**：你帳號裡的 `miir.*` 遙控可透過官方雲 API 讀出（`{region}.api.io.mi.com/app/v2/irdevice/...`）。
    - **DIY 學習的鍵**：raw code 存在你帳號上 → 可直接重播。**品牌配對的遙控**：只存參照，真碼在小米碼庫、是 **AES-ECB+gzip 加密 → 微秒時序 → Pronto**，且只有 `chuangmi.ir.v2` 能播。
    - **格式綁 blaster**：chuangmi base64 ≠ acpartner `FE` ≠ pronto，不能互換。你的 `lumi.acpartner.v2` 只能重播「在 acpartner 上學的」碼；**抽出來的 TV/chuangmi 碼它送不了**。
    - 你手上**沒有 `chuangmi.ir.v2`**，若要乾淨地本地重播電視，多半得加一顆。

## 哪些設備能本地噴 IR

| 型號 | `python-miio` 類別 | 本地 learn/play？ | 備註 |
|---|---|---|---|
| `chuangmi.ir.v2` / `chuangmi.remote.v2`（萬能遙控器） | `ChuangmiIr` | ✅ `learn`/`read`/`play`/`play_pronto` 完整 | **任意碼最乾淨**；你目前沒有 |
| `lumi.acpartner.v2`（你有 ×2：书房空调、風） | `AirConditioningCompanion` | ✅ `learn`/`send_ir_code`（**FE 格式**） | 冷氣最佳；可學 TV/風扇，但碼是 acpartner 專屬 |
| `lumi.acpartner.mcn02`（你有：主卧空调） | `AirConditioningCompanionMcn02` | ❌ 只有 on/off/status/send_command | 本地**學不了** IR |
| `xiaomi.wifispeaker.l05b` / `l05c`（你有） | `WifiSpeaker` | ❌ 無任何本地 IR 方法 | **實測：你的 `l05c` 就是這 6 個 `miir.*` 的 parent blaster（有 IR 硬體）**，但 `WifiSpeaker` 無本地 IR API → **只能雲端** |

!!! warning "「叫小愛用 IR 開電視」是雲端技能，不是本地"
    就算是帶 IR 的小愛（`lx5a`/`L05G`），`python-miio` 的 `WifiSpeaker` 類別**沒有任何 IR 方法**——它的 IR 完全靠小米雲/語音場景驅動。**沒有任何一款小愛音箱能當本地 IR 發射器。**要本地就用 `chuangmi.ir.v2` 或你的 `acpartner.v2`。

## Path 1：把雲端 `miir.*` 的碼抽出來（回答你的問題）

`miir.tv.ir01`、`miir.aircondition.ir02`、`miir.fan.ir01`… 沒 token、沒 `localip`，因為它們不是實體裝置，而是米家在真實 blaster 上疊的「家電定義」。但**錄好的碼可以透過官方雲 API 抽出來**，用你 `mi-tokens` 已經有的 `serviceToken`/`ssecurity` 簽名呼叫（跟 extractor 同一套 RC4 簽名）。

### 端點（POST，官方 `api.io.mi.com`，非第三方）

| 端點 | 參數 | 用途 |
|---|---|---|
| `/v2/irdevice/controllers` | `{parent_id}` | 列出某個實體 blaster 底下的虛擬遙控 |
| `/v2/irdevice/controller/keys` | `{did}` | 列出某遙控的**按鍵**（DIY 的話含 `code`） |
| `/v2/irdevice/controller/info` | `{did}` | 遙控資訊，含品牌配對的 `controller_id`（matchid） |
| `/v2/ircode/controller/keys` | `{controller_id}` | 品牌配對遙控的鍵＋碼（來自碼庫） |
| `/v2/irdevice/controller/key/click` | `{did, key_id}` | **雲端**觸發一顆鍵（繼續依賴雲，但今天就能動） |

決定「能不能本地重播」的關鍵是每個 `miir.*` 的 **`parent_id`**（哪顆實體 blaster 生的），它決定碼的格式：

| 情況 | 碼格式 | 本地重播 |
|---|---|---|
| DIY 學習、parent = chuangmi blaster/小愛 | chuangmi base64（`Z6WP…`，magic `0xA567`） | ✅ `chuangmi.ir.v2` `play('raw:…')`（**你沒有這顆**） |
| DIY 學習、parent = acpartner | `FE…` frame | ✅ 同一顆 `acpartner.v2` 用 `send_ir_code` 重播 |
| **品牌配對**（選了電視品牌） | 碼庫加密：base64 → AES-ECB(`fd7e915003168929c1a9b0ec32a60788`) → gzip → 微秒時序 → 轉 **Pronto** | ✅ 只有 `chuangmi.ir.v2` `play('pronto:…')` |

### 抽取流程

1. 用 tw（與 cn）的 session，`POST .../v2/irdevice/controller/keys {did: <miir 的 did>}`，看原始 JSON 有沒有 `code` 欄位。
2. **有 `code`（DIY）**：直接重播——chuangmi base64 → `miiocli chuangmi_ir … play 'raw:<code>'`；`FE…` → 送回**原本那顆 acpartner**。
3. **沒 `code`（品牌配對）**：`.../controller/info {did}` 拿 `controller_id` → `.../ircode/controller/keys {controller_id}`（或公開碼庫 `sg-urc.io.mi.com/controller/code/1?matchid=…&vendor=mi`）→ AES+gzip 解 → 微秒 → Pronto → `play 'pronto:…'`（僅 `chuangmi.ir.v2`）。

!!! danger "實測結論（你的設定）"
    `uv run --group tokens python tools/mi_tokens.py ir` 查出：你 **6 個 `miir.*` 全部掛在 `xiaomi.wifispeaker.l05c`（小愛音箱）** 底下——**2 個品牌配對**（TV 时间窃取器 = FFALCON `matchid 10982`、客厅空调 `matchid 4754`）＋ **4 個 DIY 自學**（圣诞树灯/电暖炉/暖暖地毯/冷风扇）。

    - **小愛音箱沒有本地 IR API** → 這 6 個**沒有一個能經 speaker 本地重播**。
    - **品牌配對**的碼在小米碼庫（用 matchid 解成 pronto）；**DIY 自學**的碼是雲端 learn、標準端點不直接匯出（al-one 也只是雲端 click，不匯出）。
    - 你目前**沒有能本地重播的 blaster**（`acpartner` 格式不合且偏 AC）。**要本地控電視，最實際 = 買一顆 `chuangmi.ir.v2`**，再用 [SmartIR](#path-3home-assistant-remote--smartir最佳-ux)（FFALCON 選碼庫）或重學。

### 用 `mi-tokens ir` 查你的遙控

```bash
uv run --group tokens python tools/mi_tokens.py ir   # 掃碼一次後 session 會快取，之後免掃
```
會列出每個 `miir.*` 的 **parent blaster**、鍵數、以及 **DIY(自學) vs 品牌配對(matchid)**，原始 keys/info 寫進 `.secrets/mi-ir.json`。這就是判斷「能不能／怎麼本地化」的第一步。

### 現在就能用：雲端觸發 `ir-send`（免硬體）

不必等買 blaster——`/v2/irdevice/controller/key/click` 讓雲端叫 parent blaster 發射，**DIY / 品牌配對都行**。實測送 `VOL+` 到 FFALCON TV 成功：

```bash
uv run --group tokens python tools/mi_tokens.py ir-send --remote 时间窃取器 --key VOL+
uv run --group tokens python tools/mi_tokens.py ir-send --remote 冷风扇 --key POWER --repeat 2
```

缺點：走雲端（依賴網路＋小米）、且要 speaker 在家電 IR 射程內。但**零硬體、可腳本化 / 給 Claude**。

### `ir-code`：把 IRDB matchid 解成 Pronto（本地重播用）

```bash
uv run --group tokens python tools/mi_tokens.py ir-code --matchid xm_1_199
```

抓碼庫 → AES-ECB/gzip 解 → 每顆鍵輸出 **Pronto**（可餵給 `chuangmi.ir.v2` 的 `play_pronto`）。

!!! warning "你的 TV 碼抽不到（controller_id ≠ matchid）"
    實測：TV 帳號的 `controller_id 10982` **不是**公開 IRDB 的 matchid（查無），所以**無法用它直接抽你的 FFALCON 碼**。雲端知道碼（所以 `ir-send` 能動），但不以帳號 ID 外露。要本地電視碼，最實際是 **SmartIR**（內建 FFALCON）或在 `chuangmi.ir.v2` 上**重學**。

> 參考實作：[`al-one/hass-xiaomi-miot`](https://github.com/al-one/hass-xiaomi-miot) 的 `remote.py`（列 controllers/keys、雲端 click）、[`ysard/mi_remote_database`](https://github.com/ysard/mi_remote_database)（碼庫解密到 pronto/Flipper）、[`MiEcosystem/miot-plugin-sdk`](https://github.com/MiEcosystem/miot-plugin-sdk) 的 `ircontroller.js`（官方 API）。

## Path 2：直接在本地重學（不抽取，最單純）

不折騰雲端抽碼，直接拿原廠遙控對著你**可本地控**的 blaster 學一次。今天就能跑（用 Python API；本機 `miiocli` 有 bug，見文末）：

```python
# 萬能遙控器 chuangmi.ir.v2（若你買了一顆）
from miio import ChuangmiIr
d = ChuangmiIr("<BLASTER_IP>", "<TOKEN>")
d.learn(1)                 # armed slot 1 → 對著按遙控
print(d.read(1))           # → base64 code，存起來重用
d.play("<BASE64_CODE>")    # 重播（也吃 'pronto:HEX'）

# 你已有的 acpartner.v2（零成本，射程/覆蓋較弱、偏冷氣）
from miio import AirConditioningCompanion as A
a = A("<IP>", "<TOKEN>", model="lumi.acpartner.v2")
a.learn(30); print(a.learn_result())   # armed → 按遙控 → 擷取 FE code
# 重播：a.send_ir_code(model_hex, code_hex) 或 raw send_ir_code(['FE…'])
```

先用 [`mi-tokens verify`](../concepts/auth-token.md) 確認 blaster 的 token + **即時 IP**（cloud 的 `localip` 常過期，工具會自動 ARP-by-MAC 解）。

## Path 3：Home Assistant `remote` + SmartIR（最佳 UX）

把萬能遙控器用 `xiaomi_miio` 的 `remote` 平台（host+token 直打 LAN）加進 HA，支援 `chuangmi.ir.v2`/`chuangmi.remote.v2`：

```yaml
remote:
  - platform: xiaomi_miio
    name: living_room_ir
    host: 192.168.31.x
    token: YOUR_BLASTER_TOKEN
    slot: 1
```

- **學**：`xiaomi_miio.remote_learn_command`（擷到的 base64 跳在 HA 通知）。**播**：`remote.send_command`（`raw:…` / `pronto:…`）。
- **免逐鍵學電視** → **SmartIR**（[`litinoveweedle/SmartIR`](https://github.com/litinoveweedle/SmartIR)，HACS）：`controller_data` 指向你的 `xiaomi_miio` **ChuangmiIr remote 實體**，`device_code` 選電視型號，長出完整 `media_player`。

!!! warning "SmartIR 的 Xiaomi = 萬能遙控器 remote 實體"
    SmartIR 的 Xiaomi 控制器**特指** `xiaomi_miio` 的 **ChuangmiIr `remote` 實體**——**不能**驅動 `lumi.acpartner`（不是 remote 實體）、也不能驅動音箱。

加進 HA 後就能經 [HA MCP](../solutions/home-assistant.md#接-claudeha-內建-mcp-server) 讓 Claude 噴 IR、或給 Siri/Google。

## 修好本機的 `miiocli`

本機 `miiocli` 目前壞了：`click` 8.2.x 與 `python-miio` 0.5.12 不相容（`TypeError: argument of type 'bool' is not iterable`）。**Python API 正常**（上面片段都能跑）。要用 CLI 就先 pin：

```bash
uv pip install 'click<8.2'   # 在 .venv 裡；或等 python-miio 升級
```

## 相關

- 為什麼 `miir.*` 沒 token 是正常的 → [本地 vs 雲端](../concepts/local-vs-cloud.md)、[我的裝置](../reference/devices.md)。
- 抽 token / 解即時 IP → [認證與 Token](../concepts/auth-token.md)。
- 把 blaster 接進中樞、曝露給 Claude → [Home Assistant 中樞](../solutions/home-assistant.md)。
