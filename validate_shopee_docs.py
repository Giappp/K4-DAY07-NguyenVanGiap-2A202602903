#!/usr/bin/env python3

import argparse
import csv
import re
from pathlib import Path


REQ = [
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate Markdown metadata against sources.csv."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing *.md files and sources.csv",
    )
    return parser.parse_args()


def extract_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    parts = text.split("---")
    if len(parts) < 3:
        return {}

    front_matter = parts[1]

    return dict(
        re.findall(
            r"^(\w+):\s*(.+)$",
            front_matter,
            re.M,
        )
    )


def main():
    args = parse_args()
    directory = args.directory

    if not directory.exists():
        print(f"ERROR: Directory không tồn tại: {directory}")
        return 1

    sources_path = directory / "sources.csv"

    if not sources_path.exists():
        print(f"ERROR: Không tìm thấy: {sources_path}")
        return 1

    mds = sorted(directory.glob("*.md"))

    with sources_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    ids = []
    audiences = {}

    print("=== Markdown metadata ===")

    for path in mds:
        fm = extract_front_matter(path)

        doc_id = fm.get("doc_id")
        ids.append(doc_id)

        audience = fm.get("audience")
        audiences[audience] = audiences.get(audience, 0) + 1

        ok = (
            all(key in fm for key in REQ)
            and fm.get("doc_id") == path.stem
        )

        status = "OK" if ok else "THIEU METADATA"

        if not ok:
            print(f"\n[{path.name}]")
            print("Parsed metadata:", fm)
            missing = [key for key in REQ if key not in fm]
            if missing:
                print("Missing:", missing)
            if fm.get("doc_id") != path.stem:
                print(
                f"doc_id sai: '{fm.get('doc_id')}' "
                f"!= filename '{path.stem}'")


        print(f"{path.name:40} {status}")

    csv_ids = sorted(row.get("doc_id", "") for row in rows)
    md_ids = sorted(ids)

    print()
    print("so file :", len(mds), "(can 5-10)")
    print(
        "csv     :",
        "khop" if csv_ids == md_ids else "LECH",
    )
    print("audience:", audiences)

    # Exit code khác 0 nếu validation thất bại.
    all_valid = (
        len(mds) >= 5
        and len(mds) <= 10
        and csv_ids == md_ids
        and all(
            all(key in extract_front_matter(path) for key in REQ)
            and extract_front_matter(path).get("doc_id") == path.stem
            for path in mds
        )
    )

    if all_valid:
        print("\nVALIDATION: PASS")
        return 0

    print("\nVALIDATION: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
