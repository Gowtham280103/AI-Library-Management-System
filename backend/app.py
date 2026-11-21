
from flask import Flask, render_template, request, redirect, url_for
from db import get_db_connection, create_table

app = Flask(__name__)

create_table()

@app.route("/")
def index():
    search = request.args.get("search", "")

    conn = get_db_connection()

    books = conn.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ?",
        (f"%{search}%", f"%{search}%")
    ).fetchall()

    conn.close()

    return render_template("index.html", books=books, search=search)


@app.route("/add", methods=["POST"])
def add_book():
    title = request.form["title"]
    author = request.form["author"]
    category = request.form["category"]
    quantity = request.form["quantity"]

    conn = get_db_connection()

    conn.execute(
        "INSERT INTO books (title, author, category, quantity) VALUES (?, ?, ?, ?)",
        (title, author, category, quantity)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:book_id>")
def delete_book(book_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM books WHERE id = ?",
        (book_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/edit/<int:book_id>", methods=["POST"])
def edit_book(book_id):
    title = request.form["title"]
    author = request.form["author"]
    category = request.form["category"]
    quantity = request.form["quantity"]

    conn = get_db_connection()

    conn.execute(
        "UPDATE books SET title=?, author=?, category=?, quantity=? WHERE id=?",
        (title, author, category, quantity, book_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
