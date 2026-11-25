# AI-Enabled Library Management System

Flask and SQLite app for managing the existing book inventory, borrowing, and returns.

## Run locally

From the project directory, activate the included environment and start Flask:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Set-Location .\backend
python app.py
```

Open <http://127.0.0.1:5000>. The app uses the existing `library.db` at the project root (regardless of the current directory), preserves the existing `books` table and records, and creates the `loans` table on startup. To use a different database, set `LIBRARY_DB_PATH` before starting the app.

## Features

- Add, search, edit, update available stock, and delete books.
- Borrow available copies and automatically deduct them from inventory.
- Return active loans once and automatically restore the copies.
- View active loans and the complete borrowing history.
- Books with active loans cannot be deleted. Deleting a book with only returned loans retains the loan history and its recorded book title.

## Tests

From the project directory:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

Tests use a temporary SQLite database and do not modify `library.db`.

## Database Design & Integration

### Database Used
- SQLite
- Database file: `library.db`
- Backend integration: Python and Flask

### Database Tables

**1. Books**

| Column | Data Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| title | TEXT | Book title |
| author | TEXT | Author name |
| category | TEXT | Book category |
| quantity | INTEGER | Available quantity |

**2. Loans**

| Column | Data Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| book_id | INTEGER | Foreign key referencing books.id |
| book_title | TEXT | Book title |
| borrower_name | TEXT | Borrower's name |
| quantity | INTEGER | Borrowed quantity |
| issue_date | TEXT | Issue date |
| expected_return_date | TEXT | Expected return date |
| actual_return_date | TEXT | Actual return date |
| status | TEXT | Loan status |

### Database Relationship
The books and loans tables are connected through `books.id` and `loans.book_id`. One book can have multiple loan records.

### CRUD Operations
- **Create:** Inserted a temporary test book.
- **Read:** Retrieved the inserted book record.
- **Update:** Changed its quantity from 5 to 10.
- **Delete:** Successfully deleted the temporary test book.

### Database Connectivity
The application uses Python's SQLite3 module to connect to the SQLite database and execute SQL queries.

### Testing Result
All four CRUD operations were successfully tested. The original book record remained unchanged after the temporary test record was deleted.

### Conclusion
The database structure and integration were verified successfully. The application can store, retrieve, update and delete library records using SQLite.

