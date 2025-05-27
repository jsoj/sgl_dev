import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ProjetosList({ empresaId }) {
    const [projetos, setProjetos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Buscar projetos quando o componente montar ou empresaId mudar
        const fetchProjetos = async () => {
            try {
                setLoading(true);
                const response = await axios.get('/api/projetos/', {
                    params: { empresa: empresaId },
                    headers: {
                        'Authorization': `Token ${localStorage.getItem('authToken')}`
                    }
                });
                setProjetos(response.data.results || response.data);
                setError(null);
            } catch (err) {
                setError(err.message || 'Erro ao carregar projetos');
                console.error('Erro ao buscar projetos:', err);
            } finally {
                setLoading(false);
            }
        };

        if (empresaId) {
            fetchProjetos();
        } else {
            setProjetos([]);
            setLoading(false);
        }
    }, [empresaId]);

    if (loading) return <div>Carregando projetos...</div>;
    if (error) return <div className="error">Erro: {error}</div>;
    if (!projetos.length) return <div>Nenhum projeto encontrado para esta empresa.</div>;

    return (
        <div className="projetos-lista">
            <h2>Projetos da Empresa</h2>
            <ul>
                {projetos.map(projeto => (
                    <li key={projeto.id}>
                        <strong>{projeto.codigo_projeto}</strong> - {projeto.nome_projeto_cliente || 'Sem nome'}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default ProjetosList;
