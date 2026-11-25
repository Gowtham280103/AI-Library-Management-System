const bookSelect = document.querySelector("#book-select");
const borrowQuantity = document.querySelector("#borrow-quantity");

function updateBorrowLimit() {
    if (!bookSelect || !borrowQuantity) return;

    const option = bookSelect.selectedOptions[0];
    const stock = Number(option && option.dataset.stock);
    if (Number.isInteger(stock) && stock > 0) {
        borrowQuantity.max = String(stock);
        borrowQuantity.setCustomValidity(
            Number(borrowQuantity.value) > stock
                ? `Only ${stock} copies are available.`
                : ""
        );
    } else {
        borrowQuantity.removeAttribute("max");
        borrowQuantity.setCustomValidity("");
    }
}

if (bookSelect && borrowQuantity) {
    bookSelect.addEventListener("change", updateBorrowLimit);
    borrowQuantity.addEventListener("input", updateBorrowLimit);
    updateBorrowLimit();
}

document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
});

const recommendBook = document.querySelector("#recommend-book");
const recommendButton = document.querySelector("#recommend-button");
const recommendationMessage = document.querySelector("#recommendation-message");
const recommendationResults = document.querySelector("#recommendation-results");

if (recommendBook && recommendButton) {
    recommendButton.addEventListener("click", async () => {
        const bookId = recommendBook.value;

        recommendationResults.replaceChildren();

        if (!bookId) {
            recommendationMessage.textContent = "Please select a book first.";
            return;
        }

        recommendationMessage.textContent = "Finding similar books...";
        recommendButton.disabled = true;

        try {
            const response = await fetch(
                `/api/recommendations/${encodeURIComponent(bookId)}`
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Unable to get recommendations.");
            }

            if (data.recommendations.length === 0) {
                recommendationMessage.textContent =
                    "No similar books are currently available.";
                return;
            }

            recommendationMessage.textContent =
                `Found ${data.recommendations.length} recommended book(s).`;

            data.recommendations.forEach((book) => {
                const card = document.createElement("article");
                card.className = "recommendation-card";

                const title = document.createElement("h3");
                title.textContent = book.title;

                const author = document.createElement("p");
                author.textContent = `Author: ${book.author}`;

                const category = document.createElement("p");
                category.textContent = `Category: ${book.category}`;

                const stock = document.createElement("p");
                stock.textContent = `Available copies: ${book.quantity}`;

                card.append(title, author, category, stock);
                recommendationResults.appendChild(card);
            });

        } catch (error) {
            recommendationMessage.textContent = error.message;
        } finally {
            recommendButton.disabled = false;
        }
    });
}

