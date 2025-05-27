/**
 * Busca projetos filtrados por empresa usando Axios
 * @param {number} empresaId - ID da empresa para filtrar
 * @returns {Promise} Promise com os dados dos projetos
 */
function getProjetosPorEmpresa(empresaId) {
    const baseURL = '/api/projetos/';
    
    return axios.get(baseURL, {
        params: {
            empresa: empresaId
        },
        headers: {
            'Authorization': `Token ${localStorage.getItem('authToken')}`
        }
    })
    .then(response => response.data)
    .catch(error => {
        console.error('Erro ao buscar projetos:', error);
        throw error;
    });
}

// Função para obter um projeto específico
function getProjetoDetalhe(projetoId) {
    return axios.get(`/api/projetos/${projetoId}/`, {
        headers: {
            'Authorization': `Token ${localStorage.getItem('authToken')}`
        }
    })
    .then(response => response.data)
    .catch(error => {
        console.error(`Erro ao buscar projeto ${projetoId}:`, error);
        throw error;
    });
}
