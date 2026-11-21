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
