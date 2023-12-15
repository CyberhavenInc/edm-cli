import unittest
import argparse
from unittest.mock import patch, Mock
from edmtool import utils


class TestUtils(unittest.TestCase):

    def test_get_file_size(self):
        with patch('os.path.exists', return_value=True), patch('os.path.getsize', return_value=100):
            size = utils.Get_file_size('test_path')
            self.assertEqual(size, 100)

    def test_get_file_size_file_not_found(self):
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                utils.Get_file_size('test_path')

    def test_validate_name(self):
        name = "short_name"
        result = utils.Validate_name(name)
        self.assertEqual(result, name)

    def test_validate_name_too_long(self):
        name = "a" * 31
        with self.assertRaises(argparse.ArgumentTypeError):
            utils.Validate_name(name)

    def test_validate_description(self):
        description = "short_description"
        result = utils.Validate_description(description)
        self.assertEqual(result, description)

    def test_validate_description_too_long(self):
        description = "a" * 256
        with self.assertRaises(argparse.ArgumentTypeError):
            utils.Validate_description(description)

    def test_validate_proximity(self):
        proximity = 150
        result = utils.Validate_proximity(proximity)
        self.assertEqual(result, proximity)

    def test_validate_proximity_out_of_range(self):
        proximity = 250
        with self.assertRaises(argparse.ArgumentTypeError):
            utils.Validate_proximity(proximity)

    def test_validate_create_args_all_present(self):
        args = Mock(name="test_name",
                    description="test_description",
                    version="1.0",
                    proximity=150,
                    file_path="test_path",
                    algorithm="test_algo")
        missing_args = utils.Validate_create_args(args)
        self.assertEqual(missing_args, [])

    def test_validate_create_args_missing_some(self):
        args = argparse.Namespace(name=None,
                                  description="test_description",
                                  version="1.0",
                                  proximity=150,
                                  metadata_file_path="test_path",
                                  algorithm="test_algo")
        missing_args = utils.Validate_create_args(args)
        self.assertEqual(missing_args, ["name"])

    def test_print_user_friendly_response_create_success(self):
        action = "create"
        response = {
            "success": True,
            "db_name": "test_db",
            "id": "1234",
            "upload_link": "/upload/1234"
        }
        with self.assertLogs() as cm:
            utils.Print_user_friendly_response(action, response)
            self.assertTrue(
                any("Next step: Upload your file using the following endpoint: /upload/1234 or using the CLI"
                    in log for log in cm.output))

    def test_print_user_friendly_response_create_fail(self):
        action = "create"
        response = {"success": False}
        with self.assertRaises(utils.errors.ServerError):
            utils.Print_user_friendly_response(action, response)

    def test_print_user_friendly_response_upload_success(self):
        action = "upload"
        response = "success"
        with self.assertLogs() as cm:
            utils.Print_user_friendly_response(action, response)
            self.assertTrue(
                any("File successfully uploaded to the database" in log for log in cm.output))

    def test_print_user_friendly_response_upload_fail(self):
        action = "upload"
        response = ""
        with self.assertRaises(utils.errors.ServerError):
            utils.Print_user_friendly_response(action, response)


if __name__ == '__main__':
    unittest.main()
