// Fonction globale pour initialiser les graphiques du dashboard
function initDashboardCharts(salesLabels, salesData, topProductsLabels, topProductsData) {
    
    // --- 1. CONFIGURATION DU GRAPHIQUE DES VENTES (COURBE VERTE) ---
    const canvasSales = document.getElementById('salesEvolutionChart');
    if (canvasSales) {
        const ctxSales = canvasSales.getContext('2d');
        
        const salesGradient = ctxSales.createLinearGradient(0, 0, 0, 250);
        salesGradient.addColorStop(0, 'rgba(16, 185, 129, 0.25)'); // Vert émeraude opaque
        salesGradient.addColorStop(1, 'rgba(16, 185, 129, 0.00)'); // Transparent

        new Chart(ctxSales, {
            type: 'line',
            data: {
                labels: salesLabels.length ? salesLabels : ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
                datasets: [{
                    label: 'Ventes (FCFA)',
                    data: salesData.length ? salesData : [0, 0, 0, 0, 0, 0, 0],
                    borderColor: '#10b981',
                    borderWidth: 3,
                    pointBackgroundColor: '#10b981',
                    pointHoverRadius: 6,
                    tension: 0.35,
                    fill: true,
                    backgroundColor: salesGradient
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: '#9ca3af', font: { size: 11 } }
                    },
                    y: {
                        grid: { color: '#f3f4f6' },
                        border: { display: false },
                        ticks: { color: '#9ca3af', font: { size: 11 } }
                    }
                }
            }
        });
    }

    // --- 2. CONFIGURATION DU GRAPH DES 3 PRODUITS LES PLUS VENDUS (BAR CHART VERTICAL) ---
    const canvasTopProducts = document.getElementById('topProductsChart');
    if (canvasTopProducts) {
        const ctxProducts = canvasTopProducts.getContext('2d');

        new Chart(ctxProducts, {
            type: 'bar',
            data: {
                labels: topProductsLabels.length ? topProductsLabels : ["Aucun produit", "Aucun produit", "Aucun produit"],
                datasets: [{
                    label: 'Quantité vendue',
                    data: topProductsData.length ? topProductsData : [0, 0, 0],
                    backgroundColor: 'rgba(16, 185, 129, 0.85)', // Vert émeraude plein
                    hoverBackgroundColor: '#10b981', // Teinte plus vive au survol
                    borderRadius: [6, 6, 0, 0], // Arrondit uniquement le haut des barres verticales
                    borderSkipped: 'bottom',
                    barThickness: 32 // Largeur ajustée pour l'espace vertical
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false } 
                },
                scales: {
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { 
                            color: '#4b5563', // Noms des produits bien visibles en bas
                            font: { size: 11, weight: 'bold' }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f3f4f6' }, // Lignes de repère horizontales discrètes
                        border: { display: false },
                        ticks: { 
                            color: '#9ca3af', 
                            font: { size: 11 },
                            precision: 0 // Uniquement des entiers pour les quantités sur le côté
                        }
                    }
                }
            }
        });
    }
}