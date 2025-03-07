"""Download URLs specified in a CSV, taking output names from the CSV also."""

import argparse
import collections
import csv
import logging
import os
import re
import time
from typing import Mapping
import urllib

import requests


def read_csv(path: str) -> list[Mapping[str, str]]:
    with open(path, "rt") as f:
        return list(csv.DictReader(f))


def get_extension_from_url(url: str) -> str:
    """Returns the file extension from the URL if present, empty string otherwise.

    Args:
      url: URL from which to extract the extension.
    Returns: the extension, *including* leading dot or empty string.
    """
    parsed = urllib.parse.urlparse(url)
    return os.path.splitext(parsed.path)[1].lower()


class CsvColumnDownloader:

    def __init__(
        self,
        rows: list[dict],
        url_column: str,
        name_column: str,
        output_dir: str,
        max_downloads: int = -1,
    ):
        assert rows
        assert url_column in rows[0]
        assert name_column in rows[0]
        self.output_dir = output_dir
        self.num_failed = 0
        self.failed = set()
        self.num_succeeded = 0
        self.already_downloaded = 0
        self.download_seconds = 0.0
        # Note: this is guaranteed to be a stable sort.
        # See https://wiki.python.org/moin/HowTo/Sorting/#Sort_Stability_and_Complex_Sorts.
        self.rows = sorted(rows, key=lambda d: d[name_column])
        self.name_counts = collections.Counter()

        # In the first pass over the over rows, we add the proposed output filename (within
        # output_dir). We do this as a separate pass vs the main loop where we do the
        # actual downloading since we want to provide the proposed name regardless of
        # whether we actually attempt the download.
        for row in self.rows:
            base_name = self.make_unique_base_name(row[name_column])
            url = row[url_column]
            extension = get_extension_from_url(url)
            filename = base_name + extension
            row["output_filename"] = filename
        # Note: we can consider making this multithreaded; however, initiating too many requests
        # in parallel may be a good way to end up getting blocked by the server on the other
        # side.
        num_attempts = 0
        start_seconds = time.time()
        for row in self.rows:
            output_path = os.path.join(output_dir, row["output_filename"])
            if os.path.exists(output_path):
                self.already_downloaded += 1
            url = row[url_column]
            if max_downloads >= 0 and num_attempts >= max_downloads:
                break
            num_attempts += 1
            try:
                r = requests.get(url)
                with open(output_path, "wb") as f:
                    f.write(r.content)
            except requests.exceptions.RequestException as e:
                self.num_failed += 1
                self.failed.add(url)
                logging.error("Download failed for %s: %s", url, e)
                continue
            self.num_succeeded += 1
        self.download_seconds = time.time() - start_seconds
        with open(os.path.join(output_dir, "output.csv"), "wt") as f:
            w = csv.DictWriter(f, fieldnames=list(self.rows[0].keys()))
            w.writeheader()
            w.writerows(self.rows)

    def make_unique_base_name(self, name: str) -> str:
        name = re.sub(r"[^a-z0-9]+", "_", name.lower())
        self.name_counts[name] += 1
        return f"{name}_{self.name_counts[name]:03}"

    def print_summary(self):
        print(f"Downloads took {self.download_seconds / 60:0.2f} minutes")
        print(f"Num successfully downloaded: {self.num_succeeded}")
        print(f"Num failed: {self.num_failed}")
        print(f"Num already downloaded: {self.already_downloaded}")
        if self.failed:
            print(f'Failed downloads include: {", ".join(sorted(self.failed)[:100])}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="csv_column_download",
        description="Download from the URLs specified in a CSV column",
    )
    parser.add_argument(
        "--input", help="Path to the CSV file to be used", required=True
    )
    parser.add_argument(
        "--url_column",
        help="Name of the column containing URLs to download",
        required=True,
    )
    parser.add_argument(
        "--name_column",
        help="Column that will be used to name the downloaded files",
        required=True,
    )
    parser.add_argument(
        "--output_dir",
        help="Directory into which to store output. Will be created if needed.",
        required=True,
    )
    parser.add_argument(
        "--max_downloads",
        default=-1,
        type=int,
        help="If set, the maximum number of downloads to attempt. Useful for testing.",
    )
    args = parser.parse_args()
    downloader = CsvColumnDownloader(
        rows=read_csv(args.input),
        url_column=args.url_column,
        name_column=args.name_column,
        output_dir=args.output_dir,
        max_downloads=args.max_downloads,
    )
    downloader.print_summary()
