/**
 * Carrega projetos por empresa utilizando jQuery AJAX
 * @param {number} empresaId - ID da empresa para filtrar
 * @param {function} callback - Função de callback para processar os resultados
 */
function carregarProjetosPorEmpresa(empresaId, callback) {
    $.ajax({
        url: '/api/projetos/',
        method: 'GET',
        data: {
            empresa: empresaId
        },
        headers: {
            'Authorization': 'Token ' + localStorage.getItem('authToken')
        },
        success: function(data) {
            callback(null, data);
        },
        error: function(xhr, status, error) {
            console.error('Erro ao carregar projetos:', error);
            callback(error, null);
        }
    });
}

// Exemplo de uso com jQuery para popular um select
$(document).ready(function() {
    // Quando o select de empresa mudar
    $('#empresa-select').change(function() {
        const empresaId = $(this).val();
        
        if (empresaId) {
            // Limpar e mostrar loading
            $('#projeto-select').empty().append('<option>Carregando...</option>');
            
            // Carregar projetos da empresa selecionada
            carregarProjetosPorEmpresa(empresaId, function(err, data) {
                $('#projeto-select').empty();
                $('#projeto-select').append('<option value="">Selecione um projeto</option>');
                
                if (!err && data && data.results) {
                    // Adicionar opções de projetos ao select
                    $.each(data.results || data, function(i, projeto) {
                        $('#projeto-select').append(
                            $('<option>', {
                                value: projeto.id,
                                text: projeto.codigo_projeto + ' - ' + (projeto.nome_projeto_cliente || 'Sem nome')
                            })
                        );
                    });
                } else {
                    $('#projeto-select').append('<option disabled>Erro ao carregar projetos</option>');
                }
            });
        } else {
            // Resetar o select de projetos
            $('#projeto-select').empty().append('<option value="">Selecione uma empresa primeiro</option>');
        }
    });
});
