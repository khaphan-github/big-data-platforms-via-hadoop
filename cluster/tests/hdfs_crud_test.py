#!/usr/bin/env python3
"""Simple CRUD smoke test for HDFS via WebHDFS using the `hdfs` library."""

import argparse
import posixpath
import sys
from datetime import datetime, timezone
from pathlib import Path

from hdfs import InsecureClient


def build_client(namenode_http: str, user: str) -> InsecureClient:
    # WebHDFS endpoint comes from NameNode HTTP UI service, default 9870.
    return InsecureClient(namenode_http, user=user)


def ensure_dir(client: InsecureClient, hdfs_dir: str) -> None:
    client.makedirs(hdfs_dir)


def resolve_upload_file(upload_file: str) -> Path:
    candidate = Path(upload_file).expanduser()
    if candidate.is_file():
        return candidate

    # Also support running from repo root by resolving relative to this script.
    local_to_script = Path(__file__).resolve().parent / upload_file
    if local_to_script.is_file():
        return local_to_script

    raise FileNotFoundError(f"Upload file not found: {upload_file}")


def run_crud(client: InsecureClient, base_dir: str, upload_file: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = posixpath.join(base_dir, f"run_{ts}")
    ensure_dir(client, run_dir)

    src_path = posixpath.join(run_dir, "sample.txt")
    renamed_path = posixpath.join(run_dir, "sample_renamed.txt")

    upload_path = resolve_upload_file(upload_file)
    payload = upload_path.read_text(encoding="utf-8")

    # Create
    client.write(src_path, data=payload, encoding="utf-8", overwrite=True)

    # Read
    with client.read(src_path, encoding="utf-8") as reader:
        content = reader.read()

    if content != payload:
        raise RuntimeError("Read content mismatch after create/write")

    # Update (append simulation by overwrite with extended payload)
    updated_payload = payload + "status=updated\n"
    client.write(src_path, data=updated_payload, encoding="utf-8", overwrite=True)

    with client.read(src_path, encoding="utf-8") as reader:
        content2 = reader.read()

    if content2 != updated_payload:
        raise RuntimeError("Read content mismatch after update")

    # Rename
    ok = client.rename(src_path, renamed_path)
    # `hdfs` client versions differ: some return True, others return None on success.
    if ok is False:
        raise RuntimeError("Rename returned false")

    # List
    files = client.list(run_dir)
    if "sample_renamed.txt" not in files:
        raise RuntimeError("Renamed file not present in directory listing")

    # Delete file + run dir
    # client.delete(renamed_path)
    # client.delete(run_dir, recursive=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HDFS CRUD smoke test using python hdfs library")
    parser.add_argument(
        "--namenode-http",
        default="http://localhost:9870",
        help="NameNode HTTP endpoint for WebHDFS (default: http://localhost:9870)",
    )
    parser.add_argument(
        "--user",
        default="hadoop",
        help="HDFS user name (default: hadoop)",
    )
    parser.add_argument(
        "--base-dir",
        default="/tmp/python-hdfs-crud",
        help="Base HDFS dir for CRUD test (default: /tmp/python-hdfs-crud)",
    )
    parser.add_argument(
        "--upload-file",
        default="README.md",
        help="Local file to upload to HDFS (default: README.md)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        client = build_client(args.namenode_http, args.user)
        run_crud(client, args.base_dir, args.upload_file)
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    print("[PASS] HDFS CRUD smoke test completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
