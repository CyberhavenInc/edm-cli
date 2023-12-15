# EDMTool

`edmtool` is a command-line interface tool in Python designed to interact with Cyberhaven EDM DB API, allowing users to manage and upload hashed EDM database files to operate on them further, building EDM Rules and manage the database definitions.

## Table of Contents

- [Features](#features)
- [Development](#development)
- [Installation](#installation)
- [Usage](#usage)
  - [Hash EDM DB file](#hash-edm-db-file)
  - [Create a New Database Entry and Upload the EDM DB File](#create-a-new-database-entry-and-upload)
  - [Create a New Database Entry](#create-a-new-database-entry)
  - [Upload the EDM DB File](#upload-a-file)
  - [Update an existing Database Entry and Upload the EDM DB File](#update-an-existing-database-entry-and-upload)

## Features

- Hash EDM DB file into a compatible format in order to upload.
- Create a new EDM database entry and upload the EDM DB file directly.
- Upload EDM DB file with progress tracking.

## Development

In order to develop you advisably need to have `Python>=3.7`, `pip` and, preferably, `virtualenv` installed in order to develop in isolation.

If you do have `virtualenv` installed, run

```bash
make venv

# IMPORTANT!
# activate the venv
source .venv/bin/activate
```

To install all dependencies

```bash
make install-dev
```

Also it is possible to run the CLI for testing purposes without building and installing it locally:

```bash
python3 -m edmtool <commands>
```

## Installation

Build the package:

```bash
make build
```

To install after building (from the dist folder), you can use pip:

```bash
pip install ./dist/edmtool-<version>.tar.gz

# OR

make install-local
```

## Usage

### Hash EDM DB file

It takes an input file provided by you and generates 2 new output files.
A `<filename>_encoded.csv` and `<filename>_encoded_metadata.json`, please do not modify in any way or remove those once generated.

```bash
edmtool encode --algorithm "spooky" --db_file_path ./path/to/your/file.csv
```

You can also use optional argument to indicate that your EDM DB CSV file delimiter is distinct from `'|'`

```bash
--db_file_delimiter ';'
```

### Create a new Database Entry and upload

Create an new EDM DB entry and upload the associated file.

```bash
edmtool create_and_upload --name "Your DB Name" --description "Your Description" --file /path/to/your/file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Update an existing Database Entry and upload

Update an existing EDM DB entry and upload the associated file.

```bash
edmtool update_and_upload --id DATABASE_ID --description "Your Description" --file /path/to/your/updated_file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Create a new Database entry

Create the database entry based on a generated EDM DB encoded file.

```bash
edmtool create --name "Your DB Name" --description "Your Description" --file /path/to/your/file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Update an existing Database entry

Update an existing database with a new EDM DB encoded file.

```bash
edmtool update --name "Your DB Name" --description "Your Description" --file /path/to/your/file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Upload a File

Upload the EDM DB encoded file. This applies to both new and existing database entries.

```bash
edmtool upload --id DATABASE_ID --file ./path/to/your/file_encoded_metadata.json --base_url http://api.example.com --token YOUR_AUTH_TOKEN
```
