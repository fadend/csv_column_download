# csv_column_download

Utility to download URLs as given in a CSV file.

Also takes the output name from a column in the CSV.

## Usage

### Install and prepare to run

The following steps create a new [Python virtual environment](https://docs.python.org/3/library/venv.html)
with the utility. You can delete the new directory once you're done.

```
# Create a virtual env to keep things clean
python -m venv downloadenv

# Move into the directory with the venv
cd downloadenv

# Install from Github
bin/pip3 install git+https://github.com/fadend/csv_column_download
```

### Run

```
bin/python -m csv_column_download.csv_column_download \
  --input $HOME/Downloads/bees.csv \
  --url_column image_url \
  --name_column scientific_name \
  --output_dir images
```

- `--input` points to a CSV file providing the URLs to download.
- `--url_column` names the column with the URLs.
- `--name_column` names the column to use for the base names for output files.
- `--output_dir` says where to put the downloaded files. It will be created if it doesn't
  exist already.

You can also use:
- `--max_downloads` to limit the total number of files downloaded if you're testing things out.

## filter_output_csv

This package also includes the `filter_output_csv` command, which filters the output from
`csv_column_download`.

To get started, you can follow intall instructions above.

Here's example usage of `filter_output_csv`:

```
bin/python -m csv_column_download.filter_output_csv \
  --original_output_dir=images \
  --excluded_output_dir=excluded \
  --max_count_per_base_name=3 \
  --filter_column=scientific_name \
  --excluded_values_file=bad_species.txt
```

- `--original_output_dir` should match the output directory from an earlier `csv_column_download` run.
- `--excluded_output_dir` says where to put downloaded files that are being excluded.
- `--max_count_per_base_name` if set will the max allowed count/number. E.g., with `--max_count_per_base_name=3`,
  downloaded file `"pizza_004.jpeg"` would be excluded while `"pizza_003.jpeg"` be kept.
- `--filter_column` if set names a column to examine for excluded values, provided by the
  file pointed to with `--excluded_values_file`.
- `--excluded_values_file`, used in conjunction with `--filter_column`, points to a line-separated file
  of values to exclude.