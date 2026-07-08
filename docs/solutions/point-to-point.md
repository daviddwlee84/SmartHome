# 點對點橋接

不架任何中樞，直接一條線接一件事。**最小、最快，但每種能力各自為政、逐台手接**。適合只有 1–2 台設備、臨時用途。

## 組成

| 能力 | 工具 | 連線 |
|---|---|---|
| 控制 | [`python-miio`](../control/cli.md)（CLI） | 本地 miIO（需 token） |
| Siri | [`homebridge-miot`](../ecosystem/apple-home.md) | 經 Homebridge（需 token） |
| Google | [官方帳號綁定](../ecosystem/google-home.md) | 雲端 |

## 什麼時候用

- 只有少數幾台設備，不值得架 HA。
- 臨時、一次性的控制或腳本。
- 想先玩玩看 miIO 本地協議。

## 限制

- 每種能力各自設定、各自維護，換設備要重接。
- 沒有統一的自動化／場景層。
- 需要逐台處理 [token](../concepts/auth-token.md)。

規模一旦長大，建議升級成 [Home Assistant 中樞](home-assistant.md)或 [MijiaPilot](mijiapilot.md)。
