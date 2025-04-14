# Especificacao funcional do SGL

## Acesso

* Um usuário só pode acessar informações referentes a empresa a qual esta associado.
* somente o admin pode acessar todos as empresas e todos os dados.

## Projeto

* A criação do projeto automaticamente:
  * cria as amostras do projeto.
  * cria as quantidades de placa 96 poços com 90 posições uteis dependendo do número de amostras informados no projeto.
  * crias os poços referente as placas e amostras.
  * gera um template em pdf com o esquema visual de organização das amostras na placa
  * gera um relatorio pdf sobre o projeto criado.
  * envia os dois arquivos pdf para o e-mail informado.

## Poços de Controle

Os poços de controle são: A01, B01, C01, D01, E01 e F01. Exceto para a BASF

Entao temos 90 poços uteis em cada placa 96.

## Criar placas 384 em lote.

### Passos

* Escolher empresa.
* Escolher projetos ativos e com placas 96 ativas relacionados aquela empresa.
* Escolher quais placas 96 serão usadas para criar as placas 384.
* Dividir o número de placas 96 por 4 para determinar a quantidade de placas 384 devem ser criadas.
* Criar as placas 384 utilizando-se das placas 96 escolhidas.
  * Criar os poços de cada placa 384 criadas.
  * Criar o mapeamento de cada placa 96 para 384 criada.

#### Detalhamento

* Ao menos uma placa 96 deve ser escolhida para se criar uma placa 384.
* Cada placa 384 contém até 04 placas 96.
* A cada 04 placas 96 deve ser criada 01 ṕlaca 384, com seu mapeamento e seus poços.
* A ordem da utilização das placas 96 escolhidas é sempre crescente.
* A organização das amostras nos poços segue o padrão já utilizado no processo individual.
  * prenchimento em Z.
* A placa 96 utilizada deve ser inativada para nao participar mais em transferencia futuras.
* O nome da placa 384 deve ser composto pela identifica da primeira placa 96 e da quarta placa 96.
  * usar 03 ultimos digitos da primeira placa 96 + "-" + 03 ultimos digitos da ultima placa 96 que compoe a placa 384, conforme exemplo abaixo.

| placa 96 01 | Placa 96 02 | Placa 96 03 | Placa 96 04 | Nome da Placa 384 criada |
| ----------- | ----------- | ----------- | ----------- | ------------------------ |
| 001         | 002         | 003         | 004         | 001-004                  |
| 005         | 006         | 007         | 008         | 005-008                  |
| 009         | 010         | 011         | 012         | 009-012                  |
| 013         | 014         | 015         | 016         | 013-016                  |

* Devem ser criadas tantas placas 384 quanto necessário para atender as placas 96 selecionadas.
* Placas 96 nao selecionadas devem ficar ativas e serem usadas em futuras transferências.
* Durante o processo de criação de cada 384 é necessário gerar os poços e mapeamentos das placas 96 para a placa 384.
* O Usuário deve ser informado a cada placa 384 processada com sucesso.
* O usuário deve selecionar ao menos uma placa 96 para poder criar uma placa 384.
