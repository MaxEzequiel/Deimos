"use strict";

const printInvoiceButton = document.getElementById("print-invoice");

if (printInvoiceButton) {
	printInvoiceButton.addEventListener("click", () => window.print());
}
