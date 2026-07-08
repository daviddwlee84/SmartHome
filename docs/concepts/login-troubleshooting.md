# 登入疑難排解

小米登入是整個流程最容易卡的地方。這頁把實測到的坑、根因、對策一次講清楚，並附上**安全驗證**（哪些工具只連官方、密碼怎麼處理）——這些結論是實際 grep 過各工具安裝後原始碼得到的，你可自行複核。

## `miiocli cloud` 回 `Access denied`（`MiCloudAccessDenied`）

`python-miio` 底層是 [`micloud`](https://pypi.org/project/micloud/) v0.6（2022 後幾乎停更），走帳密 POST 到 `account.xiaomi.com/pass/serviceLoginAuth2`。小米後來在這條 endpoint 對非 App client 加了 **captcha ＋ email/phone 2FA**，無人值守的帳密 POST 解不掉，就被擋成 `Access denied`。Home Assistant 的「Xiaomi Miio」雲端流程（HA → python-miio → micloud）撞同一道牆。

| 現象 | 根因 | 對策 |
|---|---|---|
| `miiocli cloud` 回 `Access denied` | 密碼流被 captcha/2FA 攔截 | 改走 QR（`mi-tokens` / `mijiaAPI`） |
| HA Xiaomi Miio 雲端登入失敗 | 繼承同一道牆 | 同上，或 `mi-tokens` 抽 token 後手填 |
| 帳密正確也被擋 | **網路層**：Cloudflare(1.1.1.1) DNS、AdGuard/PiHole、路由器地區限制（如 UniFi） | 換非 Cloudflare DNS、關廣告過濾、別擋 `api.io.mi.com` |
| 撞到 2FA 上限 | 每區每天約 3–5 封驗證信（記得翻垃圾信匣） | 等，或改 QR（不受此限） |

!!! note "這不是後門，是流程無法 headless 自動化"
    已驗證 `micloud` 與 extractor 只連小米官方網域，且密碼是先做 **unsalted MD5（大寫 hex）** 雜湊後才走 TLS 上傳，**明碼密碼從不出網卡**。全新登入解不掉 captcha/2FA 是結構性限制，不是工具藏了 backdoor。

## region 陷阱：`miiocli` 的 locale 沒有 `tw`

台灣帳號**不是**中國帳號，`cn` 一定抓不到。小米把帳號＋裝置綁在 Xiaomi Home App 配對當下選的區，走 `{region}.api.io.mi.com`。

!!! danger "python-miio 的 AVAILABLE_LOCALES 沒有 tw"
    `python-miio` 內建 locale 只有 `cn, de, i2, ru, sg, us`（＋`all`）——**沒有 `tw`**。所以 `miiocli cloud`、`micloud`、HA Xiaomi Miio 雲端流程會**默默漏掉**台灣帳號的裝置，清單看起來是空的。

| 工具 | 支援 region | 對台灣帳號 |
|---|---|---|
| python-miio / micloud | cn, de, i2, ru, sg, us | ❌ 無 tw |
| `mi-tokens` / Xiaomi-cloud-tokens-extractor | cn, de, us, ru, **tw**, **sg**, in, i2；留空掃全部 | ✅ |

實務：`mi-tokens` 預設掃 `tw, sg, cn`。很多台灣／東南亞使用者的裝置其實在 **`sg`**（配對時把 App 區域設成新加坡）。**「裝置清單是空的」最常見的原因是選錯區，不是帳密錯。**

## 安全驗證：哪些只連官方、密碼怎麼處理

| 工具 | 只連小米官方？ | 密碼處理 | 給 token？ |
|---|---|---|---|
| `mi-tokens` / extractor | ✅ `account.xiaomi.com` + `{region}.api.io.mi.com` | QR 免密／或 getpass 遮蔽＋MD5 後送 | ✅ |
| `miiocli cloud` / micloud | ✅ 官方 | ⚠️ `miio cloud` prompt 沒遮蔽（明碼回顯）＋MD5 後送 | ✅ |
| **`mijiaAPI` / `miot-mcp`** | ❌ **裝置流走第三方 `api.mijia.tech`** | QR 免密（但 token 走第三方） | ❌ |
| `miio-extract-tokens` | ✅ 零連網（離線） | 免 | ✅ |

!!! note "密碼明碼回顯 ≠ 外洩"
    `python-miio` 的 `miio cloud` 密碼 prompt 漏了 `hide_input=True`（`miio/cloud.py`），所以密碼會**明碼顯示在終端**——這是**顯示層**瑕疵，密碼仍先 MD5 再走 TLS 上傳、只到 `account.xiaomi.com`，不送第三方。`micloud` 自己的 CLI 有正確遮蔽。並避免用 `--password` 命令列參數（會進 shell history／`ps`），改用互動 getpass。

!!! danger "mijiaAPI / miot-mcp 走第三方 proxy"
    `mijiaAPI`（`apis.py:29` 寫死 `api_base_url = https://api.mijia.tech/app`）把你的 `serviceToken`/`ssecurity` 和每條裝置指令送到 **`api.mijia.tech`——非小米官方（作者自架、Tencent DNSPod、一般中國 IP）**。等於一個受信任的 MITM：proxy 端能記錄、重放、竄改你所有裝置資料與控制指令。純雲端控制且你信任它才用；要隱私／要 token 請走 `mi-tokens`（只連官方）。

## QR 免密碼但不等於零互動

QR 登入把授權交給手機 App，繞過 `serviceLoginAuth2` 的 captcha＋email-2FA，也不受每日 2FA 額度限制。但手機端偶爾仍會要求 SMS/OTP 確認——是「script 裡不打密碼」，不是「完全不用動手」。

要選哪條路（token / 純控制 / 離線）→ 見[認證與 Token](auth-token.md)的「該用哪一種」。
