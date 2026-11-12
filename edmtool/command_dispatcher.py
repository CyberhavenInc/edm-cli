import argparse
import logging

from edmtool import utils
from edmtool.client import UploaderClient
from edmtool.command_handler import CommandHandler


class _Parser(argparse.ArgumentParser):
    """Options in `exact_only` are not prefix-matched, so they never make older abbreviations ambiguous."""
    exact_only = frozenset()

    def _get_option_tuples(self, option_string):
        return [t for t in super()._get_option_tuples(option_string) if t[1] not in self.exact_only]


class CommandDispatcher:

    def __init__(self):
        self.parser = _Parser(description="Database Client CLI")
        self.parser.add_argument("action",
                                 choices=[
                                     "encode", "create", "update", "upload", "create_and_upload",
                                     "update_and_upload"
                                 ],
                                 help="Action to perform")
        self.parser.add_argument("--id", help="Database ID for upload or update actions.")
        self.parser.add_argument("--name",
                                 type=utils.Validate_name,
                                 help="Database name for create action (max 30 chars).")
        self.parser.add_argument("--description",
                                 type=utils.Validate_description,
                                 help="Database description for create action (max 255 chars).")
        self.parser.add_argument(
            "--algorithm",
            "--algo",
            choices=["spooky", "sha256", "hmac-sha256"],
            help="Hashing algorithm for encode. hmac-sha256 is keyed and needs --key-file.")
        self.parser.add_argument(
            "--key-file",
            "--key_file",
            dest="key_file",
            help="hmac-sha256: file with the tenant key in hex (else $EDM_KEY_HEX).")
        self.parser.add_argument("--tokenizer",
                                 choices=["purview", "wb"],
                                 help="hmac-sha256: default column tokenizer (default purview).")
        self.parser.add_argument(
            "--lower",
            choices=["simple", "python"],
            help="hmac-sha256: cell lowercasing (default simple, same as document scanning).")
        self.parser.add_argument(
            "--purview-col",
            "--purview_col",
            dest="purview_col",
            action="append",
            default=[],
            metavar="NAME[:case][:ignored=CHARS]",
            help="hmac-sha256: Purview tokenization for one column (repeatable). 'case' makes it "
            "case sensitive, 'ignored' lists characters removed from its tokens.")
        self.parser.add_argument("--no-shapes",
                                 "--no_shapes",
                                 dest="no_shapes",
                                 action="store_true",
                                 help="hmac-sha256: omit the shape metadata used for scan gating.")
        self.parser.exact_only = frozenset([
            "--algo", "--key-file", "--key_file", "--tokenizer", "--lower", "--purview-col",
            "--purview_col", "--no-shapes", "--no_shapes"
        ])
        self.parser.add_argument("--db_file_path", help="Path to the original file for encoding.")
        self.parser.add_argument(
            "--db_file_delimiter",
            help=
            "If your CSV has a different, custom delimiter, please indicate. Pay attention to the delimiter inside the cells data.",
            default=',')
        self.parser.add_argument("--metadata_file_path", help="Path to the encoded metadata file")
        self.parser.add_argument(
            "--token", help="Cyberhaven API token. Can be obtained in the Dashboard configuration.")
        self.parser.add_argument(
            "--base_url", help="Base URL of the API (should be your cluster deployment URL).")
        self.parser.add_argument(
            "--allow_empty_cells",
            action="store_true",
            default=False,
            help="Allow empty cells in the EDM database. Empty cells will be hashed but will never match during evaluation.")

    def capture(self):
        args = self.parser.parse_args()

        try:
            client = UploaderClient(args.base_url, args.token)
            cd = CommandHandler(client)

            if args.action == "create":
                cd.create(args)
            elif args.action == "update":
                cd.update(args)
            elif args.action == "encode":
                cd.encode(args)
            elif args.action == "create_and_upload":
                cd.create_and_upload(args)
            elif args.action == "update_and_upload":
                cd.update_and_upload(args)
            elif args.action == "upload":
                cd.upload(args)
        except Exception as e:
            logging.error(f"Operation {args.action} errored. {e}")
