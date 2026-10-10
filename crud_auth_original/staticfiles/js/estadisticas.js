document.addEventListener("DOMContentLoaded", () => {

	const params = new URLSearchParams(window.location.search);
	const selAnio = document.getElementById("sel-anio");
	const selMes = document.getElementById("sel-mes");
	if (params.get("anio") && selAnio) selAnio.value = params.get(
		"anio");
	if (params.get("mes") && selMes) selMes.value = params.get("mes");

	const qs = params.toString();
	const url = "/estadisticas/data/" + (qs ? `?${qs}` : "");

	const naranja = "#f39c12";
	const palette = ["#f39c12", "#3498db", "#2ecc71", "#e74c3c",
		"#9b59b6", "#1abc9c", "#95a5a6", "#e67e22",
		"#34495e", "#16a085"
	];
	const meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
		"Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
	];

	const lineOpts = () => ({
		plugins: {
			legend: {
				labels: {
					color: "#e0e0e0"
				}
			}
		},
		scales: {
			x: {
				ticks: {
					color: "#b0b0b0"
				}
			},
			y: {
				ticks: {
					color: "#b0b0b0"
				},
				beginAtZero: true
			}
		}
	});

	const charts = [];

	function applyChartTheme(chart) {
		const style = getComputedStyle(document.body);
		const text = style.getPropertyValue('--text-secondary')
		.trim() || '#b0b0b0';
		const border = style.getPropertyValue('--border-color')
		.trim() || '#ffffff20';
		chart.options.plugins.legend.labels.color = text;
		Object.values(chart.options.scales || {}).forEach(scale => {
			scale.ticks.color = text;
			scale.grid.color = border;
		});
	}
	document.addEventListener('deimos:appearance', () => {
		charts.forEach(chart => {
			applyChartTheme(chart);
			chart.update('none');
		});
	});

	// Helper: solo crea el gráfico si el canvas existe
	function crear(id, config) {
		const el = document.getElementById(id);
		if (!el) return; // canvas no existe → no hace nada
		const chart = new Chart(el, config);
		charts.push(chart);
		applyChartTheme(chart);
		chart.update('none');
	}

	fetch(url)
		.then(r => {
			if (!r.ok) throw new Error(
				"No se pudieron cargar las estadísticas");
			return r.json();
		})
		.then(data => {

			const diario = data.actividad_diaria;
			const labelsDia = diario.map(d => {
				const [anio, mes, dia] = d.fecha.split("-");
				return `${dia}/${mes}/${anio}`;
			});
			const moneda = new Intl.NumberFormat("es-AR", {style: "currency", currency: "ARS"});
			const ingresosOpts = lineOpts();
			ingresosOpts.scales.y.ticks.callback = value => moneda.format(value);
			ingresosOpts.plugins.tooltip = {callbacks: {
				label: ctx => `${ctx.dataset.label}: ${moneda.format(ctx.parsed.y)}`
			}};
			crear("graficoIngresosDia", {
				type: "line",
				data: {labels: labelsDia, datasets: [
					{label: "Ingresos", data: diario.map(d => Number(d.ingresos)), borderColor: "#2ecc71"},
					{label: "Anulaciones", data: diario.map(d => Number(d.anulaciones)), borderColor: "#e74c3c"},
					{label: "Neto", data: diario.map(d => Number(d.neto)), borderColor: naranja}
				]},
				options: ingresosOpts
			});
			const checkinsOpts = lineOpts();
			checkinsOpts.scales.y.ticks.precision = 0;
			crear("graficoCheckinsDia", {
				type: "bar",
				data: {labels: labelsDia, datasets: [
					{label: "Check-ins", data: diario.map(d => d.checkins), backgroundColor: "#3498db"}
				]},
				options: checkinsOpts
			});

			const labelsMes = data.mes ? [meses[data.mes - 1]] :
				meses;

			// --- Línea: usuarios por mes ---
			crear("graficoMesUsuarios", {
				type: "line",
				data: {
					labels: labelsMes,
					datasets: [{
						label: "Usuarios",
						data: data.por_mes.map(m =>
							m.cantidad),
						borderColor: naranja,
						backgroundColor: "rgba(243,156,18,.2)",
						fill: true,
						tension: .3
					}]
				},
				options: lineOpts()
			});

			// --- Línea: rutinas por mes (solo si el canvas existe) ---
			crear("graficoMesRutinas", {
				type: "line",
				data: {
					labels: labelsMes,
					datasets: [{
						label: "Rutinas",
						data: data.rutinas_mes
							.filter(m => !data
								.mes || m.mes ===
								data.mes).map(m => m
								.cantidad),
						borderColor: "#2ecc71",
						backgroundColor: "rgba(46,204,113,.2)",
						fill: true,
						tension: .3
					}]
				},
				options: lineOpts()
			});

			// --- Barras: pagos realizados y anulaciones ---
			crear("graficoPagos", {
				type: "bar",
				data: {
					labels: data.pagos_mes.map(p => meses[p
						.mes - 1]),
					datasets: [{
						label: "Pagos realizados",
						data: data.pagos_mes.map(
							p => p.pagos),
						backgroundColor: "#2ecc71"
					}, {
						label: "Anulaciones",
						data: data.pagos_mes.map(
							p => p.anulaciones),
						backgroundColor: "#e74c3c"
					}]
				},
				options: {
					plugins: {
						legend: {
							position: "bottom",
							labels: {
								color: "#e0e0e0"
							}
						}
					},
					scales: {
						x: {
							ticks: {
								color: "#b0b0b0"
							}
						},
						y: {
							ticks: {
								color: "#b0b0b0"
							},
							beginAtZero: true,
							precision: 0
						}
					}
				}
			});

			// --- Barras horizontales: top clientes ---
			crear("graficoTopClientes", {
				type: "bar",
				data: {
					labels: data.top_clientes.map(c => c
						.nombre ||
						`Cliente #${c.cliente_id}`),
					datasets: [{
						label: "Rutinas",
						data: data.top_clientes.map(
							c => c.cantidad),
						backgroundColor: naranja
					}]
				},
				options: {
					indexAxis: "y",
					plugins: {
						legend: {
							display: false
						}
					},
					scales: {
						x: {
							ticks: {
								color: "#b0b0b0"
							},
							beginAtZero: true
						},
						y: {
							ticks: {
								color: "#b0b0b0"
							}
						}
					}
				}
			});

		})
		.catch(err => console.error("Error cargando estadísticas:",
			err));
});
