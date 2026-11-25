
import re
from collections import Counter


def tokenize(value):
    return set(re.findall(r"[a-z0-9]+", (value or "").lower()))


def recommend_books(conn, book_id, limit=5):
    selected = conn.execute(
        "SELECT id, title, author, category FROM books WHERE id = ?",
        (book_id,)
    ).fetchone()

    if selected is None:
        return None

    books = conn.execute(
        """
        SELECT id, title, author, category, quantity
        FROM books
        WHERE id != ? AND quantity > 0
        """,
        (book_id,)
    ).fetchall()

    selected_title = tokenize(selected["title"])
    selected_author = tokenize(selected["author"])
    selected_category = tokenize(selected["category"])

    recommendations = []

    for book in books:
        title_tokens = tokenize(book["title"])
        author_tokens = tokenize(book["author"])
        category_tokens = tokenize(book["category"])

        title_match = len(selected_title & title_tokens)
        author_match = len(selected_author & author_tokens)
        category_match = len(selected_category & category_tokens)

        score = (
            title_match * 2
            + author_match * 3
            + category_match * 5
        )

        if score > 0:
            recommendations.append({
                "id": book["id"],
                "title": book["title"],
                "author": book["author"],
                "category": book["category"],
                "quantity": book["quantity"],
                "score": score
            })

    recommendations.sort(
        key=lambda item: (-item["score"], item["title"].lower())
    )

    return recommendations[:limit]
