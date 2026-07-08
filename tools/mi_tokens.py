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


def cmd_verify(a: argparse.Namespace) -> int:
    """用已安裝的 miiocli 對某台裝置做 LAN 驗證，證明 token 本地可用。"""
    rows = json.loads(Path(a.out).read_text(encoding="utf-8"))
    dev = next((r for r in rows if r.get("did") == a.did), None)
    if not dev or not dev.get("localip") or not dev.get("token"):
        print(f"[mi-tokens] {a.did} 沒有 localip/token，無法本地驗證", file=sys.stderr)
        return 1
    cmd = [
        "uv", "run", "--group", "miio", "miiocli", "device",
        "--ip", dev["localip"], "--token", dev["token"], "info",
    ]
    print(f"[mi-tokens] miiocli device --ip {dev['localip']} --token … info")
    return subprocess.run(cmd).returncode


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

    pv = sub.add_parser("verify", help="用 miiocli 本地驗證某台 token")
    add_common(pv)
    pv.add_argument("--did", required=True, help="要驗證的裝置 did")
    pv.set_defaults(func=cmd_verify)

    a = p.parse_args()
    if not getattr(a, "func", None):
        p.print_help()
        return 2
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
