
from contextlib import closing
from datetime import date
import os

from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from db import get_db_connection, create_table
from recommendations import recommend_books

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "library-management-development-key"
)

create_table()


class UserInputError(Exception):
    pass


def required_text(field, label, max_length):
    value = request.form.get(field, "").strip()
    if not value:
        raise UserInputError(f"{label} is required.")
    if len(value) > max_length:
        raise UserInputError(f"{label} must be {max_length} characters or fewer.")
    return value


def form_quantity(field, label, minimum):
    raw_value = request.form.get(field, "").strip()
    try:
        quantity = int(raw_value)
    except ValueError:
        raise UserInputError(f"{label} must be a whole number.") from None
    if quantity < minimum or quantity > 2147483647:
        raise UserInputError(
            f"{label} must be between {minimum} and 2,147,483,647."
        )
    return quantity


def form_date(field, label):
    raw_value = request.form.get(field, "").strip()
    try:
        return date.fromisoformat(raw_value).isoformat()
    except ValueError:
        raise UserInputError(f"Enter a valid {label.lower()}.") from None


def book_form_values():
    return (
        required_text("title", "Book title", 200),
        required_text("author", "Author name", 200),
        required_text("category", "Category", 100),
    )


@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    with closing(get_db_connection()) as conn:
        books = conn.execute(
            """
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR category LIKE ?
            ORDER BY title COLLATE NOCASE, id
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        ).fetchall()
        available_titles = conn.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()[0]
        available_copies = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM books"
        ).fetchone()[0]
        active_loans = conn.execute(
            """
            SELECT loans.id, loans.book_id, loans.book_title, loans.borrower_name,
                   loans.quantity, loans.issue_date, loans.expected_return_date
            FROM loans
            WHERE loans.status = 'Borrowed'
            ORDER BY loans.expected_return_date, loans.id
            """
        ).fetchall()
        history = conn.execute(
            """
            SELECT id, book_title, borrower_name, quantity, issue_date,
                   expected_return_date, actual_return_date, status
            FROM loans
            ORDER BY id DESC
            """
        ).fetchall()
        borrowable_books = conn.execute(
            """
            SELECT id, title, author, quantity
            FROM books
            WHERE quantity > 0
            ORDER BY title COLLATE NOCASE, id
            """
        ).fetchall()

    return render_template(
        "index.html",
        books=books,
        search=search,
        available_titles=available_titles,
        available_copies=available_copies,
        active_loans=active_loans,
        history=history,
        borrowable_books=borrowable_books,
        today=date.today().isoformat(),
    )


@app.route("/add", methods=["POST"])
def add_book():
    try:
        title, author, category = book_form_values()
        quantity = form_quantity("quantity", "Quantity", 0)
    except UserInputError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    with closing(get_db_connection()) as conn:
        conn.execute(
            """
            INSERT INTO books (title, author, category, quantity)
            VALUES (?, ?, ?, ?)
            """,
            (title, author, category, quantity),
        )
        conn.commit()

    flash("Book added successfully.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    try:
        with closing(get_db_connection()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            active_loan = conn.execute(
                """
                SELECT 1 FROM loans
                WHERE book_id = ? AND status = 'Borrowed'
                LIMIT 1
                """,
                (book_id,),
            ).fetchone()
            if active_loan:
                raise UserInputError("Return this book's active loans before deleting it.")

            result = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
            if result.rowcount == 0:
                raise UserInputError("Book not found.")
            conn.commit()
    except UserInputError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    flash("Book deleted successfully.", "success")
    return redirect(url_for("index"))


@app.route("/edit/<int:book_id>", methods=["POST"])
def edit_book(book_id):
    try:
        title, author, category = book_form_values()
        quantity_value = request.form.get("quantity")
        quantity = (
            form_quantity("quantity", "Quantity", 0)
            if quantity_value is not None
            else None
        )
    except UserInputError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    with closing(get_db_connection()) as conn:
        if quantity is None:
            result = conn.execute(
                """
                UPDATE books SET title = ?, author = ?, category = ?
                WHERE id = ?
                """,
                (title, author, category, book_id),
            )
        else:
            result = conn.execute(
                """
                UPDATE books
                SET title = ?, author = ?, category = ?, quantity = ?
                WHERE id = ?
                """,
                (title, author, category, quantity, book_id),
            )
        conn.commit()

    if result.rowcount == 0:
        flash("Book not found.", "error")
    else:
        flash("Book details updated successfully.", "success")
    return redirect(url_for("index"))


@app.route("/stock/<int:book_id>", methods=["POST"])
def update_stock(book_id):
    try:
        quantity = form_quantity("quantity", "Available stock", 0)
    except UserInputError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    with closing(get_db_connection()) as conn:
        result = conn.execute(
            "UPDATE books SET quantity = ? WHERE id = ?",
            (quantity, book_id),
        )
        conn.commit()

    if result.rowcount == 0:
        flash("Book not found.", "error")
    else:
        flash("Available stock updated successfully.", "success")
    return redirect(url_for("index"))


@app.route("/borrow", methods=["POST"])
def borrow_book():
    try:
        borrower_name = required_text("borrower_name", "Borrower name", 120)
        book_id = form_quantity("book_id", "Book", 1)
        quantity = form_quantity("quantity", "Borrow quantity", 1)
        issue_date = form_date("issue_date", "Issue date")
        expected_return_date = form_date(
            "expected_return_date", "Expected return date"
        )
        if expected_return_date < issue_date:
            raise UserInputError(
                "Expected return date cannot be before the issue date."
            )
    except UserInputError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    try:
        with closing(get_db_connection()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            book = conn.execute(
                "SELECT title, quantity FROM books WHERE id = ?",
                (book_id,),
            ).fetchone()
            if book is None:
                raise UserInputError("The selected book does not exist.")
            if quantity > book["quantity"]:
                raise UserInputError(
                    f"Insufficient stock. Only {book['quantity']} available."
                )

            updated = conn.execute(
                """
                UPDATE books SET quantity = quantity - ?
                WHERE id = ? AND quantity >= ?
                """,
                (quantity, book_id, quantity),
            )
            if updated.rowcount != 1:
                raise UserInputError("Insufficient stock for this borrowing.")
            conn.execute(
                """
                INSERT INTO loans (
                    book_id, book_title, borrower_name, quantity,
                    issue_date, expected_return_date
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    book["title"],
                    borrower_name,
                    quantity,
                    issue_date,
                    expected_return_date,
                ),
            )
            conn.commit()
    except UserInputError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    flash("Book borrowed successfully.", "success")
    return redirect(url_for("index"))


