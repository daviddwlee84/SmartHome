#!/usr/bin/env python3
"""mi-tokens — 免密碼 QR 登入「官方」小米雲，抽出每台裝置的 miIO token（+ 本地 IP、
BLE beaconkey），並產生 devices.md 表格，供本地 (LAN) 控制使用。

這是 PiotrMachowski/Xiaomi-cloud-tokens-extractor (MIT) 的薄包裝。相對於 mijiaAPI
（會把你的 serviceToken 透過第三方 proxy api.mijia.tech 中轉、且拿不到 local token），
本工具：

* 只連官方網域：account.xiaomi.com + {region}.api.io.mi.com
* 支援 tw / sg 伺服器（miiocli/micloud 的 locale 清單根本沒有 tw）
* 產出 mijiaAPI 拿不到的 per-device token + 本地 IP + BLE key
* 免密碼（走 QR），token 輸出 chmod 600 + 放進 gitignore 的 .secrets/

用法：
    uv run --group tokens python tools/mi_tokens.py extract          # QR 登入抽 token（掃 tw,sg,cn）
    uv run --group tokens python tools/mi_tokens.py extract --server tw --server sg
    uv run --group tokens python tools/mi_tokens.py list             # 離線重印上次結果
    uv run --group tokens python tools/mi_tokens.py verify --did <DID>  # 用 miiocli 本地驗證某台
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXTRACTOR_DIR = REPO / ".external" / "Xiaomi-cloud-tokens-extractor"
EXTRACTOR_PY = EXTRACTOR_DIR / "token_extractor.py"
EXTRACTOR_REPO = "https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor"
SECRETS_DIR = REPO / ".secrets"
DEFAULT_JSON = SECRETS_DIR / "mi-tokens.json"
DEFAULT_MD = SECRETS_DIR / "devices.md"
# 台灣帳號的裝置常綁在 tw 或 sg（配對時 App 選的區），cn 對非中國帳號一定空。
DEFAULT_REGIONS = ["tw", "sg", "cn"]


def _ensure_extractor() -> None:
    """第三方 extractor 放在 gitignore 的 .external/，缺了就自動 clone。"""
    if EXTRACTOR_PY.exists():
        return
    EXTRACTOR_DIR.parent.mkdir(parents=True, exist_ok=True)
    print(f"[mi-tokens] 找不到 extractor，clone 到 {EXTRACTOR_DIR} …")
    subprocess.run(
        ["git", "clone", "--depth", "1", EXTRACTOR_REPO, str(EXTRACTOR_DIR)],
        check=True,
    )


def _load_extractor():
    """import token_extractor.py，但不讓它模組層的 argparse 吃掉我們的 argv。"""
    _ensure_extractor()
    saved_argv = sys.argv
    sys.argv = ["token_extractor"]  # 中性參數：extractor 全用預設值
    try:
        spec = importlib.util.spec_from_file_location("token_extractor", EXTRACTOR_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except ModuleNotFoundError as e:
        raise SystemExit(
            f"[mi-tokens] 缺相依套件 ({e.name})。請用：\n"
            f"    uv sync --group tokens\n"
            f"或以 `uv run --group tokens python tools/mi_tokens.py ...` 執行。"
        )
    finally:
        sys.argv = saved_argv
    mod.args.host = "127.0.0.1"  # QR 影像 server 顯示 http://127.0.0.1:31415
    return mod


def _collect(conn, regions: list[str]) -> list[dict]:
    """逐區抓 home → device_info，跨區以 did 去重。"""
    devices: dict[str, dict] = {}
    for country in regions:
        homes: list[dict] = []
        h = conn.get_homes(country)
        if h and h.get("result"):
            for x in h["result"].get("homelist", []) or []:
                homes.append({"home_id": x["id"], "home_owner": conn.userId})
        cnt = conn.get_dev_cnt(country)
        if cnt and cnt.get("result"):
            for x in cnt["result"].get("share", {}).get("share_family", []) or []:
                homes.append({"home_id": x["home_id"], "home_owner": x["home_owner"]})
        for home in homes:
            resp = conn.get_devices(country, home["home_id"], home["home_owner"])
            info = ((resp or {}).get("result") or {}).get("device_info") or []
            for d in info:
                did = d.get("did", "")
                if not did or did in devices:
                    continue
                rec = {
                    "name": d.get("name", ""),
                    "model": d.get("model", ""),
                    "did": did,
                    "region": country,
                    "localip": d.get("localip", ""),
                    "token": d.get("token", ""),
                    "mac": d.get("mac", ""),
                }
                if "blt" in did:  # BLE 裝置：多抓 beaconkey
                    bk = conn.get_beaconkey(country, did)
                    if bk and bk.get("result"):
                        rec["beaconkey"] = bk["result"].get("beaconkey", "")
                devices[did] = rec
    return list(devices.values())


def _render_md(rows: list[dict], reveal: bool) -> str:
    def tok(v: str) -> str:
        if not v:
            return ""
        return v if reveal else "…redacted…"

    lines = [
        "| 裝置 | 型號 (model) | 區 | 本地 IP | token | MAC |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.get('name','')} | `{r.get('model','')}` | {r.get('region','')} "
            f"| {r.get('localip','')} | {tok(r.get('token',''))} | {r.get('mac','')} |"
        )
    return "\n".join(lines)


def _write_secret(path: Path, data: str) -> None:
    SECRETS_DIR.mkdir(exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)


def cmd_extract(a: argparse.Namespace) -> int:
    mod = _load_extractor()
    conn = mod.QrCodeXiaomiCloudConnector()
    print("[mi-tokens] 免密碼 QR 登入 — 開瀏覽器掃碼（見下方網址），用『米家 App』掃：")
    if not conn.login():
        print("[mi-tokens] 登入失敗（QR 逾時或被取消）", file=sys.stderr)
        return 1
    regions = a.server or DEFAULT_REGIONS
    rows = _collect(conn, regions)
    if not rows:
        print(
            f"[mi-tokens] 這些區沒找到裝置：{regions}。"
            f"改用 --server 指定或留空掃全部（tw,sg,cn,de,us,ru,in,i2）。",
            file=sys.stderr,
        )
    _write_secret(Path(a.out), json.dumps(rows, ensure_ascii=False, indent=2))
    _write_secret(Path(a.md), _render_md(rows, reveal=True) + "\n")
    print(f"[mi-tokens] {len(rows)} 台裝置 → {a.out} (chmod 600) + {a.md}")
    print()
    print(_render_md(rows, reveal=a.show))  # stdout 預設遮蔽 token，--show 才顯示
    if not a.show:
        print("\n（token 已遮蔽；完整值在上面的 .secrets/ 檔，或加 --show）")
    return 0


def cmd_list(a: argparse.Namespace) -> int:
    if not Path(a.out).exists():
        print(f"[mi-tokens] 找不到 {a.out}，請先跑 extract", file=sys.stderr)
        return 1
    rows = json.loads(Path(a.out).read_text(encoding="utf-8"))
    print(_render_md(rows, reveal=a.show))
    return 0


def _norm_mac(mac: str) -> str:
    return ":".join(f"{int(p, 16):02X}" for p in mac.split(":"))


def _arp_ip_for(mac: str) -> str | None:
    """查目前 LAN 上這個 MAC 的即時 IP（cloud 回的 localip 常過期）。"""
    if not mac:
        return None
    try:
        target = _norm_mac(mac)
    except ValueError:
        return None
    out = subprocess.run(["arp", "-an"], capture_output=True, text=True).stdout
    for ln in out.splitlines():
        if "incomplete" in ln:
            continue
        m = re.search(r"\(([\d.]+)\) at ([0-9a-fA-F:]+)", ln)
        if not m:
            continue
        try:
            if _norm_mac(m.group(2)) == target:
                return m.group(1)
        except ValueError:
            continue
    return None


def cmd_verify(a: argparse.Namespace) -> int:
    """對某台裝置做 LAN 本地驗證（直接用 python-miio API，不經有 bug 的 miiocli CLI）。"""
    rows = json.loads(Path(a.out).read_text(encoding="utf-8"))
    dev = next((r for r in rows if r.get("did") == a.did), None)
    if not dev:
        print(f"[mi-tokens] 找不到 did={a.did}", file=sys.stderr)
        return 1
    token = dev.get("token")
    if not token:
        print(f"[mi-tokens] {dev.get('model','')} 沒有 token（IR 虛擬遙控/雲端裝置），無法本地驗證", file=sys.stderr)
        return 1
    # cloud 的 localip 常過期：優先用 ARP 查該 MAC 的即時 IP
    ip = dev.get("localip") or ""
    live = _arp_ip_for(dev.get("mac", ""))
    if live and live != ip:
        print(f"[mi-tokens] cloud IP {ip or '-'} 已過期，改用 LAN 現值 {live}")
        ip = live
    elif live:
        ip = live
    if not ip:
        print(f"[mi-tokens] {dev.get('model','')} 沒有可用 IP（多半不在你目前的 LAN）", file=sys.stderr)
        return 1
    try:
        from miio import Device
    except ModuleNotFoundError:
        raise SystemExit(
            "[mi-tokens] verify 需要 python-miio，請用：\n"
            "    uv run --group miio --group tokens python tools/mi_tokens.py verify --did <DID>"
        )
    try:
        info = Device(ip, token).info()
        print(
            f"[mi-tokens] ✅ {dev.get('name','')}（{dev.get('model','')}）@ {ip} 本地可控"
            f" — model={info.model} fw={info.firmware_version}"
        )
        return 0
    except Exception as e:  # noqa: BLE001 — 回報任何本地失敗
        print(f"[mi-tokens] ❌ {dev.get('model','')} @ {ip} 本地失敗：{type(e).__name__}: {e}")
        print("   （多半是裝置離線、或你不在該裝置所在的 LAN）", file=sys.stderr)
        return 1


# ---------- IR: enumerate cloud miir.* remotes ----------
SESSION_JSON = SECRETS_DIR / "mi-session.json"
IR_JSON = SECRETS_DIR / "mi-ir.json"


def _load_session() -> dict | None:
    if not SESSION_JSON.exists():
        return None
    try:
        return json.loads(SESSION_JSON.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_session(conn) -> None:
    _write_secret(SESSION_JSON, json.dumps({
        "userId": conn.userId, "ssecurity": conn._ssecurity,
        "serviceToken": conn._serviceToken,
    }, indent=2))


def _install_terminal_qr(conn) -> None:
    """把登入 QR 直接畫在終端機（python-qrcode）；browser :31415 仍保留為 fallback。"""
    try:
        import qrcode
    except ImportError:
        return
    orig = conn.login_step_2

    def step2():
        url = getattr(conn, "_login_url", None)
        if url:
            print("\n[mi-tokens] 用『米家 App』掃描下方 QR：\n")
            qr = qrcode.QRCode(border=1)
            qr.add_data(url)
            qr.make(fit=True)
            qr.print_ascii(invert=True)
        return orig()

    conn.login_step_2 = step2


def _connector(mod, force_login: bool = False):
    """回傳登入好的 connector；能沿用 .secrets/mi-session.json 就不重掃 QR。"""
    conn = mod.QrCodeXiaomiCloudConnector()
    sess = None if force_login else _load_session()
    if sess and sess.get("serviceToken") and sess.get("ssecurity") and sess.get("userId"):
        conn.userId = sess["userId"]
        conn._ssecurity = sess["ssecurity"]
        conn._serviceToken = sess["serviceToken"]
        return conn, True
    _install_terminal_qr(conn)
    print("[mi-tokens] 免密碼 QR 登入（掃終端機 QR，或開 http://127.0.0.1:31415）：")
    if not conn.login():
        raise SystemExit("[mi-tokens] 登入失敗（QR 逾時或被取消）")
    _save_session(conn)
    return conn, False


def _api(conn, country: str, path: str, payload: dict):
    url = conn.get_api_url(country) + path
    params = {"data": json.dumps(payload, separators=(",", ":"))}
    return conn.execute_api_call_encrypted(url, params)


def _fetch_devices(conn, regions: list[str]) -> dict:
    """did -> {model,name,region,parent_id}，跨區。"""
    devmap: dict[str, dict] = {}
    for country in regions:
        homes: list[tuple] = []
        h = conn.get_homes(country)
        if h and h.get("result"):
            for x in h["result"].get("homelist", []) or []:
                homes.append((x["id"], conn.userId))
        cnt = conn.get_dev_cnt(country)
        if cnt and cnt.get("result"):
            for x in cnt["result"].get("share", {}).get("share_family", []) or []:
                homes.append((x["home_id"], x["home_owner"]))
        for home_id, owner in homes:
            resp = conn.get_devices(country, home_id, owner)
            for d in ((resp or {}).get("result") or {}).get("device_info") or []:
                did = str(d.get("did", ""))
                if did and did not in devmap:
                    devmap[did] = {
                        "model": d.get("model", ""), "name": d.get("name", ""),
                        "region": country, "parent_id": str(d.get("parent_id", "") or ""),
                    }
    return devmap


def _keys_have_code(keys_resp) -> tuple[int, bool]:
    """(鍵數, 是否有任何 raw code)。回應結構不確定，盡量容錯。"""
    res = (keys_resp or {}).get("result")
    keys = res.get("keys") or res.get("list") or [] if isinstance(res, dict) else (res or [])
    has_code = any(
        isinstance(k, dict) and (k.get("code") or k.get("ir_code") or k.get("value"))
        for k in (keys if isinstance(keys, list) else [])
    )
    return (len(keys) if isinstance(keys, list) else 0), has_code


def cmd_ir(a: argparse.Namespace) -> int:
    """列出雲端 miir.* 遙控、其 parent blaster、以及 DIY(有 raw code) vs 品牌配對。"""
    mod = _load_extractor()
    conn, reused = _connector(mod, force_login=a.relogin)
    regions = a.server or DEFAULT_REGIONS
    devmap = _fetch_devices(conn, regions)
    if not devmap and reused:
        print("[mi-tokens] session 可能過期，改重新 QR 登入 …")
        conn, reused = _connector(mod, force_login=True)
        devmap = _fetch_devices(conn, regions)
    if reused:
        print("[mi-tokens] 沿用已存 session（--relogin 可強制重登）")

    miirs = {did: v for did, v in devmap.items() if v["model"].startswith("miir")}
    if not miirs:
        print(f"[mi-tokens] 這些區沒找到 miir.* 遙控：{regions}", file=sys.stderr)
        return 1

    dump, rows = {}, []
    for did, v in miirs.items():
        country = v["region"]
        parent = devmap.get(v["parent_id"], {})
        keys_resp = _api(conn, country, "/v2/irdevice/controller/keys", {"did": did})
        info_resp = _api(conn, country, "/v2/irdevice/controller/info", {"did": did})
        nkeys, _ = _keys_have_code(keys_resp)
        info_res = (info_resp or {}).get("result") or {}
        try:
            cid = int(info_res.get("controller_id") or 0)
        except (TypeError, ValueError):
            cid = 0
        brand = info_res.get("brand_id")
        if cid > 0:
            kind = "品牌配對"
        elif info_res.get("controller_id") is not None:
            kind = "DIY(自學)"
        else:
            kind = "未知"
        dump[did] = {
            "model": v["model"], "name": v["name"], "region": country,
            "parent_id": v["parent_id"], "parent_model": parent.get("model", "?"),
            "parent_name": parent.get("name", ""), "keys": nkeys, "kind": kind,
            "controller_id": cid, "brand_id": brand,
            "raw_keys": keys_resp, "raw_info": info_resp,
        }
        rows.append((v["model"], v["name"], parent.get("model", "?"), nkeys, kind, cid or "—"))

    _write_secret(IR_JSON, json.dumps(dump, ensure_ascii=False, indent=2))
    parents = sorted({r[2] for r in rows})
    print(f"\n[mi-tokens] {len(rows)} 個 miir.* 遙控 → {IR_JSON} (chmod 600，含原始 keys/info)\n")
    print("| 遙控 model | 名稱 | parent blaster | 鍵數 | 類型 | matchid |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |")
    print(f"\nparent blaster：{', '.join(parents)}")
    print("判讀：品牌配對 → 碼在小米碼庫(matchid)，可解成 pronto；DIY(自學) → 雲端 learn、碼不直接匯出。")
    print("兩者要本地重播都需要一顆能本地控的 blaster（chuangmi.ir.v2）；小愛音箱沒有本地 IR API。")
    return 0


def cmd_ir_send(a: argparse.Namespace) -> int:
    """雲端觸發某遙控的某顆鍵（經 parent blaster 發射）——DIY/品牌配對皆可，免本地硬體。"""
    if not IR_JSON.exists():
        print("[mi-tokens] 先跑 `... ir` 建立 .secrets/mi-ir.json", file=sys.stderr)
        return 1
    ir = json.loads(IR_JSON.read_text(encoding="utf-8"))
    tgt = next(((did, r) for did, r in ir.items()
                if a.remote.lower() in (str(r.get("name", "")) + r.get("model", "") + did).lower()), None)
    if not tgt:
        print("[mi-tokens] 找不到遙控。可用：" + ", ".join(r["name"] for r in ir.values()), file=sys.stderr)
        return 1
    did, r = tgt
    keys = ((r.get("raw_keys") or {}).get("result") or {}).get("keys") or []
    if not a.key:
        print(f"[mi-tokens] {r['name']}（{r['model']}）可用的鍵（{len(keys)}）：")
        for x in keys:
            print(f"  {str(x.get('name','')):16} {x.get('display_name','')}")
        return 0
    k = next((x for x in keys if a.key.upper() in (str(x.get("name", "")) + str(x.get("display_name", ""))).upper()), None)
    if not k:
        print(f"[mi-tokens] {r['name']} 沒有含「{a.key}」的鍵。可用："
              + ", ".join(f"{x['id']}:{x['name']}" for x in keys), file=sys.stderr)
        return 1
    mod = _load_extractor()
    conn, _ = _connector(mod, force_login=a.relogin)
    cid = int(r.get("controller_id") or 0)
    payload = {"did": did, "key_id": int(k["id"])}
    if cid:
        payload["controller_id"] = cid
    country = r.get("region", "cn")
    resp = _api(conn, country, "/v2/irdevice/controller/key/click", payload)
    ok = isinstance(resp, dict) and resp.get("code") == 0
    print(f"[mi-tokens] {'✅ 已送出' if ok else '❌ 失敗'}：{k['name']}"
          f"（{k.get('display_name', '')}）→ {r['name']}（雲端 → {r.get('parent_model', '')} 發射）"
          + ("" if ok else f" — {resp}"))
    for _ in range(max(0, a.repeat - 1)):
        if ok:
            _api(conn, country, "/v2/irdevice/controller/key/click", payload)
    if ok and a.repeat > 1:
        print(f"[mi-tokens]   （共送 {a.repeat} 次）")
    return 0 if ok else 1


EXTERNAL = REPO / ".external"
YSARD_DIR = EXTERNAL / "mi_remote_database"


def _ensure_ysard() -> None:
    if (YSARD_DIR / "src" / "crypt_utils.py").exists():
        return
    print(f"[mi-tokens] clone IR 碼庫工具到 {YSARD_DIR} …")
    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/ysard/mi_remote_database", str(YSARD_DIR)], check=True)


def _timings_to_pronto(timings: list, freq: int) -> str:
    """微秒 ON/OFF 時序 + 載波頻率 → Pronto hex（可餵給 chuangmi.ir.v2 play_pronto）。"""
    fw = round(1_000_000 / (freq * 0.241246))
    cycles = [max(1, round(t * freq / 1_000_000)) for t in timings]
    if len(cycles) % 2:
        cycles.append(1)
    words = [0x0000, fw, len(cycles) // 2, 0x0000] + cycles
    return " ".join(f"{w:04X}" for w in words)


def cmd_ir_code(a: argparse.Namespace) -> int:
    """給 IRDB matchid（如 xm_1_199），抓碼 → 解密 → 每顆鍵輸出 Pronto。"""
    _ensure_ysard()
    sys.path.insert(0, str(YSARD_DIR / "src"))
    import crypt_utils as cu  # ysard (AGPL)：僅本機引用、不隨本 repo 散布
    txt = cu.build_url("/controller/code/1", [("matchid", a.matchid), ("vendor", "mi")], country=a.country)
    data = (json.loads(txt) or {}).get("data")
    if not isinstance(data, dict) or not data.get("key"):
        print(f"[mi-tokens] IRDB 查無 matchid={a.matchid}。"
              "\n  注意：米家帳號的 controller_id（如你 TV 的 10982）不是 IRDB matchid，"
              "不能直接查——請從 IRDB 品牌樹找型號，或改用 SmartIR。", file=sys.stderr)
        return 1
    freq = int(data.get("frequency") or 38000)
    out = {}
    for btn, enc in data["key"].items():
        try:
            out[btn] = {"frequency": freq, "pronto": _timings_to_pronto(cu.process_xiaomi_shit(enc), freq)}
        except Exception as e:  # noqa: BLE001
            out[btn] = {"error": f"{type(e).__name__}: {e}"}
    path = SECRETS_DIR / f"ir-code-{a.matchid}.json"
    _write_secret(path, json.dumps(out, ensure_ascii=False, indent=2))
    print(f"[mi-tokens] matchid={a.matchid} freq={freq}Hz，{len(out)} 顆鍵 → {path}")
    for btn, v in list(out.items())[:8]:
        print(f"  {btn:18} {str(v.get('pronto', v.get('error','')))[:52]}…")
    print("\n重播：chuangmi.ir.v2 → `miiocli chuangmi_ir play 'pronto:<hex>'`（或 HA remote.send_command）。")
    return 0


_AC_MODES = {"auto": 0, "cool": 1, "dry": 2, "heat": 3, "fan": 4}


def _miot_ok(resp) -> bool:
    if not isinstance(resp, dict) or resp.get("code") != 0:
        return False
    res = resp.get("result")
    if isinstance(res, list):
        return all(x.get("code", 0) == 0 for x in res if isinstance(x, dict))
    return True


def cmd_ir_ac(a: argparse.Namespace) -> int:
    """冷氣絕對控制（走 MIoT-spec 設溫度/模式/開關）——TV 音量做不到絕對，但冷氣是狀態式的。"""
    if not IR_JSON.exists():
        print("[mi-tokens] 先跑 `... ir` 建立 .secrets/mi-ir.json", file=sys.stderr)
        return 1
    ir = json.loads(IR_JSON.read_text(encoding="utf-8"))
    if a.remote:
        tgt = next(((did, r) for did, r in ir.items()
                    if a.remote.lower() in (str(r.get("name", "")) + r.get("model", "") + did).lower()), None)
    else:
        tgt = next(((did, r) for did, r in ir.items() if r["model"].startswith("miir.aircondition")), None)
    if not tgt:
        print("[mi-tokens] 找不到冷氣遙控（miir.aircondition.*）", file=sys.stderr)
        return 1
    did, r = tgt
    country = r.get("region", "cn")
    if a.temp is not None and not (16 <= a.temp <= 30):
        print("[mi-tokens] --temp 需 16-30", file=sys.stderr)
        return 1
    mode_val = None
    if a.mode:
        mode_val = _AC_MODES.get(a.mode.lower())
        if mode_val is None:
            print("[mi-tokens] --mode 需為 " + "/".join(_AC_MODES), file=sys.stderr)
            return 1
    mod = _load_extractor()
    conn, _ = _connector(mod, force_login=a.relogin)
    if a.status:
        info = _api(conn, country, "/v2/irdevice/controller/info", {"did": did})
        print(f"[mi-tokens] {r['name']} 目前 ac_state：{(info or {}).get('result', {}).get('ac_state')}")
        return 0
    if a.off:
        resp = _api(conn, country, "/miotspec/action", {"params": {"did": did, "siid": 2, "aiid": 5, "in": []}})
        print(f"[mi-tokens] {'✅ 已關冷氣' if _miot_ok(resp) else f'❌ {resp}'}")
        return 0 if _miot_ok(resp) else 1
    props = []
    if mode_val is not None:
        props.append({"did": did, "siid": 2, "piid": 1, "value": mode_val})
    if a.temp is not None:
        props.append({"did": did, "siid": 2, "piid": 2, "value": a.temp})
    if not props and not a.on:
        print("[mi-tokens] 指定 --temp / --mode / --on / --off / --status 其一", file=sys.stderr)
        return 1
    if props:
        resp = _api(conn, country, "/miotspec/prop/set", {"params": props})
        tag = (a.mode or "") + (f" {a.temp}°C" if a.temp is not None else "")
        print(f"[mi-tokens] 設定{tag}：{'✅' if _miot_ok(resp) else '❌ ' + str(resp)}")
    resp = _api(conn, country, "/miotspec/action", {"params": {"did": did, "siid": 2, "aiid": 6, "in": []}})
    print(f"[mi-tokens] 開機/送出：{'✅ 已送出（看冷氣有沒有反應）' if _miot_ok(resp) else '❌ ' + str(resp)}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        prog="mi-tokens",
        description="免密碼 QR 登入官方小米雲、抽 per-device token（tw/sg 友善）",
    )
    sub = p.add_subparsers(dest="cmd")

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--out", default=str(DEFAULT_JSON), help="tokens JSON 路徑")
        sp.add_argument("--show", action="store_true", help="stdout 顯示完整 token（預設遮蔽）")

    pe = sub.add_parser("extract", help="QR 登入並抽 token")
    add_common(pe)
    pe.add_argument("--server", action="append", help="區域(可重複)；預設 tw sg cn")
    pe.add_argument("--md", default=str(DEFAULT_MD), help="devices.md 輸出路徑")
    pe.set_defaults(func=cmd_extract)

    pl = sub.add_parser("list", help="離線重印上次 extract 結果")
    add_common(pl)
    pl.set_defaults(func=cmd_list)

    pv = sub.add_parser("verify", help="本地驗證某台 token（LAN，自動 ARP 解 IP）")
    add_common(pv)
    pv.add_argument("--did", required=True, help="要驗證的裝置 did")
    pv.set_defaults(func=cmd_verify)

    pi = sub.add_parser("ir", help="列出雲端 miir.* 遙控：parent blaster + DIY/品牌配對")
    add_common(pi)
    pi.add_argument("--server", action="append", help="區域(可重複)；預設 tw sg cn")
    pi.add_argument("--relogin", action="store_true", help="強制重新 QR 登入（忽略存的 session）")
    pi.set_defaults(func=cmd_ir)

    ps = sub.add_parser("ir-send", help="雲端觸發遙控某鍵（免本地硬體，DIY/品牌皆可）")
    ps.add_argument("--remote", required=True, help="遙控名稱/型號/did（子字串）")
    ps.add_argument("--key", help="鍵名（子字串，如 VOL+ / POWER）；省略則列出可用鍵")
    ps.add_argument("--repeat", type=int, default=1, help="送幾次")
    ps.add_argument("--relogin", action="store_true")
    ps.set_defaults(func=cmd_ir_send)

    pc = sub.add_parser("ir-code", help="IRDB matchid → 每鍵 Pronto（給 chuangmi.ir.v2）")
    pc.add_argument("--matchid", required=True, help="IRDB matchid，如 xm_1_199")
    pc.add_argument("--country", default="CN", help="碼區域（部分碼有地區差異）")
    pc.set_defaults(func=cmd_ir_code)

    pa = sub.add_parser("ir-ac", help="冷氣絕對控制（設溫度/模式/開關，MIoT-spec）")
    pa.add_argument("--remote", help="冷氣遙控（子字串）；預設第一個 miir.aircondition")
    pa.add_argument("--temp", type=int, help="目標溫度 16-30")
    pa.add_argument("--mode", help="模式：auto/cool/dry/heat/fan")
    pa.add_argument("--on", action="store_true", help="開機")
    pa.add_argument("--off", action="store_true", help="關機")
    pa.add_argument("--status", action="store_true", help="讀目前 ac_state")
    pa.add_argument("--relogin", action="store_true")
    pa.set_defaults(func=cmd_ir_ac)

    a = p.parse_args()
    if not getattr(a, "func", None):
        p.print_help()
        return 2
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
