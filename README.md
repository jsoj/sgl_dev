# Sistema de Gestão de Laboratório (SGL)

## Estrutura do Projeto

# SGL - Sistema de Gestão de Laboratório - V.1.0.6 - 03-05-2025
## AGROMARKERS

### Objetivo

Gerencias os aspectos operacionais de um laboratório de bioteconologia, através de metodologia de gerenciamento de projetos, principalmente para controle e rastreabilidade de amostras durante as diversas fases do projeto.


### Funcionalidades. 

* Criação de Projetos.
* Criação automática das placas 96 referentes ao projeto.
* Criação das amostras.
* Alocação das amostras nos respectivos poços das placas 96. 
* Envio de amostras ao laboratório. (des)
* Recepção de amostras no laboratório. (des)
* Evolução das fases dentro do laboratório. (des)
* Criação em lote das placas 384. 
* Carga de resultados via relatório Pherastar 1536 (des)
* Carga de resultados via relatório Pherastar 384 (des)
* Carga de resultados via relatório QuantumStudio 384 (des)


### Release: V.1.0.7 (Em desenvolvimento)

*   **Planejamento:** Veja as [Issues abertas](https://github.com/jsoj/sgl_dev/issues?q=is%3Aopen+is%3Aissue) para detalhes sobre o que está sendo trabalhado.
*   Carga automática de resultados
    *   Implementação de importação automática do Pherastar 1536
    *   Implementação de importação automática do Pherastar 384
    *   Implementação de importação automática do QuantumStudio 384
*   Frontend:
    *   Consulta Projetos.
    *   Tela de criação automática de placas 1536.
    *   Tela para subir resultados brutos.
    *   Tela para tratar resulados brutos.
    *   Lista de resultados com importação e exportação.

### Release: V.1.0.6 - 01/05/2025 
* Backend:
 - Importação automatica de Pherastar 1536 e 384 versão beta. 
* Frontend:
  - Nova tela de entrada de projeto
  - Tela de criação automática de placas 384.
  - Lista de Projetos.
  - PDF de Projeto


### Release: V.1.0.5 - 01/04/2025 

* Criamos a interface do usuário fora do contexto do admin.
* Tela de criação de projetos. 
* Lista de projetos. 
* Tela de criação de placas 384 em lote


### Release: V.1.0. - 01/03/2025 

* Cadastros:
  - Empresa
  - Projeto
  - Placas
  - Amostras
  - Poços 
  - Tecnologia
  - Traits e Marcadores


## Tecnologias

- Python
- Django
- Outras tecnologias...

