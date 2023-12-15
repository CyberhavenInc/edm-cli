import argparse
import logging

from edmtool import errors
from edmtool import utils
from edmtool.client import UploaderClient
from edmtool.file_transformer import FileTransformer
from edmtool.hasher import Hasher


class CommandHandler:

    def __init__(self, client: UploaderClient):
        self.client = client

    def encode(self, args):
        missing_args = utils.Validate_encode_args(args)
        if missing_args:
            raise errors.MissingArgumentsError(
                f"The following arguments are required for the 'encode' action: {', '.join(missing_args)}"
            )

        h = Hasher(args.algorithm)
        ft = FileTransformer(h, args.db_file_delimiter)
        hash, size = ft.create_encoded_file(args.db_file_path)

        done_phrase = f"File under path {args.db_file_path} has been successfully hashed.\nChecksum is {hash} and output size is {size}."
        logging.info(done_phrase)

    def create(self, args):
        missing_args = utils.Validate_create_args(args)
        if missing_args:
            raise errors.MissingArgumentsError(
                f"The following arguments are required for the 'create' action: {', '.join(missing_args)}"
            )

        metadata = utils.Read_metadata_file(args.metadata_file_path)

        response = self.client.create_database(name=args.name,
                                               description=args.description,
                                               rows=metadata["rows"],
                                               size=metadata["size"],
                                               fields=metadata["fields"],
                                               algorithm=metadata["algo"],
                                               checksum=metadata["checksum"])

        utils.Print_user_friendly_response(args.action, response)

        return response

    def update(self, args):
        missing_args = utils.Validate_update_args(args)
        if missing_args:
            raise errors.MissingArgumentsError(
                f"The following arguments are required for the 'update' action: {', '.join(missing_args)}"
            )

        metadata = utils.Read_metadata_file(args.metadata_file_path)
        response = self.client.update_database(id=args.id,
                                               rows=metadata["rows"],
                                               size=metadata["size"],
                                               fields=metadata["fields"],
                                               algorithm=metadata["algo"],
                                               checksum=metadata["checksum"])

        utils.Print_user_friendly_response(args.action, response)

        return response

    def upload(self, args):
        if not args.metadata_file_path or not args.id:
            raise errors.MissingArgumentsError(
                "Please provide both --metadata_file_path and --id for the upload action.")

        metadata = utils.Read_metadata_file(args.metadata_file_path)
        encoded_file_path = utils.Get_file_path_from_metadata(metadata['filename'],
                                                              args.metadata_file_path)

        encoded_file_size = utils.Get_file_size(encoded_file_path)
        file_checksum = utils.Calculate_file_sha256_checksum(encoded_file_path)

        if encoded_file_size != metadata["size"] or file_checksum != metadata["checksum"]:
            raise errors.DifferentFileSizeError(
                f"File contents are modified in relation to the metadata at {args.metadata_file_path}.\nAborting..."
            )

        response = self.client.upload(args.id, encoded_file_path, metadata)

        utils.Print_user_friendly_response(args.action, response)

        return response

    def create_and_upload(self, args):
        create_response = self.create(args)

        if not create_response or not create_response.get("success"):
            raise errors.ProcessInterruptedError(
                "Can't follow with the upload as the database creation was not successful.")

        upload_response = self.upload(
            argparse.Namespace(id=create_response.get("id"),
                               metadata_file_path=args.metadata_file_path,
                               action="upload"))
        utils.Print_user_friendly_response("upload", upload_response)

    def update_and_upload(self, args):
        update_response = self.update(args)

        if not update_response or not update_response.get("success"):
            raise errors.ProcessInterruptedError(
                "Can't follow with the upload as the database updating was not successful.")

        upload_response = self.upload(
            argparse.Namespace(id=update_response.get("id"),
                               metadata_file_path=args.metadata_file_path,
                               action="upload"))
        utils.Print_user_friendly_response("upload", upload_response)
