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
