/* Se carga en head: aplica la elección antes de mostrar la página. */
(() => {
	'use strict';
	const root = document.documentElement;
	const read = key => {
		try {
			return localStorage.getItem(key);
		} catch (_) {
			return null;
		}
	};
	const save = (key, value) => {
		try {
			localStorage.setItem(key, value);
		} catch (_) {
			/* Funciona sin almacenamiento. */ }
	};
	const design = 'deimos';
	const preference = window.matchMedia('(prefers-color-scheme: light)');
	let explicitTheme = ['light', 'dark'].includes(read('theme'));
	let theme = explicitTheme ? read('theme') : (preference.matches ?
		'light' : 'dark');
	const apply = () => {
		root.dataset.design = design;
		root.dataset.theme = theme;
		root.classList.toggle('light-mode-preload', theme === 'light');
		if (document.body) document.body.classList.toggle('light-mode',
			theme === 'light');
		document.querySelectorAll('[data-theme-toggle]').forEach(
			button => {
				const next = theme === 'dark' ? 'claro' : 'oscuro';
				button.setAttribute('aria-label',
					`Cambiar a tema ${next}`);
				button.title = `Cambiar a tema ${next}`;
				button.querySelector('[data-theme-symbol]')
					.textContent = theme === 'dark' ? '☀' : '☾';
				button.querySelector('[data-theme-label]')
					.textContent = theme === 'dark' ? 'Claro' :
					'Oscuro';
			});
		// Permite a módulos como gráficos reaccionar sin duplicar preferencias.
		document.dispatchEvent(new CustomEvent('deimos:appearance', {
			detail: {
				design,
				theme
			}
		}));
	};
	apply();
	document.addEventListener('DOMContentLoaded', () => {
		apply();
		document.querySelectorAll('[data-theme-toggle]').forEach(
			button => button.addEventListener('click', () => {
				explicitTheme = true;
				theme = theme === 'dark' ? 'light' : 'dark';
				save('theme', theme);
				apply();
			}));
		const currentPath = window.location.pathname.replace(/\/$/,
			'');
		document.querySelectorAll('.sidebar-menu a[href]').forEach(
			link => {
				const path = new URL(link.href, window.location
					.origin).pathname.replace(/\/$/, '');
				if (path === currentPath || (path && currentPath
						.startsWith(path + '/'))) link
					.setAttribute('aria-current', 'page');
			});
	});
	preference.addEventListener('change', () => {
		if (!explicitTheme) {
			theme = preference.matches ? 'light' : 'dark';
			apply();
		}
	});
	window.addEventListener('storage', event => {
		if (event.key === 'theme' || event.key === null) {
			explicitTheme = ['light', 'dark'].includes(read(
				'theme'));
			theme = explicitTheme ? read('theme') : (preference
				.matches ? 'light' : 'dark');
			apply();
		}
	});
})();
