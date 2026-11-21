from contextlib import closing
import os
from pathlib import Path
import sys
import tempfile
import unittest


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
TEMP_DIR = tempfile.TemporaryDirectory()
os.environ["LIBRARY_DB_PATH"] = str(Path(TEMP_DIR.name) / "test-library.db")

from app import app, get_db_connection


class LibraryManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")

    def setUp(self):
        with closing(get_db_connection()) as conn:
            conn.execute("BEGIN")
            conn.execute("DELETE FROM loans")
            conn.execute("DELETE FROM books")
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('loans', 'books')")
            conn.commit()
        self.client = app.test_client()

    def add_book(self, quantity=5):
        return self.client.post(
            "/add",
            data={
                "title": "Test Book",
                "author": "Test Author",
                "category": "Testing",
                "quantity": str(quantity),
            },
            follow_redirects=True,
        )

    def borrow(self, book_id, quantity=2):
        return self.client.post(
            "/borrow",
            data={
                "borrower_name": "Avery Reader",
                "book_id": str(book_id),
                "quantity": str(quantity),
                "issue_date": "2026-11-21",
                "expected_return_date": "2026-11-30",
            },
            follow_redirects=True,
        )

    def test_add_book_and_preserve_book_fields(self):
        response = self.add_book(quantity=4)
        self.assertIn(b"Book added successfully.", response.data)
        with closing(get_db_connection()) as conn:
            book = conn.execute("SELECT * FROM books").fetchone()
        self.assertEqual((book["title"], book["author"], book["category"], book["quantity"]),
                         ("Test Book", "Test Author", "Testing", 4))

    def test_borrow_reduces_stock_and_return_restores_it_once(self):
        self.add_book()
        with closing(get_db_connection()) as conn:
            book_id = conn.execute("SELECT id FROM books").fetchone()["id"]

        self.borrow(book_id, quantity=3)
        with closing(get_db_connection()) as conn:
            self.assertEqual(
                conn.execute("SELECT quantity FROM books WHERE id = ?", (book_id,)).fetchone()[0],
                2,
            )
            loan_id = conn.execute("SELECT id FROM loans").fetchone()["id"]

        response = self.client.post(
            f"/return/{loan_id}",
            follow_redirects=True,
        )
        self.assertIn(b"Book returned successfully.", response.data)
        with closing(get_db_connection()) as conn:
            self.assertEqual(
                conn.execute("SELECT quantity FROM books WHERE id = ?", (book_id,)).fetchone()[0],
                5,
            )
            loan = conn.execute(
                "SELECT status, actual_return_date FROM loans WHERE id = ?",
                (loan_id,),
            ).fetchone()
            self.assertEqual(loan["status"], "Returned")
            self.assertIsNotNone(loan["actual_return_date"])

        response = self.client.post(
            f"/return/{loan_id}",
            follow_redirects=True,
        )
        self.assertIn(b"already been returned", response.data)
        with closing(get_db_connection()) as conn:
            self.assertEqual(
                conn.execute("SELECT quantity FROM books WHERE id = ?", (book_id,)).fetchone()[0],
                5,
            )

    def test_insufficient_stock_does_not_create_loan_or_change_stock(self):
        self.add_book(quantity=2)
        with closing(get_db_connection()) as conn:
            book_id = conn.execute("SELECT id FROM books").fetchone()["id"]

        response = self.borrow(book_id, quantity=3)
        self.assertIn(b"Insufficient stock", response.data)
        with closing(get_db_connection()) as conn:
            self.assertEqual(
                conn.execute("SELECT quantity FROM books WHERE id = ?", (book_id,)).fetchone()[0],
                2,
            )
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0], 0)

    def test_active_loan_prevents_book_deletion(self):
        self.add_book()
        with closing(get_db_connection()) as conn:
            book_id = conn.execute("SELECT id FROM books").fetchone()["id"]
        self.borrow(book_id)

        response = self.client.post(
            f"/delete/{book_id}",
            follow_redirects=True,
        )
        self.assertIn(b"active loans", response.data)
        with closing(get_db_connection()) as conn:
            self.assertIsNotNone(
                conn.execute("SELECT id FROM books WHERE id = ?", (book_id,)).fetchone()
            )

    def test_invalid_book_quantity_is_rejected(self):
        response = self.client.post(
            "/add",
            data={
                "title": "Invalid Book",
                "author": "Test Author",
                "category": "Testing",
                "quantity": "-1",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Quantity must be between 0", response.data)
        with closing(get_db_connection()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM books").fetchone()[0], 0)

    def test_search_and_stock_update(self):
        self.add_book(quantity=4)
        with closing(get_db_connection()) as conn:
            book_id = conn.execute("SELECT id FROM books").fetchone()["id"]

        response = self.client.get("/?search=Test+Author")
        self.assertIn(b"Test Book", response.data)
        self.client.post(
            f"/stock/{book_id}",
            data={"quantity": "9"},
            follow_redirects=True,
        )
        with closing(get_db_connection()) as conn:
            self.assertEqual(
                conn.execute("SELECT quantity FROM books WHERE id = ?", (book_id,)).fetchone()[0],
                9,
            )
        self.client.post(
            f"/edit/{book_id}",
            data={
                "title": "Updated Test Book",
                "author": "Test Author",
                "category": "Testing",
                "quantity": "6",
            },
            follow_redirects=True,
        )
        with closing(get_db_connection()) as conn:
            updated_book = conn.execute(
                "SELECT title, quantity FROM books WHERE id = ?", (book_id,)
            ).fetchone()
        self.assertEqual((updated_book["title"], updated_book["quantity"]), ("Updated Test Book", 6))

    def test_deleting_returned_book_keeps_loan_history(self):
        self.add_book()
        with closing(get_db_connection()) as conn:
            book_id = conn.execute("SELECT id FROM books").fetchone()["id"]
        self.borrow(book_id, quantity=1)
        with closing(get_db_connection()) as conn:
            loan_id = conn.execute("SELECT id FROM loans").fetchone()["id"]

        self.client.post(f"/return/{loan_id}")
        self.client.post(f"/delete/{book_id}")

        with closing(get_db_connection()) as conn:
            self.assertIsNone(
                conn.execute("SELECT id FROM books WHERE id = ?", (book_id,)).fetchone()
            )
            history = conn.execute(
                "SELECT book_id, book_title, status FROM loans WHERE id = ?",
                (loan_id,),
            ).fetchone()
        self.assertIsNone(history["book_id"])
        self.assertEqual(history["book_title"], "Test Book")
        self.assertEqual(history["status"], "Returned")


if __name__ == "__main__":
    unittest.main()
