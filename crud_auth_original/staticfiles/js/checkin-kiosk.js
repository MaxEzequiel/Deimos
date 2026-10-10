(() => {
	'use strict';
	const clock = document.querySelector('[data-clock]');
	const date = document.querySelector('[data-date]');
	const updateClock = () => {
		const now = new Date();
		const timeZone = 'America/Argentina/Buenos_Aires';
		if (clock) clock.textContent = now.toLocaleTimeString('es-AR', {
			timeZone,
			hour: '2-digit',
			minute: '2-digit',
			hour12: false
		});
		if (date) date.textContent = now.toLocaleDateString('es-AR', {
			timeZone,
			weekday: 'long',
			day: 'numeric',
			month: 'short'
		});
	};
	updateClock();
	setInterval(updateClock, 1000);
	const fullscreen = document.querySelector('[data-fullscreen]');
	if (!document.fullscreenEnabled && fullscreen) fullscreen.hidden = true;
	fullscreen?.addEventListener('click', async () => {
		try {
			if (document.fullscreenElement) await document
				.exitFullscreen();
			else await document.documentElement
				.requestFullscreen();
		} catch (_) {
			/* Pantalla completa no disponible en este navegador. */ }
	});
	const form = document.querySelector('[data-entry-form]');
	if (form) {
		const input = form.querySelector('#id_dni');
		input.addEventListener('input', () => input.setCustomValidity(''));
		form.addEventListener('submit', event => {
			if (!/^\d{6,10}$/.test(input.value.trim())) {
				event.preventDefault();
				input.setCustomValidity(
					'Ingresá un DNI de 6 a 10 dígitos, sin puntos ni espacios.'
					);
				input.reportValidity();
				return;
			}
			form.querySelector('[type="submit"]').disabled = true;
			form.querySelector('[data-submit-label]').textContent =
				'Registrando…';
			form.setAttribute('aria-busy', 'true');
		});
		window.addEventListener('pageshow', () => {
			form.querySelector('[type="submit"]').disabled = false;
			form.querySelector('[data-submit-label]').textContent =
				'Registrar ingreso';
			form.removeAttribute('aria-busy');
			input.focus({
				preventScroll: true
			});
		});
	}
	const confirmation = document.querySelector('[data-confirmation]');
	if (confirmation) {
		document.addEventListener('keydown', event => {
			if (event.repeat || !['Enter', 'Escape'].includes(event
					.key)) return;
			if (event.altKey || event.ctrlKey || event.metaKey ||
				event.isComposing) return;
			if (event.target.closest(
					'button, input, textarea, select') && event
				.key === 'Enter') return;
			event.preventDefault();
			window.location.replace(confirmation.dataset.returnUrl);
		});
	}
})();
