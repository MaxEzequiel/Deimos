document.addEventListener("DOMContentLoaded", () => {

    const params = new URLSearchParams(window.location.search);
    const selAnio = document.getElementById("sel-anio");
    const selMes = document.getElementById("sel-mes");
    if (params.get("anio") && selAnio) selAnio.value = params.get("anio");
    if (params.get("mes") && selMes) selMes.value = params.get("mes");

    const qs = params.toString();
    const url = "/estadisticas/data/" + (qs ? `?${qs}` : "");

    const naranja = "#f39c12";
    const palette = ["#f39c12", "#3498db", "#2ecc71", "#e74c3c",
                     "#9b59b6", "#1abc9c", "#95a5a6", "#e67e22",
                     "#34495e", "#16a085"];
    const meses = ["Ene","Feb","Mar","Abr","May","Jun",
                   "Jul","Ago","Sep","Oct","Nov","Dic"];

    const lineOpts = () => ({
        plugins: { legend: { labels: { color: "#e0e0e0" } } },
        scales: {
            x: { ticks: { color: "#b0b0b0" } },
            y: { ticks: { color: "#b0b0b0" }, beginAtZero: true }
        }
    });

    fetch(url)
        .then(r => r.json())
        .then(data => {

            const labelsMes = data.mes ? [meses[data.mes - 1]] : meses;

            new Chart(document.getElementById("graficoMesUsuarios"), {
                type: "line",
                data: { labels: labelsMes, datasets: [{
                    label: "Usuarios", data: data.por_mes.map(m => m.cantidad),
                    borderColor: naranja, backgroundColor: "rgba(243,156,18,.2)",
                    fill: true, tension: .3
                }]},
                options: lineOpts()
            });

            new Chart(document.getElementById("graficoMesMembresias"), {
                type: "line",
                data: { labels: labelsMes, datasets: [{
                    label: "Membresías", data: data.membresias_mes.map(m => m.cantidad),
                    borderColor: "#3498db", backgroundColor: "rgba(52,152,219,.2)",
                    fill: true, tension: .3
                }]},
                options: lineOpts()
            });

            new Chart(document.getElementById("graficoMesRutinas"), {
                type: "line",
                data: { labels: labelsMes, datasets: [{
                    label: "Rutinas", data: data.rutinas_mes.map(m => m.cantidad),
                    borderColor: "#2ecc71", backgroundColor: "rgba(46,204,113,.2)",
                    fill: true, tension: .3
                }]},
                options: lineOpts()
            });

            new Chart(document.getElementById("graficoGrupo"), {
                type: "doughnut",
                data: {
                    labels: data.por_grupo.map(g => g.grupo),
                    datasets: [{ data: data.por_grupo.map(g => g.cantidad), backgroundColor: palette }]
                },
                options: { plugins: { legend: { position: "bottom", labels: { color: "#e0e0e0" } } } }
            });

            new Chart(document.getElementById("graficoMembresiasEstado"), {
                type: "pie",
                data: {
                    labels: data.membresias_estado.map(m => m.estado),
                    datasets: [{ data: data.membresias_estado.map(m => m.cantidad), backgroundColor: palette }]
                },
                options: { plugins: { legend: { position: "bottom", labels: { color: "#e0e0e0" } } } }
            });

            new Chart(document.getElementById("graficoActivos"), {
                type: "bar",
                data: {
                    labels: ["Activos", "Inactivos"],
                    datasets: [{
                        data: [data.activos_inactivos.activos, data.activos_inactivos.inactivos],
                        backgroundColor: ["#2ecc71", "#e74c3c"]
                    }]
                },
                options: { plugins: { legend: { display: false } },
                    scales: { x: { ticks: { color: "#b0b0b0" } },
                              y: { ticks: { color: "#b0b0b0" }, beginAtZero: true } } }
            });

            new Chart(document.getElementById("graficoTopClientes"), {
                type: "bar",
                data: {
                    labels: data.top_clientes.map(c => c.nombre || `Cliente #${c.cliente_id}`),
                    datasets: [{ label: "Rutinas", data: data.top_clientes.map(c => c.cantidad), backgroundColor: naranja }]
                },
                options: { indexAxis: "y", plugins: { legend: { display: false } },
                    scales: { x: { ticks: { color: "#b0b0b0" }, beginAtZero: true },
                              y: { ticks: { color: "#b0b0b0" } } } }
            });

        })
        .catch(err => console.error("Error cargando estadísticas:", err));
});