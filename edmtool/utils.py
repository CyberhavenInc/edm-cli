import argparse
import logging
import os
import hashlib
import json

from edmtool import errors

logging.basicConfig(format='%(levelname)s: %(message)s')


def Count_file_lines(filename: str):
    line_count = 0
    with open(filename, "r") as f:
        line_count = sum(1 for _ in f)
    return line_count


def Get_file_path_from_metadata(filename: str, metadata_path: str):
    directory, _ = os.path.split(metadata_path)
    return os.path.join(directory, filename)


def Read_metadata_file(metadata_path: str):
    with open(metadata_path, 'r') as f:
        return json.load(f)


def Calculate_file_sha256_checksum(file_path: str):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def Get_file_size(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    return os.path.getsize(file_path)


def Validate_name(name):
    if len(name) > 30:
        raise argparse.ArgumentTypeError("Name length should be up to 30 characters.")
    return name


def Validate_description(description):
    if len(description) > 255:
        raise argparse.ArgumentTypeError("Description length should be up to 255 characters.")
    return description


def Validate_proximity(proximity):
    if not 100 <= proximity <= 200:
        raise argparse.ArgumentTypeError("Proximity should be between 100 and 200 (inclusive).")
    return proximity


def Validate_encode_args(args):
    missing_args = []

    if not args.algorithm:
        missing_args.append("algorithm")
    if not args.db_file_path:
        missing_args.append("db_file_path")

    return missing_args


def Validate_update_args(args):
    missing_args = []

    if not args.id:
        missing_args.append("id")
    if not args.metadata_file_path:
        missing_args.append("metadata_file_path")

    return missing_args


def Validate_create_args(args):
    missing_args = []

    if not args.name:
        missing_args.append("name")
    if not args.description:
        missing_args.append("description")
    if not args.metadata_file_path:
        missing_args.append("metadata_file_path")

    return missing_args


def Print_user_friendly_response(action, response):
    if action == "upload":
        if response:
            logging.info(f"File successfully uploaded to the database")
        else:
            raise errors.ServerError(
                "Failed to upload the file. If the status is 413 or 404 you have an outdated version of your tenant, please contact CX, otherwise, please check the provided parameters and try again.")

    if not response:
        raise errors.MissingArgumentsError(
            f"Operation '{action}' failed. Please check the provided parameters and try again.")

    if action == "create":
        if response.get("success"):
            logging.info(
                f"Database '{response['db_name']}' successfully created with ID: {response['id']}")
            logging.info(
                f"Next step: Upload your file using the following endpoint: {response['upload_link']} or using the CLI"
            )
        else:
            raise errors.ServerError(
                f"Failed to create the database. Please check the provided parameters and try again."
            )

    elif action == "update":
        if response.get("success"):
            logging.info(
                f"Database '{response['db_name']}' successfully updated with ID: {response['id']}")
            logging.info(
                f"Next step is going to be performed - Uploading of your file using the following endpoint: {response['upload_link']}"
            )
        else:
            raise errors.ServerError(
                f"Failed to update the database. Please check the provided parameters and try again."
            )

    elif action == "create_and_upload":
        if response:
            logging.info(f"Database successfully created and starting upload process.")
        else:
            raise errors.ServerError(
                f"Failed to create the database. Please check the provided parameters and try again.")
