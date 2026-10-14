"""Clean a CSV using explicit rules and record every change.

Python 3.10+, standard library only. Original files are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path


def clean_csv(text: str, *, trim: list[str], lowercase: list[str], key: list[str]):
    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = reader.fieldnames
    if not headers or any(not column for column in headers):
        raise ValueError("CSV must have a nonempty header for every column")
    if len(headers) != len(set(headers)):
        raise ValueError("Duplicate column names make the CSV ambiguous")
    unknown = set(trim + lowercase + key) - set(headers)
    if unknown:
        raise ValueError("Unknown columns: " + ", ".join(sorted(unknown)))

    rows, changes, duplicates, conflicts, missing_keys = [], [], [], [], []
    seen = {}
    input_count = 0
    for source_row, source in enumerate(reader, start=2):
        input_count += 1
        if None in source or any(value is None for value in source.values()):
            raise ValueError(f"Row {source_row} has a different number of fields")
        row = dict(source)
        for column in headers:
            original = row[column]
            result = original.strip() if column in trim else original
            if column in lowercase:
                result = result.lower()
            if result != original:
                changes.append({"source_row": source_row, "column": column,
                                "before": original, "after": result})
                row[column] = result
        if key:
            row_key = tuple(row[column] for column in key)
            if any(value == "" for value in row_key):
                missing_keys.append(source_row)
            elif row_key in seen:
                matches = [(previous, previous_row) for previous, previous_row in seen[row_key]
                           if row == previous]
                if matches:
                    duplicates.append({"source_row": source_row,
                                       "kept_source_row": matches[0][1]})
                    continue
                conflicts.append({"source_row": source_row,
                                  "first_source_row": seen[row_key][0][1],
                                  "key": list(row_key)})
                seen[row_key].append((row, source_row))
            else:
                seen[row_key] = [(row, source_row)]
        rows.append(row)

    result = io.StringIO(newline="")
    writer = csv.DictWriter(result, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    report = {
        "input_rows": input_count, "output_rows": len(rows),
        "changed_cells": len(changes), "removed_duplicate_rows": len(duplicates),
        "conflicting_keys_retained": conflicts,
        "missing_key_rows_retained": missing_keys,
        "rules": {"trim": trim, "lowercase": lowercase, "key": key},
        "changes": changes, "duplicates": duplicates,
    }
    return result.getvalue(), report


def columns(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--trim", type=columns, default=[])
    parser.add_argument("--lowercase", type=columns, default=[])
    parser.add_argument("--key", type=columns, default=[])
    args = parser.parse_args()
    destinations = [args.output.resolve(), args.report.resolve()]
    if args.source.resolve() in destinations or len(set(destinations)) != 2:
        parser.error("Input, output and report must be different files")
    if any(path.exists() for path in destinations):
        parser.error("Output or report already exists; choose new filenames")
    try:
        output, report = clean_csv(args.source.read_text(encoding="utf-8-sig"),
                                  trim=args.trim, lowercase=args.lowercase, key=args.key)
    except (ValueError, OSError, UnicodeError, csv.Error) as error:
        parser.exit(2, f"Error: {error}\n")
    # Both files are prepared before writing. Exclusive creation prevents accidental overwrites.
    with args.output.open("x", encoding="utf-8", newline="") as stream:
        stream.write(output)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"{report['input_rows']} input rows -> {report['output_rows']} output rows; "
          f"{report['changed_cells']} changed cells; "
          f"{report['removed_duplicate_rows']} identical duplicates removed; "
          f"{len(report['conflicting_keys_retained'])} conflicting keys retained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
