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

## Resultados 384

* Ja temos uma funcao via admin para subir arquivos e tratar os resultados via Pherastar 1536.
* Falta:
  * Criar processo para subir arquivo Pherastar 384
  * Criar processo para subir arquivo QuantunStudio 384
  * Criar um serviço para tratar os arquivos.
  * Criar um modelo a exemplo ResultadoAmostra para receber os resultados de relatorios 384 ResultadoAmostra384.


### Normalização dos dados passo a passo:

* Encontrar o tabela de dados apos a tag "Data".
* Identificar o cabecalho e inicio dos dados.
* remover colunas que nao sao de interesse:
  ```
  colunas_remover = ['DaughterPlate', 'SNPID', 'SubjectID']
  ```
* renomear as colunas restantes:
  ```
  mapeamento_colunas = {
  'MasterPlate': 'Placa_384',
  'MasterWell': 'Poco_Placa_384',
  'Call': 'Resultado'
  }
  ```
  * Substituir "_" por "-" e " " por "-" na coluna Placa_384 e colocar tudo em upercase
  * Crias as colunas Teste e Projeto a Partir da coluna Placa_384.
    * Projeto são os primeiros caracteres até o primeiro hifen. 
    * Teste são os ultioms caracteres apos o hifen. 
  * Garantir que após do primeiro hifen tenhamos 3 caracteres, preenchendo com zeros a esquerda quando necessário.
  * Garatnir que após o segundo hifem tenhamos 3 caracteres, preenchendo com zeros a esquerda quanod necessario. 
  * Criar a coluna 'chave' combinando Placa_384 e Poco_Placa_384
  * Após criar a coluna 'chave', agora podemos remover a informação do teste da coluna Placa_384
  * Normalização final: remover a informação do projeto da coluna Placa_384
  * Mapeamento da coluna resultado:
  ```
   RESULTADO_MAPPING = {
                'X:X': 'POS:POS',
                'Y:Y': 'NEG:NEG',
                'X:Y': 'POS:NEG',
                'Y:X': 'POS:NEG',
                'NTC': 'NTC',
                '?': 'FAIL',
                'Heterozygous NEG/POS': 'NEG:POS',
                'Homozygous NEG/NEG': 'NEG:NEG',
                'Homozygous POS/POS': 'POS:POS',
                'Negative Control (NC)': 'NTC',
                'Undetermined': 'FAIL',
            }
    ```

### Processamento e arquivo

* Após normalização vamos salvar os arquivos em um banco de dados onde temos apenas uma chave estrageira que seria o upload.  

### Passos
* crir modelo de upload.
* atualizar servico de processamento dos arquivos 384 e processar o arquivo. 
* salvar informações do upload em um modelo adequado




#### codigo de apoio

import pandas as pd
import numpy as np
import re

