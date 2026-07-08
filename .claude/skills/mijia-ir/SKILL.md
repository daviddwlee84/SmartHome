---
name: mijia-ir
description: Control the user's Xiaomi Mijia IR devices (TV, air-conditioner, fan, and DIY on/off remotes) via the cloud using this repo's mi-tokens CLI. Use whenever the user asks to control the TV (volume / mute / power / input / channel), set the air-conditioner (temperature / mode / on / off / status), or send any IR remote button — e.g. "電視靜音", "電視音量+", "開客廳冷氣 26 度", "冷氣關掉", "風扇開". Runs cloud IR through the 小愛音箱 blaster; no local hardware or Home Assistant needed.
---

# Mijia IR control

Control the user's cloud IR remotes (`miir.*`) through `tools/mi_tokens.py`. Run commands from the repo root with the `tokens` uv group. A QR-login session is cached in `.secrets/mi-session.json`; if a command prints `❌` with a non-zero `code`, the session likely expired — rerun with `--relogin` and tell the user to scan the QR.

## The user's remotes (from `.secrets/mi-ir.json`)

| 使用者會說 | `--remote` | 型別 |
|---|---|---|
| 電視 | `时间窃取器` | TV (FFALCON), 58 keys |
| 客廳 / 冷氣 | `客厅空调` | AC — **state-based** |
| 風扇 | `冷风扇` | fan |
| 聖誕燈 / 電暖爐 / 暖暖地毯 | `圣诞树灯` / `电暖炉` / `暖暖地毯` | DIY on/off |

If unsure of the exact remote or key, first **list** them:
- all remotes: `uv run --group tokens python tools/mi_tokens.py ir`
- one remote's keys: `uv run --group tokens python tools/mi_tokens.py ir-send --remote <name>` (omit `--key`)

## Send a TV / generic remote key

```bash
uv run --group tokens python tools/mi_tokens.py ir-send --remote <remote> --key <KEY> [--repeat N]
```
Common TV keys: `POWER`, `MUTE`, `VOL+`, `VOL-`, `INPUT`, `HOMEPAGE`, digit keys.

- 「電視靜音」→ `ir-send --remote 时间窃取器 --key MUTE`
- 「電視音量+」/「大聲一點」→ `ir-send --remote 时间窃取器 --key VOL+ --repeat 3`
- 「電視關機」→ `ir-send --remote 时间窃取器 --key POWER`
- 「開/關風扇」→ `ir-send --remote 冷风扇 --key POWER`

## Air-conditioner — absolute state

```bash
uv run --group tokens python tools/mi_tokens.py ir-ac [--temp 16-30] [--mode auto|cool|dry|heat|fan] [--on|--off|--status]
```
- 「開客廳冷氣 26 度」/「冷氣調 26 度制冷」→ `ir-ac --temp 26 --mode cool`
- 「冷氣關掉」→ `ir-ac --off`
- 「冷氣現在幾度」→ `ir-ac --status`
- 「冷氣調暖 24 度」→ `ir-ac --temp 24 --mode heat`

`ir-ac` 預設控制唯一的 IR 冷氣遙控 `客厅空调`（會印出目標名稱）；若有多台就加 `--remote 客厅空调`。注意 `主卧空调`／`书房空调`／`風` 是 `lumi.acpartner`（實體空調伴侶，不是 IR 遙控），`ir-ac` **不**控它們——那些要走 HA 或直接對該裝置下 MIoT 指令。

## Guardrails

- This is **cloud** IR (through Xiaomi + the 小愛音箱 blaster) — needs internet and the speaker in IR range of the appliance. On success the CLI prints `✅`.
- IR is one-way: **no absolute TV volume** (only `VOL+`/`VOL-`); the AC is state-based so absolute temp/mode works.
- Just run explicit requests. For a potentially disruptive power action the user did **not** ask for (e.g. turning the AC on unprompted), confirm first.
- Once the user sets up Home Assistant, prefer its built-in MCP over this skill (brand-agnostic, no third-party proxy) — see `docs/solutions/home-assistant.md`.
