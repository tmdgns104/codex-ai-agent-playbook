from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "snapshots" / "manifest.json"
ALLOWED = {
    ("K-Dense-AI/scientific-agent-skills", "390f5146bf3c1877cf15636a3dd7b775e4f0f185"),
    ("NVIDIA/skills", "7149a886d50da8db72cdc1f20ff01cefeadfe6a9"),
}


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def build_url(record: dict) -> str:
    repo = record["repository"]
    revision = record["source_revision"]
    upstream = record["upstream_path"].strip("/")
    if (repo, revision) not in ALLOWED:
        raise ValueError(f"unapproved repository/revision: {repo}@{revision}")
    if not upstream or ".." in upstream.split("/"):
        raise ValueError(f"unsafe upstream path: {upstream}")
    owner, name = repo.split("/", 1)
    path = quote(upstream + "/SKILL.md", safe="/")
    return f"https://raw.githubusercontent.com/{owner}/{name}/{revision}/{path}"


def fetch_raw(url: str, timeout: float) -> bytes:
    req = Request(url, headers={"User-Agent": "codex-playbook-bench-003b/1"}, method="GET")
    with urlopen(req, timeout=timeout) as response:
        final = urlparse(response.geturl())
        if final.scheme != "https" or final.hostname != "raw.githubusercontent.com":
            raise RuntimeError(f"unexpected fetch destination: {response.geturl()}")
        return response.read()


def save_manifest(data: dict) -> None:
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\r\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch exact pinned SKILL.md snapshots for BENCH-003B")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--candidate")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    data = load_manifest()
    records = data["records"]
    if args.candidate:
        records = [r for r in records if r["candidate_id"] == args.candidate]
        if len(records) != 1:
            raise SystemExit(f"candidate not found or duplicated: {args.candidate}")

    for record in records:
        cid = record["candidate_id"]
        url = build_url(record)
        if args.dry_run:
            print(f"DRY_RUN {cid} {url}")
            continue

        raw = fetch_raw(url, args.timeout)
        if not raw:
            raise RuntimeError(f"empty snapshot: {cid}")
        digest = hashlib.sha256(raw).hexdigest()
        target = ROOT.parent.parent / record["snapshot_path"]
        if target.exists():
            existing = target.read_bytes()
            if existing != raw:
                raise RuntimeError(f"existing snapshot differs: {cid}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        record["sha256"] = digest
        record["byte_size"] = len(raw)
        record["fetch_status"] = "FETCHED"
        record["content_encoding"] = "utf-8" if _is_utf8(raw) else None
        record["notes"] = "Exact pinned upstream SKILL.md fetched read-only; raw bytes preserved."
        print(f"FETCHED {cid} bytes={len(raw)} sha256={digest}")

    if not args.dry_run:
        save_manifest(data)
    return 0


def _is_utf8(raw: bytes) -> bool:
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
