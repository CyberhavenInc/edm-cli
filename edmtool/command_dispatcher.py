import argparse
import logging

from edmtool import utils
from edmtool.client import UploaderClient
from edmtool.command_handler import CommandHandler


class CommandDispatcher:

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Database Client CLI")
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
        self.parser.add_argument("--algorithm",
                                 choices=["spooky", "sha256"],
                                 help="Database algorithm for create and update action.")
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
