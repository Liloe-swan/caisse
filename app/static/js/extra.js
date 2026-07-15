(function() {
    const searchInput = document.getElementById('main-search-input');
    const resultsContainer = document.getElementById('search-results');
    const resultsList = document.getElementById('results-list');

    if (!searchInput || !resultsContainer || !resultsList) return;

    searchInput.addEventListener('input', async (e) => {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            resultsContainer.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Erreur réseau');
            
            const data = await response.json();
            
            resultsList.innerHTML = '';
            
            if (data.length > 0) {
                data.forEach(item => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <a href="${item.url}" class="block px-4 py-3 hover:bg-gray-50 transition">
                            <div class="flex justify-between items-center">
                                <span class="font-bold text-sm text-gray-800">${item.title}</span>
                                <span class="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded">${item.meta}</span>
                            </div>
                            <p class="text-xs text-gray-500">${item.subtitle}</p>
                        </a>
                    `;
                    resultsList.appendChild(li);
                });
                resultsContainer.classList.remove('hidden');
            } else {
                resultsList.innerHTML = '<li class="px-4 py-3 text-sm text-gray-400 text-center">Aucun résultat trouvé</li>';
                resultsContainer.classList.remove('hidden');
            }
        } catch (error) {
            console.error("Erreur de recherche:", error);
        }
    });

    // Fermer les résultats si on clique ailleurs
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.classList.add('hidden');
        }
    });
})();