"use strict";

const subscriptionForm = document.getElementById("subscription-payment-form");
if (subscriptionForm) {
	const prices = JSON.parse(document.getElementById("course-prices").textContent);
	const charges = JSON.parse(document.getElementById("subscription-charges").textContent);
	const kind = subscriptionForm.querySelector('[name="kind"]');
	const period = subscriptionForm.querySelector('[name="period"]');
	const amount = subscriptionForm.querySelector('[name="amount"]');
	const courses = [...subscriptionForm.querySelectorAll('[name="courses"]')];
	const currency = new Intl.NumberFormat("es-AR", {style: "currency", currency: "ARS"});
	function update() {
		const charge = charges[period.value];
		kind.disabled = false;
		if (charge) kind.value = charge.kind;
		const courseSection = subscriptionForm.querySelector("[data-payment-courses]");
		if (courseSection) courseSection.hidden = kind.value === "gym" || !!charge;
		let cents = kind.value === "classes" ? 0 : Math.round(Number(subscriptionForm.dataset.gymPrice) * 100);
		courses.forEach(input => {
			input.disabled = !!charge || kind.value === "gym";
			if (!input.disabled && input.checked) cents += Math.round(Number(prices[input.value]) * 100);
		});
		amount.value = charge ? charge.amount : (cents / 100).toFixed(2);
		document.getElementById("payment-total").textContent = currency.format(Number(amount.value));
		const detail = document.getElementById("payment-detail");
		detail.replaceChildren();
		if (charge) {
			const note = document.createElement("p");
			note.textContent = "La cuota existente conserva su concepto y precio original.";
			detail.append(note);
			charge.items.forEach(item => {
				const row = document.createElement("p");
				row.textContent = `${item.name}: ${currency.format(Number(item.price))}`;
				detail.append(row);
			});
		}
	}
	subscriptionForm.addEventListener("change", update);
	update();
}
