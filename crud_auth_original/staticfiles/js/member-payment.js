"use strict";

const memberPlanSelect = document.getElementById("id_plan");
const memberPlanPrices = document.getElementById("member-plan-prices");
const memberPlanPriceLabel = document.getElementById("selected-plan-price");
const memberPaymentForm = document.getElementById("member-payment-form");

if (memberPlanSelect && memberPlanPrices && memberPaymentForm) {
	const prices = JSON.parse(memberPlanPrices.textContent);
	const amount = memberPaymentForm.querySelector('[name="amount"]');
	const kind = memberPaymentForm.querySelector('[name="kind"]');
	const coursePricesElement = document.getElementById("member-course-prices");
	const coursePrices = coursePricesElement ? JSON.parse(coursePricesElement.textContent) : {};
	const courses = [...memberPaymentForm.querySelectorAll('[name="courses"]')];
	const currency = new Intl.NumberFormat("es-AR", {
		style: "currency",
		currency: "ARS",
	});

	const updateSelectedPlanPrice = () => {
		const courseSection = memberPaymentForm.querySelector("[data-payment-courses]");
		if (courseSection) courseSection.hidden = !kind || kind.value === "gym" || memberPaymentForm.dataset.amountLocked === "true";
		const price = prices[memberPlanSelect.value];
		memberPlanPriceLabel.textContent = price !== undefined
			? currency.format(Number(price))
			: "Sin plan seleccionado";

		if (amount && memberPaymentForm.dataset.amountLocked !== "true") {
			let cents = kind && kind.value === "classes" ? 0 : Math.round(Number(price || 0) * 100);
			courses.forEach(input => {
				input.disabled = !kind || kind.value === "gym";
				if (!input.disabled && input.checked) cents += Math.round(Number(coursePrices[input.value] || 0) * 100);
			});
			amount.value = (cents / 100).toFixed(2);
		}
	};

	memberPlanSelect.addEventListener("change", updateSelectedPlanPrice);
	memberPaymentForm.addEventListener("change", updateSelectedPlanPrice);
	updateSelectedPlanPrice();
}