@app.route("/return/<int:loan_id>", methods=["POST"])
def return_book(loan_id):
    try:
        with closing(get_db_connection()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            loan = conn.execute(
                """
                SELECT book_id, quantity, status
                FROM loans
                WHERE id = ?
                """,
                (loan_id,),
            ).fetchone()
            if loan is None:
                raise UserInputError("Borrowing record not found.")
            if loan["status"] != "Borrowed":
                raise UserInputError("This borrowing record has already been returned.")

            returned = conn.execute(
                """
                UPDATE loans
                SET status = 'Returned', actual_return_date = ?
                WHERE id = ? AND status = 'Borrowed'
                """,
                (date.today().isoformat(), loan_id),
            )
            if returned.rowcount != 1:
                raise UserInputError("This borrowing record has already been returned.")
            restocked = conn.execute(
                "UPDATE books SET quantity = quantity + ? WHERE id = ?",
                (loan["quantity"], loan["book_id"]),
            )
            if restocked.rowcount != 1:
                raise UserInputError(
                    "The associated book is no longer in inventory; the return was not recorded."
                )
            conn.commit()
    except UserInputError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    flash("Book returned successfully.", "success")
    return redirect(url_for("index"))


@app.route("/api/recommendations/<int:book_id>", methods=["GET"])
def book_recommendations(book_id):
    try:
        with closing(get_db_connection()) as conn:
            recommendations = recommend_books(conn, book_id)

            if recommendations is None:
                return jsonify({
                    "success": False,
                    "message": "Book not found."
                }), 404

            return jsonify({
                "success": True,
                "book_id": book_id,
                "recommendations": recommendations
            }), 200

    except Exception:
        app.logger.exception("Recommendation API failed")
        return jsonify({
            "success": False,
            "message": "Unable to generate recommendations."
        }), 500
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)