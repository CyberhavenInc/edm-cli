import argparse
import logging

from edmtool import errors
from edmtool import utils
from edmtool.client import UploaderClient
from edmtool.file_transformer import FileTransformer
from edmtool.hasher import Hasher
from edmtool import keyed


class CommandHandler:
    _KEYED_ARGS = ('key_file', 'tokenizer', 'lower', 'purview_col', 'no_shapes')

    @staticmethod
    def _read_uploadable_metadata(path):
        metadata = utils.Read_metadata_file(path)
        # The backend does not know the edm format yet and would store it as SHA256.
        if metadata.get('algo') == keyed.ALGO:
            raise errors.UnsupportedAlgorithmError(
                f"{keyed.ALGO} databases cannot be uploaded yet; use spooky or sha256.")
        return metadata

    def __init__(self, client: UploaderClient):
        self.client = client

    def encode(self, args):
        missing_args = utils.Validate_encode_args(args)
        if missing_args:
            raise errors.MissingArgumentsError(
                f"The following arguments are required for the 'encode' action: {', '.join(missing_args)}"
            )

        allow_empty_cells = getattr(args, 'allow_empty_cells', False)
        keyed_args = {a: getattr(args, a, None) for a in self._KEYED_ARGS}
        if args.algorithm == keyed.ALGO:
            kw = {k: keyed_args[k] for k in ('tokenizer', 'lower') if keyed_args[k]}
            opts = keyed.KeyedOptions(keyed.load_key(keyed_args['key_file']),
                                      purview_cols=keyed_args['purview_col'] or (),
                                      shapes=not keyed_args['no_shapes'],
                                      delimiter=args.db_file_delimiter,
                                      allow_empty_cells=allow_empty_cells,
                                      **kw)
            ft = keyed.KeyedFileTransformer(opts)
        else:
            given = ', '.join('--' + a.replace('_', '-') for a, v in keyed_args.items() if v)
            if given:
                raise errors.MissingArgumentsError(f"{given} need --algorithm {keyed.ALGO}")
            ft = FileTransformer(Hasher(args.algorithm),
                                 args.db_file_delimiter,
                                 allow_empty_cells=allow_empty_cells)
        logging.info(
            f"Encoding file under path {args.db_file_path}... The delimiter is \"{args.db_file_delimiter}\"."
        )
        hash, size = ft.create_encoded_file(args.db_file_path)

        done_phrase = f"File under path {args.db_file_path} has been successfully hashed.\nChecksum is {hash} and output size is {size}."
        logging.info(done_phrase)

    def create(self, args):
        missing_args = utils.Validate_create_args(args)
        if missing_args:
            raise errors.MissingArgumentsError(
                f"The following arguments are required for the 'create' action: {', '.join(missing_args)}"
            )

        metadata = self._read_uploadable_metadata(args.metadata_file_path)

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

        metadata = self._read_uploadable_metadata(args.metadata_file_path)
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

        metadata = self._read_uploadable_metadata(args.metadata_file_path)
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

        return self.upload(
            argparse.Namespace(id=create_response.get("id"),
                               metadata_file_path=args.metadata_file_path,
                               action="upload"))

    def update_and_upload(self, args):
        update_response = self.update(args)

        if not update_response or not update_response.get("success"):
            raise errors.ProcessInterruptedError(
                "Can't follow with the upload as the database updating was not successful.")

        return self.upload(
            argparse.Namespace(id=update_response.get("id"),
                               metadata_file_path=args.metadata_file_path,
                               action="upload"))
