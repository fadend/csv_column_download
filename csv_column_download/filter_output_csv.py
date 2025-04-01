"""This utility filters the output of csv_column_download.

In case the downloaded files are large, it can be more convenient to work
with the local copy instead of doing a fresh run in case we discover
some files should have been excluded.

Usage:
bin/python -m csv_column_download.filter_output_csv \
    --original_output_dir=images --excluded_output_dir=excluded \
        --max_count_per_base_name=3 --filter_column=scientific_name \
            --excluded_values_file=bad_species.txt
"""

import argparse
import csv
import logging
import os
import shutil
from typing import Mapping


def write_csv(path: str, rows: list[Mapping[str, str]], fieldnames: list[str]):
    assert path
    assert fieldnames
    with open(path, "wt", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_lines(path: str):
    assert path
    with open(path, "rt", encoding="utf8") as f:
        return [line.rstrip() for line in f]


class FilterOutputCsv:
    def __init__(
        self,
        original_output_dir: str,
        excluded_output_dir: str,
        filter_column_values: Mapping[str, set[str]] = dict(),
        max_count_per_base_name: int = -1,
    ):
        assert original_output_dir
        assert excluded_output_dir
        original_output_csv = os.path.join(original_output_dir, "output.csv")
        assert os.path.exists(original_output_csv), f"Missing {original_output_csv}"
        self.num_kept = 0
        self.num_dropped = 0
        self.num_dropped_for_count_too_high = 0
        self.num_dropped_for_excluded_value = 0
        self.num_to_move_missing = 0
        included_rows = []
        excluded_rows = []
        excluded_files = set()
        with open(original_output_csv, "rt", encoding="utf8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                keep = True
                output_filename = row["output_filename"]
                if max_count_per_base_name >= 0:
                    base_name = os.path.splitext(output_filename)[0]
                    num = int(base_name.rsplit("_", maxsplit=1)[1])
                    if num > max_count_per_base_name:
                        self.num_dropped_for_count_too_high += 1
                        keep = False
                if keep:
                    for column, excluded_values in filter_column_values.items():
                        if row[column] in excluded_values:
                            self.num_dropped_for_excluded_value += 1
                            keep = False
                            break
                if keep:
                    included_rows.append(row)
                else:
                    excluded_rows.append(row)
                    excluded_files.add(output_filename)
        self.num_kept = len(included_rows)
        self.num_dropped = len(excluded_rows)
        something = included_rows or excluded_rows
        if not something:
            logging.info("Empty input in %s, nothing to do", original_output_csv)
            return
        fieldnames = list(something[0].keys())
        included_csv = os.path.join(original_output_dir, "output-included.csv")
        write_csv(included_csv, rows=included_rows, fieldnames=fieldnames)
        os.makedirs(excluded_output_dir, exist_ok=True)
        excluded_csv = os.path.join(excluded_output_dir, "output-excluded.csv")
        write_csv(excluded_csv, rows=excluded_rows, fieldnames=fieldnames)
        for excluded_file in sorted(excluded_files):
            old_path = os.path.join(original_output_dir, excluded_file)
            if not os.path.exists(old_path):
                logging.info("Didn't find file to move: %s", old_path)
                self.num_to_move_missing += 1
                continue
            new_path = os.path.join(excluded_output_dir, excluded_file)
            logging.info("Moving %s to %s", excluded_file, new_path)
            shutil.move(old_path, new_path)

    def print_summary(self):
        print(f"Num rows kept: {self.num_kept}")
        print(f"Num rows dropped: {self.num_dropped}")
        print(f"Num with count too high: {self.num_dropped_for_count_too_high}")
        print(f"Num with excluded value: {self.num_dropped_for_excluded_value}")
        print(f"Num to-move missing: {self.num_to_move_missing}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="filter_output_csv",
        description="Filter output.csv from csv_column_download",
    )
    parser.add_argument(
        "--original_output_dir",
        help="Path at which output was originally written. Expected to include output.csv",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--excluded_output_dir",
        help="Directory under which to move filtered files.",
        default="excluded",
        type=str,
    )
    parser.add_argument(
        "--filter_column",
        help="Column to look at when deciding what to filter."
        " If set, requires that --excluded_values_file also be set.",
        default="",
        type=str,
    )
    parser.add_argument(
        "--excluded_values_file",
        help="Line-separated file of values to exclude, looking at --filter_column.",
        default="",
        type=str,
    )
    parser.add_argument(
        "--max_count_per_base_name",
        help="Max per input item count. Items with index greater than this will be excluded."
        " E.g., with --max_count_per_base_name=10, an item with output_filename pizza_011.jpeg would be excluded.",
        default=-1,
        type=int,
    )
    args = parser.parse_args()
    filter_column_values = dict()
    if args.filter_column:
        assert (
            args.excluded_values_file
        ), "--excluded_values_file is required for --filter_column"
        filter_column_values[args.filter_column] = read_lines(args.excluded_values_file)
    filter = FilterOutputCsv(
        original_output_dir=args.original_output_dir,
        excluded_output_dir=args.excluded_output_dir,
        filter_column_values=filter_column_values,
        max_count_per_base_name=args.max_count_per_base_name,
    )
    filter.print_summary()
