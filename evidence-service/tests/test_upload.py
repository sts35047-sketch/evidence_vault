import unittest
from src.services.storage import upload_file, download_file
from unittest.mock import patch, MagicMock

class TestFileUpload(unittest.TestCase):

    @patch('src.services.storage.some_storage_service')
    def test_upload_file_success(self, mock_storage_service):
        mock_storage_service.upload.return_value = True
        result = upload_file('test_file.txt', 'some_destination')
        self.assertTrue(result)
        mock_storage_service.upload.assert_called_once_with('test_file.txt', 'some_destination')

    @patch('src.services.storage.some_storage_service')
    def test_upload_file_failure(self, mock_storage_service):
        mock_storage_service.upload.side_effect = Exception("Upload failed")
        with self.assertRaises(Exception) as context:
            upload_file('test_file.txt', 'some_destination')
        self.assertEqual(str(context.exception), "Upload failed")

    @patch('src.services.storage.some_storage_service')
    def test_download_file_success(self, mock_storage_service):
        mock_storage_service.download.return_value = b'file_content'
        result = download_file('some_source')
        self.assertEqual(result, b'file_content')
        mock_storage_service.download.assert_called_once_with('some_source')

    @patch('src.services.storage.some_storage_service')
    def test_download_file_failure(self, mock_storage_service):
        mock_storage_service.download.side_effect = Exception("Download failed")
        with self.assertRaises(Exception) as context:
            download_file('some_source')
        self.assertEqual(str(context.exception), "Download failed")

if __name__ == '__main__':
    unittest.main()