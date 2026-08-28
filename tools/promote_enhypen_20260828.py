#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
ARTIST = ROOT / "data" / "artist" / "enhypen.json"
MANIFEST = ROOT / "data" / "manifest.json"
DEV_URL = "https://raw.githubusercontent.com/TsubasA-lu-c/live-ticket-data-dev/684b3fd54ffae2ed1baa789e4c714dafec1c96db/data/artist/enhypen.json"
EXPECTED_PROD_HASH = "e1f49f3634448f16"
EXPECTED_DEV_HASH = "11c03559c3b78907"
EXPECTED_MANIFEST_VERSION = 161


def sha16(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:16]


def validate_enhypen(data: dict) -> None:
    if data.get("artistId") != "enhypen":
        raise SystemExit("unexpected artistId")
    if (len(data.get("tours", [])), len(data.get("performances", [])), len(data.get("lotteries", []))) != (9, 17, 23):
        raise SystemExit("unexpected ENHYPEN counts")

    tours = {x["id"] for x in data["tours"]}
    performances = {x["id"] for x in data["performances"]}
    for p in data["performances"]:
        if p["tourId"] not in tours:
            raise SystemExit(f"dangling performance tourId: {p['id']}")
    for l in data["lotteries"]:
        if l["tourId"] not in tours:
            raise SystemExit(f"dangling lottery tourId: {l['id']}")
        for pid in l.get("performanceIds") or []:
            if pid not in performances:
                raise SystemExit(f"dangling performanceId in {l['id']}: {pid}")

    expected_unknown = {
        "enhypen_the_sin_bliss_meet_greet_2026_kanto_0905": "2026-09-05T12:00:00+09:00",
        "enhypen_the_sin_bliss_heart_touch_2026_kanto_0905": "2026-09-05T12:00:00+09:00",
        "enhypen_the_sin_bliss_2shot_2026_kanto_0905": "2026-09-05T12:00:00+09:00",
        "enhypen_the_sin_bliss_meet_greet_2026_kanto_1010": "2026-10-10T12:00:00+09:00",
        "enhypen_the_sin_bliss_long_sign_2026_kanto_1010": "2026-10-10T12:00:00+09:00",
        "enhypen_the_sin_bliss_premium_sign_2026_makuhari_1010": "2026-10-10T12:00:00+09:00",
    }
    by_id = {x["id"]: x for x in data["performances"]}
    for pid, sentinel in expected_unknown.items():
        p = by_id.get(pid)
        if not p or p.get("performanceAt") != sentinel or p.get("performanceTimeEstimated") is not True:
            raise SystemExit(f"unknown-time compatibility mismatch: {pid}")


def main() -> int:
    current_raw = ARTIST.read_bytes()
    if sha16(current_raw) != EXPECTED_PROD_HASH:
        raise SystemExit(f"production ENHYPEN baseline moved: {sha16(current_raw)}")

    with urllib.request.urlopen(DEV_URL, timeout=30) as response:
        dev_raw = response.read()
    if sha16(dev_raw) != EXPECTED_DEV_HASH:
        raise SystemExit(f"dev ENHYPEN hash mismatch: {sha16(dev_raw)}")
    dev_data = json.loads(dev_raw)
    validate_enhypen(dev_data)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("version") != EXPECTED_MANIFEST_VERSION:
        raise SystemExit(f"production manifest version moved: {manifest.get('version')}")
    if manifest.get("artists", {}).get("enhypen", {}).get("hash") != EXPECTED_PROD_HASH:
        raise SystemExit("production manifest ENHYPEN hash mismatch")

    ARTIST.write_bytes(dev_raw)
    manifest["version"] = EXPECTED_MANIFEST_VERSION + 1
    manifest["updatedAt"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    manifest["artists"]["enhypen"]["hash"] = EXPECTED_DEV_HASH
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("ENHYPEN production promotion OK")
    print(f"artist hash={EXPECTED_DEV_HASH} manifest version={manifest['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