def processar_arquivo_genotipagem(caminho_arquivo, encoding='utf-8', sep=','):
    """
    Processa o arquivo de genotipagem executando todos os passos necessários.
    
    Args:
        caminho_arquivo (str): Caminho completo para o arquivo CSV
        encoding (str): Codificação do arquivo (padrão: 'utf-8')
        sep (str): Separador de colunas (padrão: ',')
        
    Returns:
        pandas.DataFrame: DataFrame final processado
    """
    try:
        # Passo 1 e 2: Carregar o arquivo CSV e encontrar onde os dados tabulares começam
        print("Passo 1 e 2: Carregando arquivo e identificando dados tabulares...")
        with open(caminho_arquivo, 'r', encoding=encoding) as file:
            linhas = file.readlines()
        
        # Procurar pelo início dos dados tabulares após a seção "Data"
        indice_cabecalho = -1
        for i, linha in enumerate(linhas):
            if linha.strip() == "Data":
                indice_cabecalho = i + 1  # O cabeçalho está na próxima linha após "Data"
                break
        
        if indice_cabecalho == -1:
            print("Não foi possível identificar a seção 'Data' no arquivo")
            return None
        
        # Passo 3: Transformar os dados tabulares em DataFrame
        print("Passo 3: Transformando dados em DataFrame...")
        df = pd.read_csv(
            caminho_arquivo, 
            encoding=encoding, 
            sep=sep, 
            skiprows=indice_cabecalho,
            header=0
        )
        
        print(f"Arquivo '{caminho_arquivo}' carregado com sucesso!")
        print(f"Cabeçalhos originais: {list(df.columns)}")
        
        # Passo 4: Apagar as colunas que não são de interesse
        print("Passo 4: Removendo colunas que não são de interesse...")
        colunas_remover = ['DaughterPlate', 'SNPID', 'SubjectID']
        colunas_existentes_para_remover = [col for col in colunas_remover if col in df.columns]
        
        if colunas_existentes_para_remover:
            df.drop(columns=colunas_existentes_para_remover, inplace=True)
            print(f"Colunas removidas: {colunas_existentes_para_remover}")
        
        # Verificar se há colunas que não existiam para remover
        colunas_inexistentes = set(colunas_remover) - set(colunas_existentes_para_remover)
        if colunas_inexistentes:
            print(f"Atenção: As seguintes colunas não foram encontradas para remoção: {colunas_inexistentes}")
        
        print(f"Cabeçalhos após remoção: {list(df.columns)}")
        
        # Passo 5: Renomear as colunas de interesse
        print("Passo 5: Renomeando colunas...")
        mapeamento_colunas = {
            'MasterPlate': 'Placa_384',
            'MasterWell': 'Poco_Placa_384',
            'Call': 'Resultado'
        }
        
        # Verificar quais colunas do mapeamento existem no DataFrame
        colunas_para_renomear = {col_orig: col_nova for col_orig, col_nova in mapeamento_colunas.items() 
                                if col_orig in df.columns}
        
        if colunas_para_renomear:
            df.rename(columns=colunas_para_renomear, inplace=True)
            print(f"Colunas renomeadas: {colunas_para_renomear}")
        
        # Verificar se há colunas que não existiam para renomear
        colunas_inexistentes_renomear = set(mapeamento_colunas.keys()) - set(colunas_para_renomear.keys())
        if colunas_inexistentes_renomear:
            print(f"Atenção: As seguintes colunas não foram encontradas para renomeação: {colunas_inexistentes_renomear}")
        
        print(f"Cabeçalhos após renomeação: {list(df.columns)}")
        
        # Normalização 1 da coluna Placa_384: substituições básicas e uppercase
        print("Normalização 1 da coluna Placa_384: substituições básicas e uppercase...")
        if 'Placa_384' in df.columns:
            # Guardar valores únicos antes da transformação para comparação
            valores_unicos_antes = df['Placa_384'].unique()
            
            # Aplicar transformações: substituir _ por -, substituir espaço por -, converter para maiúsculas
            df['Placa_384'] = df['Placa_384'].astype(str).apply(
                lambda x: x.replace('_', '-').replace(' ', '-').upper()
            )
            
            # Obter valores únicos após a transformação
            valores_unicos_depois = df['Placa_384'].unique()
            
            print("Valores únicos antes da normalização 1:")
            for valor in valores_unicos_antes[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_antes) > 5:
                print(f"  - ... e mais {len(valores_unicos_antes) - 5} valores")
                
            print("Valores únicos após a normalização 1:")
            for valor in valores_unicos_depois[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_depois) > 5:
                print(f"  - ... e mais {len(valores_unicos_depois) - 5} valores")
        else:
            print("Atenção: Coluna 'Placa_384' não encontrada para normalização")
            
        # Extrair o valor para as novas colunas 'Teste' e 'Projeto' APÓS a normalização inicial
        print("Criando as colunas 'Teste' e 'Projeto'...")
        if 'Placa_384' in df.columns:
            # Extrair a parte após o último hífen para a coluna 'Teste'
            df['Teste'] = df['Placa_384'].astype(str).apply(
                lambda x: x.split('-')[-1].upper()  # Pega a última parte após o hífen e converte para maiúsculas
            )
            
            # Extrair a parte até o primeiro hífen para a coluna 'Projeto'
            df['Projeto'] = df['Placa_384'].astype(str).apply(
                lambda x: x.split('-')[0].upper()  # Pega a primeira parte antes do primeiro hífen
            )
            
            # Obter valores únicos da coluna 'Teste'
            valores_unicos_teste = df['Teste'].unique()
            
            print("Valores únicos da coluna 'Teste':")
            for valor in valores_unicos_teste[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_teste) > 5:
                print(f"  - ... e mais {len(valores_unicos_teste) - 5} valores")
                
            # Obter valores únicos da coluna 'Projeto'
            valores_unicos_projeto = df['Projeto'].unique()
            
            print("Valores únicos da coluna 'Projeto':")
            for valor in valores_unicos_projeto[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_projeto) > 5:
                print(f"  - ... e mais {len(valores_unicos_projeto) - 5} valores")
        else:
            print("Atenção: Coluna 'Placa_384' não encontrada para criar as colunas 'Teste' e 'Projeto'")
        
        # Normalização 2 da coluna Placa_384: garantir 3 caracteres entre os hifens
        print("Normalização 2 da coluna Placa_384: garantir 3 caracteres entre os hifens...")
        if 'Placa_384' in df.columns:
            # Função para normalizar uma string conforme a regra (3 caracteres entre hifens)
            def normalizar_formato(valor):
                partes = valor.split('-')
                if len(partes) >= 3:  # Certifique-se de que há pelo menos 3 partes
                    # Ajustar a primeira parte (se necessário)
                    partes[0] = partes[0]  # A primeira parte não tem requisitos de comprimento
                    
                    # Ajustar a segunda parte (3 caracteres)
                    partes[1] = partes[1].zfill(3)  # Preenche com zeros à esquerda até ter 3 caracteres
                    
                    # Ajustar a terceira parte (3 caracteres)
                    partes[2] = partes[2].zfill(3)  # Preenche com zeros à esquerda até ter 3 caracteres
                    
                    # Reconstruir a string
                    return '-'.join(partes)
                return valor  # Se não tiver 3 partes, retorna o valor original
            
            # Guardar valores únicos antes da transformação para comparação
            valores_unicos_antes = df['Placa_384'].unique()
            
            # Aplicar a normalização
            df['Placa_384'] = df['Placa_384'].apply(normalizar_formato)
            
            # Obter valores únicos após a transformação
            valores_unicos_depois = df['Placa_384'].unique()
            
            print("Valores únicos antes da normalização 2:")
            for valor in valores_unicos_antes[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_antes) > 5:
                print(f"  - ... e mais {len(valores_unicos_antes) - 5} valores")
                
            print("Valores únicos após a normalização 2:")
            for valor in valores_unicos_depois[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_depois) > 5:
                print(f"  - ... e mais {len(valores_unicos_depois) - 5} valores")
        else:
            print("Atenção: Coluna 'Placa_384' não encontrada para normalização")
        
        # Criar a coluna 'chave' combinando Placa_384 e Poco_Placa_384
        # Importante: Fazemos isso ANTES de remover a informação do teste da coluna Placa_384
        print("Criando a coluna 'chave'...")
        if 'Placa_384' in df.columns and 'Poco_Placa_384' in df.columns:
            # Criar a coluna 'chave' concatenando Placa_384, hífen e Poco_Placa_384
            df['chave'] = df['Placa_384'] + '-' + df['Poco_Placa_384']
            
            # Mostrar alguns exemplos da coluna 'chave' criada
            print("Exemplos da coluna 'chave':")
            for i, chave in enumerate(df['chave'].head(5)):
                placa = df['Placa_384'].iloc[i]
                poco = df['Poco_Placa_384'].iloc[i]
                print(f"  - Placa_384: {placa}, Poco_Placa_384: {poco} → chave: {chave}")
        else:
            colunas_faltantes = []
            if 'Placa_384' not in df.columns:
                colunas_faltantes.append('Placa_384')
            if 'Poco_Placa_384' not in df.columns:
                colunas_faltantes.append('Poco_Placa_384')
            print(f"Atenção: As seguintes colunas necessárias não foram encontradas: {colunas_faltantes}")
        
        # Após criar a coluna 'chave', agora podemos remover a informação do teste da coluna Placa_384
        print("Removendo a informação do teste da coluna Placa_384...")
        if 'Placa_384' in df.columns:
            # Guardar valores únicos antes da transformação para comparação
            valores_unicos_antes = df['Placa_384'].unique()
            
            # Função para remover a parte do teste (tudo após o último hífen)
            def remover_teste(valor):
                partes = valor.split('-')
                if len(partes) > 1:  # Certifique-se de que há pelo menos 2 partes (pelo menos um hífen)
                    # Juntar todas as partes exceto a última
                    return '-'.join(partes[:-1])
                return valor  # Se não tiver hífen, retorna o valor original
            
            # Aplicar a remoção do teste
            df['Placa_384'] = df['Placa_384'].apply(remover_teste)
            
            # Obter valores únicos após a transformação
            valores_unicos_depois = df['Placa_384'].unique()
            
            print("Valores únicos antes da remoção do teste:")
            for valor in valores_unicos_antes[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_antes) > 5:
                print(f"  - ... e mais {len(valores_unicos_antes) - 5} valores")
                
            print("Valores únicos após a remoção do teste:")
            for valor in valores_unicos_depois[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_depois) > 5:
                print(f"  - ... e mais {len(valores_unicos_depois) - 5} valores")
        else:
            print("Atenção: Coluna 'Placa_384' não encontrada para remoção da informação do teste")
            
        # Normalização final: remover a informação do projeto da coluna Placa_384
        print("Normalização final: removendo a informação do projeto da coluna Placa_384...")
        if 'Placa_384' in df.columns:
            # Guardar valores únicos antes da transformação para comparação
            valores_unicos_antes = df['Placa_384'].unique()
            
            # Função para remover a parte do projeto (tudo antes do primeiro hífen)
            def remover_projeto(valor):
                partes = valor.split('-')
                if len(partes) > 1:  # Certifique-se de que há pelo menos 2 partes (pelo menos um hífen)
                    # Juntar todas as partes exceto a primeira (ignorar o projeto)
                    return '-'.join(partes[1:])
                return valor  # Se não tiver hífen, retorna o valor original
            
            # Aplicar a remoção do projeto
            df['Placa_384'] = df['Placa_384'].apply(remover_projeto)
            
            # Obter valores únicos após a transformação
            valores_unicos_depois = df['Placa_384'].unique()
            
            print("Valores únicos antes da remoção do projeto:")
            for valor in valores_unicos_antes[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_antes) > 5:
                print(f"  - ... e mais {len(valores_unicos_antes) - 5} valores")
                
            print("Valores únicos após a remoção do projeto:")
            for valor in valores_unicos_depois[:5]:  # Mostrar apenas os 5 primeiros para não poluir o output
                print(f"  - {valor}")
            if len(valores_unicos_depois) > 5:
                print(f"  - ... e mais {len(valores_unicos_depois) - 5} valores")
        else:
            print("Atenção: Coluna 'Placa_384' não encontrada para remoção da informação do projeto")
            
        # Normalização da coluna Resultado: mapear valores para o formato desejado
        print("Normalizando a coluna Resultado...")
        if 'Resultado' in df.columns:
            # Definir o mapeamento de resultados
            RESULTADO_MAPPING = {
                'X:X': 'POS:POS',
                'Y:Y': 'NEG:NEG',
                'X:Y': 'POS:NEG',
                'Y:X': 'POS:NEG',
                'NTC': 'NTC',
                '?': '-',
                'Heterozygous NEG/POS': 'NEG:POS',
                'Homozygous NEG/NEG': 'NEG:NEG',
                'Homozygous POS/POS': 'POS:POS',
                'Negative Control (NC)': 'NTC',
                'Undetermined': '-',
            }
            
            # Guardar valores únicos antes da transformação
            valores_unicos_antes = df['Resultado'].unique()
            
            # Aplicar o mapeamento (caso o valor não esteja no mapeamento, mantém o original)
            df['Resultado'] = df['Resultado'].map(lambda x: RESULTADO_MAPPING.get(x, x))
            
            # Obter valores únicos após a transformação
            valores_unicos_depois = df['Resultado'].unique()
            
            print("Valores únicos da coluna Resultado antes da normalização:")
            for valor in valores_unicos_antes:
                print(f"  - {valor}")
                
            print("Valores únicos da coluna Resultado após a normalização:")
            for valor in valores_unicos_depois:
                print(f"  - {valor}")
            
            # Verificar se algum valor não foi mapeado
            valores_nao_mapeados = [valor for valor in valores_unicos_depois if valor not in RESULTADO_MAPPING.values()]
            if valores_nao_mapeados:
                print("Atenção: Os seguintes valores não foram mapeados:")
                for valor in valores_nao_mapeados:
                    if valor not in RESULTADO_MAPPING.keys():  # Não mostrar valores que já estão nas chaves do mapeamento
                        print(f"  - {valor}")
        else:
            print("Atenção: Coluna 'Resultado' não encontrada para normalização")
        
        # Continuar com os próximos passos conforme necessário
        # Passo 6: Fazer split de uma determinada coluna
        # Passo 7: Renomear as novas colunas
        # etc...
        
        # Salvar o DataFrame processado como arquivo Excel
        print("\nSalvando o DataFrame processado como arquivo Excel...")
        try:
            # Criar o nome do arquivo de saída baseado no arquivo de entrada
            nome_arquivo_saida = caminho_arquivo.replace('.csv', '_processado.xlsx')
            
            # Salvar como Excel
            df.to_excel(nome_arquivo_saida, index=False)
            print(f"Arquivo Excel salvo com sucesso: {nome_arquivo_saida}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo Excel: {e}")
            print("Dica: verifique se a biblioteca 'openpyxl' está instalada. Você pode instalá-la com 'pip install openpyxl'")
            
            # Tentar salvar como CSV caso a exportação para Excel falhe
            try:
                nome_arquivo_csv = caminho_arquivo.replace('.csv', '_processado.csv')
                df.to_csv(nome_arquivo_csv, index=False)
                print(f"Como alternativa, o arquivo foi salvo em formato CSV: {nome_arquivo_csv}")
            except Exception as csv_err:
                print(f"Erro ao salvar como CSV: {csv_err}")
        
        return df
        
    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        return None

# Exemplo de uso
df_processado = processar_arquivo_genotipagem('genotyping_results-070.csv')


