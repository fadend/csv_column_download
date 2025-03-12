# csv_column_download

Utility to download URLs as given in a CSV file.

Also takes the output name from a column in the CSV.

## Usage

```
# Create a virtual env to keep things clean
python -m venv downloadenv

# Move into the directory with the venv
cd downloadenv

# Install from Github
bin/pip3 install git+https://github.com/fadend/csv_column_download

# Run
bin/python -m csv_column_download.csv_column_download \
  --input $HOME/Downloads/bees.csv \
  --url_column image_url \
  --name_column scientific_name \
  --output_dir images \
  --max_downloads 23
```