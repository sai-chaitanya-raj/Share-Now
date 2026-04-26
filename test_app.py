"""
NowShare — Test Suite
Run: python test_app.py
"""
import os
import sys
import unittest
from io import BytesIO

# Set test env vars before importing app
os.environ['MONGO_URI'] = ''  # Disable MongoDB for tests
os.environ['FLASK_DEBUG'] = 'false'
os.environ['FILE_EXPIRY_MINUTES'] = '10'

from app import app


class NowShareTestCase(unittest.TestCase):
    """Test all NowShare endpoints."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    # ----- Upload Tests -----

    def test_upload_success(self):
        """Upload a valid file and get a 6-digit code + QR."""
        data = {'file': (BytesIO(b'Hello World'), 'test.txt')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('code', json_data)
        self.assertIn('qr_code_url', json_data)
        self.assertEqual(len(json_data['code']), 6)
        self.assertTrue(json_data['code'].isdigit())
        self.assertTrue(json_data['qr_code_url'].startswith('data:image/png;base64,'))

    def test_upload_no_file(self):
        """Upload with no file should return 400."""
        response = self.client.post('/upload', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)

    def test_upload_empty_filename(self):
        """Upload with empty filename should return 400."""
        data = {'file': (BytesIO(b''), '')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)

    # ----- Download Tests -----

    def test_download_success(self):
        """Upload a file, then download it using the code."""
        # Upload first
        data = {'file': (BytesIO(b'Secret data'), 'secret.txt')}
        upload_resp = self.client.post('/upload', data=data, content_type='multipart/form-data')
        code = upload_resp.get_json()['code']

        # Download
        download_resp = self.client.get(f'/download/{code}')
        self.assertEqual(download_resp.status_code, 200)
        self.assertEqual(download_resp.data, b'Secret data')

    def test_download_invalid_code(self):
        """Download with invalid code should return 404."""
        response = self.client.get('/download/000000')
        self.assertEqual(response.status_code, 404)

    def test_download_preserves_filename(self):
        """Downloaded file should have the original filename."""
        data = {'file': (BytesIO(b'Content'), 'myfile.pdf')}
        upload_resp = self.client.post('/upload', data=data, content_type='multipart/form-data')
        code = upload_resp.get_json()['code']

        download_resp = self.client.get(f'/download/{code}')
        content_disp = download_resp.headers.get('Content-Disposition', '')
        self.assertIn('myfile.pdf', content_disp)

    # ----- History Tests -----

    def test_history_endpoint(self):
        """History endpoint should return a list."""
        response = self.client.get('/get_history')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_history_updates_after_upload(self):
        """History should contain entry after upload."""
        data = {'file': (BytesIO(b'Data'), 'file.txt')}
        self.client.post('/upload', data=data, content_type='multipart/form-data')

        response = self.client.get('/get_history')
        history = response.get_json()
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[-1]['filename'], 'file.txt')

    # ----- Contact Form Tests -----

    def test_contact_form_no_mongo(self):
        """Contact form should return 503 when MongoDB is not connected."""
        response = self.client.post('/submit_contact', json={
            'name': 'Test User',
            'phone': '1234567890',
            'email': 'test@example.com',
            'message': 'Hello'
        })
        self.assertEqual(response.status_code, 503)

    def test_contact_form_missing_fields(self):
        """Contact form with missing fields should return 400 or 503."""
        response = self.client.post('/submit_contact', json={
            'name': 'Test User',
            'email': 'test@example.com'
        })
        self.assertIn(response.status_code, [400, 503])

    # ----- Edge Cases -----

    def test_homepage_loads(self):
        """Homepage should return 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_homepage_with_code_param(self):
        """Homepage with ?code= param should still load (JS handles auto-fill)."""
        response = self.client.get('/?code=123456')
        self.assertEqual(response.status_code, 200)

    def test_404_handler(self):
        """Non-existent route should return 404 JSON."""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_large_code(self):
        """Extremely long code should return 404, not crash."""
        response = self.client.get('/download/' + 'A' * 1000)
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    print("=" * 60)
    print("  NowShare Test Suite")
    print("=" * 60)
    unittest.main(verbosity=2)
