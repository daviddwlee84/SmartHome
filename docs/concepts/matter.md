# Matter 的角色

Matter 是跨生態的智慧家庭標準。它對米家整合的意義是：**支援 Matter 的裝置可以被 Apple Home、Google Home、Alexa 直接採納，不必再架 Homebridge 之類的橋接**。但現階段對米家來說，它還是個「加分項」而非「主力」。

## 現況重點

- **部分新品開始支援**：Xiaomi 已在一些新裝置（例如新款門鎖）與**多模網關**（如 Xiaomi Smart Home Hub 2）上加入 Matter，能把旗下部分設備橋接到 Matter。
- **Matter = 原生跨平台**：一旦裝置以 Matter 端點出現，Apple Home / Google / Alexa 都能直接配對控制，這是最乾淨的[聯動](../ecosystem/apple-home.md)方式。
- **涵蓋率仍低、且看型號/韌體/地區**：不是所有米家設備都能走 Matter；能不能用高度依賴**具體型號、韌體版本與所在地區**。
- **Matter ≠ HomeKit 認證**：Matter 支援代表能被 Matter 控制器（含 Apple Home）控制；這跟「Apple HomeKit 原生認證」是兩回事。

!!! tip "先查你手上的裝置"
    Matter 能省掉橋接，但別假設你的設備都支援。逐台確認型號與韌體，記錄在 [我的裝置](../reference/devices.md)。

## 對決策的影響

| 情況 | 建議 |
|---|---|
| 新買、且明確標示 Matter | 優先走 Matter，直接進 Apple／Google，免橋接 |
| 舊有大量非 Matter 設備 | 仍以 [Home Assistant](../solutions/index.md) 或 [Homebridge](../ecosystem/open-source-homekit.md) 橋接為主 |
| 混合 | 中樞（HA）＋逐步把新設備 Matter 化 |
