# -*- coding: utf-8 -*-
"""
update_hashes.py  —  manifest.json 의 sha256 을 자동으로 채워주는 헬퍼
========================================================================
당신(관리자)이 모드를 추가/변경할 때만 쓰는 도구입니다. 친구에게는 안 줍니다.

사용법:
  1) URL 하나의 해시만 출력 (manifest 안 건드림):
        python update_hashes.py --url https://.../mod.jar

  2) manifest.json 의 모든 entry 를 url 에서 받아 sha256 자동 기입:
        python update_hashes.py --fill manifest.json

     - sha256 이 비었거나 "0000..." 인 항목만 채웁니다(기본).
     - 전부 강제로 다시 계산하려면 --force 추가.

표준 라이브러리만 사용합니다.
"""

import sys
import ssl
import json
import argparse
import hashlib
import urllib.request
import urllib.parse

SSL_CONTEXT = ssl.create_default_context()
PLACEHOLDER = "0" * 64


def fetch(url: str) -> bytes:
    if urllib.parse.urlparse(url).scheme != "https":
        raise SystemExit(f"HTTPS 주소만 허용됩니다: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "imi-hasher"})
    print(f"  다운로드: {url}")
    with urllib.request.urlopen(req, timeout=120, context=SSL_CONTEXT) as r:
        return r.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cmd_url(url: str):
    digest = sha256(fetch(url))
    print(f"\nSHA-256: {digest}\n")


def cmd_fill(path: str, force: bool):
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest.get("entries", [])
    changed = 0
    for e in entries:
        cur = (e.get("sha256") or "").lower()
        needs = force or (not cur) or cur == PLACEHOLDER
        name = e.get("name", e.get("url", "?"))
        if not needs:
            print(f"  건너뜀(이미 있음): {name}")
            continue
        if not e.get("url"):
            print(f"  경고: url 없음 → {name}")
            continue
        digest = sha256(fetch(e["url"]))
        e["sha256"] = digest
        print(f"    => {name}: {digest}")
        changed += 1

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\n완료: {changed}개 항목의 sha256 을 {path} 에 기입했습니다.")
    else:
        print("\n변경 사항 없음.")


def main():
    ap = argparse.ArgumentParser(description="manifest sha256 헬퍼")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="이 URL 의 SHA-256 만 출력")
    g.add_argument("--fill", metavar="MANIFEST", help="manifest 의 모든 entry 해시 채우기")
    ap.add_argument("--force", action="store_true", help="이미 있는 해시도 다시 계산")
    args = ap.parse_args()

    if args.url:
        cmd_url(args.url)
    else:
        cmd_fill(args.fill, args.force)


if __name__ == "__main__":
    main()
