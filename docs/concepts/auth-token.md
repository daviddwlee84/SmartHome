# 認證與 Token（前置需求）

不管你選哪種控制方式，第一步都是先**拿到認證**。米家有兩種認證，剛好對應[本地 vs 雲端](local-vs-cloud.md)這條軸：

| 認證 | 取得方式 | 適用控制路徑 | 受[區域](account-region.md)影響？ |
|---|---|---|---|
| 裝置 **token** | 從小米雲端拉取（`miiocli cloud` 或抽取工具） | 本地 miIO/LAN 直控 | ✅ 要選對區才列得到 |
| 帳號 **QR 登入** | 掃碼登入小米帳號 | 雲端 API（mijiaAPI / 多數 MCP） | ✅ 登入到對應區 |

!!! danger "token 是裝置機密"
    device token 等於該裝置的控制金鑰，**不要**提交進 git、貼到公開場合或分享。抽出來的 token 建議存在本機受保護的設定檔。

## 方法一：`miiocli cloud` 抓 token（本地路線）

[`python-miio`](../control/cli.md) 內建雲端指令，用帳號登入後列出每台裝置的 IP 與 token：

```bash
pip install python-miio
miiocli cloud            # 依提示輸入帳號、密碼，以及 locale/region
```

- 會列出裝置的 `did`、**IP**、**token**、model 等。
- 拿到後就能離線本地直控：`miiocli device --ip <IP> --token <TOKEN> info`。
- **region 要選對**（見[帳號分區](account-region.md)），否則清單是空的。

### 當 `miiocli cloud` 失效時（fallback）

小米偶爾改版登入流程，導致 `miiocli cloud` 登入失敗。常見備援：

- **`Xiaomi-cloud-tokens-extractor`**（`PiotrMachowski/Xiaomi-cloud-tokens-extractor`）：社群最常用的獨立抽取工具，會問 region、逐區列出裝置與 token。
- 直接用 `miio.cloud` 模組的 `CloudInterface.get_devices()` 自己寫 script 抓。
- 改走 QR 登入類工具（見下），繞過 token。

## 方法二：QR 登入（雲端路線）

雲端方案（`mijiaAPI`、[`miot-mcp`](../control/mcp.md) 等）多半**只支援掃碼登入**：

- 啟動服務 → 產生 QR → 用米家 App 掃碼授權。
- 授權後把 session 存在本機（例如 `miot-mcp` 存在 `~/.miot-mcp/auth_data.json`）。
- 不需要逐台 token，帳號看得到的裝置就能控；但每次指令走雲端。

## 該用哪一種？

- 想要**本地、低延遲、離線** → 走 token（方法一）。
- 想要**最省事、覆蓋最廣**、或設備本來就只能雲端（BLE／紅外線） → 走 QR（方法二）。
- 兩者其實常常並用：本地能控的走 token，其餘走雲端。
