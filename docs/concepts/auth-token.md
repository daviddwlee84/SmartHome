# 認證與 Token（前置需求）

不管你選哪種控制方式，第一步都是先**拿到認證**。米家有兩種認證，剛好對應[本地 vs 雲端](local-vs-cloud.md)這條軸：

| 認證 | 取得方式 | 適用控制路徑 | 受[區域](account-region.md)影響？ |
|---|---|---|---|
| 裝置 **token** | 從小米雲端拉取，或離線抽 App 備份 | 本地 miIO/LAN 直控 | ✅ 要對區 |
| 帳號 **QR 登入** | 掃碼登入小米帳號 | 雲端 API | ✅ 登入到對應區 |

!!! danger "token 是裝置機密"
    device token 等於該裝置的控制金鑰，**不要**提交進 git／貼到公開場合。本 repo 的 `.secrets/` 已 gitignore，抽出來的 token 放那裡。

!!! warning "2026 實測結論（先看這個）"
    - `miiocli cloud`（底層 `micloud`）現在**多半登入失敗**——小米在密碼流加了 captcha＋2FA，而且它的 locale 清單**沒有 `tw`**，台灣帳號抓不到。詳見[登入疑難排解](login-troubleshooting.md)。
    - QR 登入的 `mijiaAPI` / `miot-mcp` 會**把你的 session token 走第三方 proxy `api.mijia.tech`**，而且拿不到 local token——只適合純雲端控制。
    - **要 token 就用本 repo 的 `mi-tokens`**（薄包 [Xiaomi-cloud-tokens-extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)：免密碼 QR、只連官方、支援 tw/sg）。

## 推薦：`mi-tokens`（官方 QR 抽 token）

本 repo 內建 `tools/mi_tokens.py`，免密碼 QR 登入**官方**小米雲，抽出每台 token + 本地 IP + BLE key：

```bash
uv run --group tokens python tools/mi_tokens.py extract
#  → 印出 http://127.0.0.1:31415，開瀏覽器用「米家 App」掃碼
#  → 掃完抓 tw,sg,cn 三區，寫到 .secrets/mi-tokens.json (chmod 600) + .secrets/devices.md
uv run --group tokens python tools/mi_tokens.py list                # 離線重印（token 預設遮蔽，--show 顯示）
uv run --group tokens python tools/mi_tokens.py verify --did <DID>  # 用 miiocli 本地驗證某台 token 可用
```

- 只連 `account.xiaomi.com` + `{region}.api.io.mi.com`（官方），**不經第三方**。
- 預設掃 `tw, sg, cn`（台灣帳號的裝置常在 tw 或 sg）；`--server tw` 可指定。
- 拿到 token 後即可本地直控：`uv run --group miio miiocli device --ip <IP> --token <TOKEN> info`。

## 其他方法

### `miiocli cloud`（本地 token，但現在多半壞）

```bash
uv run --group miio miiocli cloud list
```
`python-miio` 內建，但底層 `micloud` 已停更、密碼流被 captcha/2FA 擋（回 `Access denied`），且 locale **無 `tw`**。台灣帳號基本上用不了——改用上面的 `mi-tokens`。細節見[登入疑難排解](login-troubleshooting.md)。

### QR 純雲端控制（`mijiaAPI` / `miot-mcp`）

```bash
uv run --group mijia mijiaAPI login          # QR 免密碼，存 ~/.config/mijia-api/auth.json
uv run --group mijia mijiaAPI --list_devices
uv run --group mijia mijiaAPI mcp            # 內建 MCP server（stdio），可掛給 Claude
```
免密碼、給 Claude 控制很方便，**但有代價**：

!!! danger "會走第三方 proxy、且拿不到 token"
    `mijiaAPI`（`miot-mcp` 也用它）把 `serviceToken`/`ssecurity` 和每條裝置指令送到 **`api.mijia.tech`（非官方、作者自架）**，等於一個受信任的 MITM；而且**拿不到 local token**、沒有 tw 區切換。在意隱私就別用；要 token 用 `mi-tokens`。

### 離線 app-backup（`miio-extract-tokens`）

完全不連網，從 Mi Home 的 Android 備份讀 token：
```bash
uv run --group miio miio-extract-tokens mibackup.ab   # 加密備份加 --password <pw>
```
最私密，但 **`adb backup` 在 Android 12+ 已幾乎失效**、新版米家設 `allowBackup=false`，實際只在舊 Android／root 手機可行。

## 該用哪一種

| 你要 | 用 |
|---|---|
| **local token 做 LAN 直控**（推薦） | `mi-tokens`（官方 QR） |
| 純雲端控制、給 Claude、可接受第三方 proxy | `mijiaAPI` / `miot-mcp`（QR） |
| 完全離線、有配對過的舊 Android | `miio-extract-tokens` |
| （歷史）`miiocli cloud` | 多半已壞，見[登入疑難排解](login-troubleshooting.md) |

深入的失敗原因、安全驗證、tw 區陷阱 → **[登入疑難排解](login-troubleshooting.md)**。
