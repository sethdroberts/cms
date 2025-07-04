import unittest
from app import app
import shutil
import os

class CMSTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.data_path = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_path, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.data_path, ignore_errors=True)
    
    def create_document(self, name, content=""):
        with open(os.path.join(self.data_path, name), 'w') as file:
            file.write(content)

    def test_index(self):
        self.create_document("about.md")
        self.create_document("changes.txt")
        self.create_document("history.txt")
        
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("about.md", response.get_data(as_text=True))
        self.assertIn("changes.txt", response.get_data(as_text=True))
        self.assertIn("history.txt", response.get_data(as_text=True))

    def test_viewing_text_document(self):
        self.create_document("history.txt", "Python 0.9.0 (initial release) is released.")
        
        response = self.client.get('/history.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/plain; charset=utf-8")
        self.assertIn("Python 0.9.0 (initial release) is released.",
                      response.get_data(as_text=True))
                      
    def test_document_not_found(self):
        # Attempt to access a nonexistent file and verify a redirect happens
        with self.client.get("/notafile.ext") as response:
            self.assertEqual(response.status_code, 302)

        # Verify redirect and message handling works
        with self.client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("notafile.ext does not exist",
                          response.get_data(as_text=True))

        # Assert that a page reload removes the message
        with self.client.get("/") as response:
            self.assertNotIn("notafile.ext does not exist",
                             response.get_data(as_text=True))

    def test_markdown_documents(self):
        self.create_document("about.md", "**open source**")
        
        response = self.client.get('/about.md')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<strong>open source</strong>",
                          response.get_data(as_text=True))
    
    def test_editing_document(self):
        self.create_document("changes.txt")
        response = self.client.get('/changes.txt/edit')
        self.assertIn('<button type="submit">Save Changes</button>', response.get_data(as_text=True))
        self.assertIn('<textarea name="content"', response.get_data(as_text=True))
    
    def test_updating_document(self):
        self.create_document("changes.txt")
        
        response = self.client.post("/changes.txt/edit",
                                    data={'content': "new content"})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("changes.txt has been updated",
                      follow_response.get_data(as_text=True))

        with self.client.get("/changes.txt") as content_response:
            self.assertEqual(content_response.status_code, 200)
            self.assertIn("new content",
                          content_response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()