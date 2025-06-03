/**
 * Busca projetos filtrados por empresa
 * @param {number} empresaId - ID da empresa para filtrar
 * @returns {Promise} Promise com os dados dos projetos
 */
function fetchProjetosPorEmpresa(empresaId) {
    // Constrói URL com parâmetro de filtro
    const url = `/api/projetos/?empresa=${empresaId}`;
    
    return fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            // Para APIs autenticadas, inclua o token
            'Authorization': `Token ${localStorage.getItem('authToken')}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
    })
    .catch(error => {
        console.error('Erro ao buscar projetos:', error);
        throw error;
    });
}

// Exemplo de uso:
// fetchProjetosPorEmpresa(1)
//     .then(data => {
//         console.log('Projetos da empresa:', data);
//     })
//     .catch(error => {
//         console.error('Falha ao carregar projetos:', error);
//     });
