from app.models import ResultadoAmostra1536, ResultadoUpload1536, Amostra, Placa384, Poco384
import pandas as pd
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, Any, Optional
import traceback
from app.models import ResultadoAmostra384, ResultadoUpload384, Amostra, Placa384, Poco384
import numpy as np
import re
import datetime
from django.utils import timezone

# Configuração de logging
logger = logging.getLogger(__name__)

class ResultadoProcessor1536:
    """Serviço para processar arquivos de resultado e criar registros no banco"""
    
    # Mapeamento de resultados para formato legível
    RESULTADO_MAPPING = {
        'X:X': 'POS:POS',
        'Y:Y': 'NEG:NEG',
        'X:Y': 'POS:NEG',
        'Y:X': 'POS:NEG',
        'NTC': 'NTC',
        '?': '-'
    }
    
    def __init__(self, upload_id: int):
        try:
            self.upload = ResultadoUpload1536.objects.get(id=upload_id)
            self.projeto = self.upload.projeto
            self.placa_1536 = self.upload.placa_1536
            logger.info(f"Inicializando ResultadoProcessor para upload_id={upload_id}")
            logger.info(f"Projeto: {self.projeto.codigo_projeto}")
            logger.info(f"Placa 1536: {self.placa_1536.codigo_placa}")
        except Exception as e:
            logger.error(f"Erro na inicialização do ResultadoProcessor: {str(e)}")
            logger.error(traceback.format_exc())

    
    def converter_resultado(self, resultado: str) -> str:
        """
        Converte o resultado do formato original para o formato legível por humanos
        
        Args:
            resultado: Resultado no formato original (X:X, Y:Y, etc)
            
        Returns:
            str: Resultado convertido para formato legível (POS/POS, NEG/NEG, etc)
        """
        return self.RESULTADO_MAPPING.get(resultado, resultado)
    
    def find_header_row(self, file_path: str) -> int:
        """
        Encontra a linha que contém o cabeçalho específico
        """
        HEADER_LINE = "DaughterPlate,MasterPlate,MasterWell,Call,X,Y,SNPID,SubjectID"
        
        with open(file_path, 'r') as file:
            for idx, line in enumerate(file):
                if HEADER_LINE in line:
                    logger.info(f"Cabeçalho encontrado na linha {idx}")
                    return idx
        
        raise ValidationError("Não foi possível encontrar a linha de cabeçalho no arquivo")
    
    def process_file(self) -> Dict[str, Any]:
        """
        Processa o arquivo CSV linha por linha
        """
        try:
            logger.info(f"Iniciando processamento do arquivo: {self.upload.arquivo.path}")
            
            # Encontra a linha do cabeçalho
            header_row = self.find_header_row(self.upload.arquivo.path)
            logger.info(f"Linha do cabeçalho: {header_row}")
            
            # Lê o arquivo
            df = pd.read_csv(
                self.upload.arquivo.path,
                delimiter=',',
                skiprows=header_row,
                encoding='utf-8'
            )
            logger.info(f"DataFrame info:")
            logger.info(f"Colunas: {df.columns.tolist()}")
            logger.info(f"Tipos de dados:\n{df.dtypes}")
            logger.info(f"Valores únicos em 'Call': {df['Call'].unique()}")        
            logger.info(f"Arquivo lido com sucesso. Shape: {df.shape}")
            logger.info(f"Colunas encontradas: {df.columns.tolist()}")
            
            # Inicializa estatísticas
            stats = {
                'total_rows': 0,
                'processed': 0,
                'errors': 0
            }
            
            # Processamento direto, sem batch
            for idx, row in df.iterrows():
                try:
                    stats['total_rows'] += 1
                    
                    # Extrair dados básicos
                    plate = str(row['DaughterPlate'])
                    well = str(row['MasterWell'])
                    call = str(row['Call'])
                    
                    # Converter o resultado para formato legível
                    call_convertido = self.converter_resultado(call)
                    
                    # Converter coordenadas
                    try:
                        x_coord = float(row['X'])
                        y_coord = float(row['Y'])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Erro ao converter coordenadas X/Y para linha {idx}: {str(e)}")
                        stats['errors'] += 1
                        continue
                    
                    # Identificar tipo de resultado
                    is_fh = 'FH' in plate.upper()
                    is_aj = 'AJ' in plate.upper()
                    
                    if not (is_fh or is_aj):
                        logger.warning(f"Tipo de resultado não identificado para placa {plate}")
                        stats['errors'] += 1
                        continue
                    
                    # Buscar amostra
                    poco = self.placa_1536.poco1536_set.filter(
                        posicao=well
                    ).select_related('amostra').first()
                    
                    if not poco:
                        logger.warning(f"Poço {well} não encontrado na placa {self.placa_1536.codigo_placa}")
                        stats['errors'] += 1
                        continue
                    
                    # Criar ou atualizar resultado
                    with transaction.atomic():
                        resultado, _ = ResultadoAmostra.objects.get_or_create(
                            upload=self.upload,
                            amostra=poco.amostra,
                            empresa=self.upload.empresa
                        )
                        
                        # Atualizar resultado baseado no tipo (FH ou AJ)
                        if is_fh:
                            resultado.resultado_fh = call_convertido  # Usando o resultado convertido
                            resultado.coordenada_x_fh = x_coord
                            resultado.coordenada_y_fh = y_coord
                        
                        if is_aj:
                            resultado.resultado_aj = call_convertido  # Usando o resultado convertido
                            resultado.coordenada_x_aj = x_coord
                            resultado.coordenada_y_aj = y_coord
                        
                        resultado.save()
                        stats['processed'] += 1
                
                except Exception as e:
                    logger.error(f"Erro ao processar linha {idx}")
                    logger.error(f"Dados da linha: {row.to_dict()}")
                    logger.error(f"Erro: {str(e)}")
                    logger.error(traceback.format_exc())
                    stats['errors'] += 1
            
            # Marca como processado se teve sucesso
            if stats['processed'] > 0:
                self.upload.processado = True
                self.upload.save()
                logger.info("Upload marcado como processado")
            else:
                logger.warning("Nenhuma linha processada com sucesso")
            
            logger.info(f"Processamento concluído. Estatísticas: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Erro crítico durante processamento: {str(e)}")
            logger.error(traceback.format_exc())
            raise


import pandas as pd
import logging
import traceback
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)

def process_upload(upload_id):
    """
    Processa um arquivo de resultado 384 e salva os dados no banco
   
    Args:
        upload_id: ID do upload a ser processado
       
    Returns:
        dict: Estatísticas de processamento
    """
    try:
        stats = processar_arquivo_384(upload_id)
        logger.info(f"Processamento de upload 384 concluído com sucesso: {stats}")
        return stats
    except ValidationError as e:
        logger.error(f"Erro no processamento: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no processamento: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValidationError(f"Erro no processamento: {str(e)}")

def garantir_valor_seguro(valor, tipo='str', padrao='', max_length=None, fill_digits=None):
    """
    Garante que um valor é seguro para salvar no banco de dados.
    Opcionalmente, limita o tamanho de strings para evitar erros de comprimento
    ou preenche com zeros à esquerda.
   
    Args:
        valor: O valor a ser processado
        tipo: O tipo desejado ('str', 'float', 'codigo')
        padrao: Valor padrão caso o valor seja None
        max_length: Tamanho máximo para strings (se None, não limita)
        fill_digits: Número de dígitos para preencher com zeros à esquerda (se None, não preenche)
   
    Returns:
        Valor processado de acordo com as regras
    """
    if valor is None:
        resultado = padrao
    elif tipo == 'str' or tipo == 'codigo':
        resultado = str(valor)
    elif tipo == 'float':
        try:
            return float(valor)
        except (ValueError, TypeError):
            return float(padrao) if padrao else 0.0
    else:
        resultado = valor
    
    # Para strings e códigos
    if tipo == 'str' or tipo == 'codigo':
        # Preencher com zeros à esquerda se necessário
        if fill_digits is not None:
            resultado = resultado.zfill(fill_digits)
            
        # Limitar tamanho se necessário
        if max_length is not None and len(resultado) > max_length:
            logger.warning(f"Valor '{resultado}' truncado para {max_length} caracteres")
            resultado = resultado[:max_length]
            
    return resultado

def processar_arquivo_384(arquivo_upload_id):
    """
    Processa um arquivo de genotipagem com cabeçalho padronizado na primeira linha
    e salva os resultados no banco de dados.
    """
    logger.info(f"=== INICIANDO PROCESSAMENTO DO ARQUIVO ID: {arquivo_upload_id} ===")
    try:
        # Recuperar o objeto de upload
        from app.models import ResultadoUpload384, ResultadoAmostra384, Empresa
       
        arquivo_upload = ResultadoUpload384.objects.get(id=arquivo_upload_id, processado=False)
       
        # Obter o código da empresa
        if arquivo_upload.empresa_codigo:
            codigo_empresa = arquivo_upload.empresa_codigo
            logger.info(f"Código da empresa obtido do campo empresa_codigo: {codigo_empresa}")
        elif hasattr(arquivo_upload, 'empresa') and arquivo_upload.empresa:
            codigo_empresa = arquivo_upload.empresa.codigo
            logger.info(f"Código da empresa obtido do relacionamento: {codigo_empresa}")
           
            # Atualizar os campos no upload para usos futuros
            arquivo_upload.empresa_codigo = codigo_empresa
            arquivo_upload.empresa_nome = arquivo_upload.empresa.nome
            arquivo_upload.save(update_fields=['empresa_codigo', 'empresa_nome'])
            logger.info(f"Campos de empresa atualizados no upload")
        else:
            codigo_empresa = '001'  # Valor padrão
            logger.warning(f"Usando código de empresa padrão: {codigo_empresa}")
           
        # Garantir que o código da empresa seja string e tenha 3 dígitos
        codigo_empresa = str(codigo_empresa).zfill(3)
        logger.info(f"Código da empresa formatado para uso: {codigo_empresa}")
       
        logger.info(f"Arquivo encontrado: {arquivo_upload.arquivo.path}")
        
        # Ler o arquivo com o cabeçalho padronizado
        df = ler_arquivo_padronizado(arquivo_upload.arquivo.path)
        logger.info(f"DataFrame criado com {len(df)} linhas")
        
        # Validações de cabeçalho e conteúdo
        validar_colunas_obrigatorias(df)
        validar_empresa_projeto(df, codigo_empresa, arquivo_upload.projeto.codigo_projeto)
        
        # Normalizar os dados
        df = normalizar_dados(df)
        
        # Salvar os resultados no banco de dados
        contador = 0
        registros_criados = 0
        registros_duplicados = 0
        erros_registro = 0
       
        # Processar linha por linha
        for _, row in df.iterrows():
            try:
                # Criar cada registro em sua própria transação
                with transaction.atomic():
                    # Extrair e preparar dados
                    # Usar o código da empresa do arquivo se existir, senão usar o do upload
                    if 'empresa' in row and row['empresa'] is not None:
                        # Extrair do arquivo e garantir formato correto
                        empresa = garantir_valor_seguro(row['empresa'], tipo='codigo', fill_digits=3, max_length=3)
                        logger.info(f"Usando código de empresa do arquivo: {row['empresa']} -> {empresa}")
                    else:
                        # Usar o código obtido no início do processamento
                        empresa = garantir_valor_seguro(codigo_empresa, tipo='codigo', fill_digits=3, max_length=3)
                        logger.info(f"Usando código de empresa do upload: {codigo_empresa} -> {empresa}")
                        
                    projeto = garantir_valor_seguro(row.get('projeto', ''), max_length=20)
                    placa = garantir_valor_seguro(row.get('placa', ''), max_length=20)
                    poco = garantir_valor_seguro(row.get('poco', ''), max_length=4)
                    teste = garantir_valor_seguro(row.get('teste', ''), max_length=20)
                    resultado = garantir_valor_seguro(row.get('resultado', ''), max_length=10)
                    x = garantir_valor_seguro(row.get('x', 0), tipo='float', padrao='0')
                    y = garantir_valor_seguro(row.get('y', 0), tipo='float', padrao='0')
                    
                    # Criar chave única
                    chave = f"{empresa}-{projeto}-{placa}-{poco}-{teste}"
                   
                    # Verificar se o registro já existe
                    registro_existente = ResultadoAmostra384.objects.filter(
                        chave=chave
                    ).exists()
                   
                    if registro_existente:
                        registros_duplicados += 1
                        continue
                   
                    # Se não existe, criar um novo
                    ResultadoAmostra384.objects.create(
                        arquivo_upload=arquivo_upload,
                        empresa=empresa,
                        projeto=projeto,
                        placa_384=placa,
                        poco_placa_384=poco,
                        teste=teste,
                        resultado=resultado,
                        x=x,
                        y=y,
                        chave=chave
                    )
                    registros_criados += 1
            except Exception as e:
                erros_registro += 1
                logger.error(f"Erro ao processar linha {contador}: {str(e)}")
                # Continuar mesmo com erro
               
            contador += 1
            if contador % 1000 == 0:
                logger.info(f"Processados {contador} registros")
       
        # Ao concluir, marcar o arquivo como processado em uma transação separada
        with transaction.atomic():
            arquivo_upload.processado = True
            arquivo_upload.data_processamento = timezone.now()
            arquivo_upload.save()
           
        # Estatísticas finais
        stats = {
            'total_registros': len(df),
            'registros_criados': registros_criados,
            'registros_duplicados': registros_duplicados,
            'erros_registro': erros_registro,
            'testes_encontrados': df['teste'].unique().tolist() if 'teste' in df else [],
            'projetos_encontrados': df['projeto'].unique().tolist() if 'projeto' in df else [],
        }
       
        logger.info(f"Processamento concluído. Estatísticas: {stats}")
        return stats
       
    except Exception as e:
        logger.exception(f"Erro durante o processamento do arquivo: {str(e)}")
        raise

def ler_arquivo_padronizado(caminho_arquivo):
    """
    Lê o arquivo CSV/Excel com cabeçalho padronizado na primeira linha.
    """
    try:
        # Detectar tipo de arquivo pelo nome
        if caminho_arquivo.endswith('.csv'):
            # Tentar várias codificações e separadores comuns
            try:
                df = pd.read_csv(caminho_arquivo, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(caminho_arquivo, encoding='latin1')
                except:
                    # Se falhar com ; como separador
                    try:
                        df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8')
                    except:
                        df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1')
        else:
            # Arquivo Excel
            df = pd.read_excel(caminho_arquivo)
        
        # Normalizar nomes das colunas (minúsculas e sem espaços)
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Log das colunas encontradas
        logger.info(f"Arquivo carregado com sucesso. Colunas encontradas: {', '.join(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.exception(f"Erro ao ler o arquivo: {str(e)}")
        logger.info(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Erro ao ler o arquivo: {str(e)}")

def validar_colunas_obrigatorias(df):
    """
    Verifica se todas as colunas obrigatórias estão presentes no DataFrame.
    """
    colunas_obrigatorias = ['empresa', 'projeto', 'placa', 'poco', 'teste', 'resultado', 'x', 'y']
    colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
    
    if colunas_faltantes:
        mensagem = f"Colunas obrigatórias faltando no arquivo: {', '.join(colunas_faltantes)}"
        logger.error(mensagem)
        raise ValidationError(mensagem)
    
    return True

def validar_empresa_projeto(df, codigo_empresa_upload, codigo_projeto_upload):
    """
    Valida se os códigos de empresa e projeto no arquivo correspondem aos informados no upload
    e se existe apenas um código de cada no arquivo.
    """
    # Verificar código da empresa
    if 'empresa' in df.columns:
        # Garantir que todos os valores de empresa sejam strings
        df['empresa'] = df['empresa'].astype(str)
        
        # Formatar os códigos de empresa para terem 3 dígitos
        df['empresa'] = df['empresa'].apply(lambda x: x.zfill(3))
        
        empresas_unicas = df['empresa'].unique()
        
        if len(empresas_unicas) > 1:
            mensagem = f"Múltiplos códigos de empresa encontrados no arquivo: {', '.join(empresas_unicas)}"
            logger.error(mensagem)
            raise ValidationError(mensagem)
        
        # Formatar o código da empresa no upload para comparação
        codigo_empresa_formatado = str(codigo_empresa_upload).zfill(3)
        
        if len(empresas_unicas) == 1 and empresas_unicas[0] != codigo_empresa_formatado:
            mensagem = f"Código de empresa no arquivo ({empresas_unicas[0]}) difere do código informado no upload ({codigo_empresa_formatado})"
            logger.error(mensagem)
            raise ValidationError(mensagem)
    
    # Verificar código do projeto
    if 'projeto' in df.columns:
        # Garantir que todos os valores de projeto sejam strings
        df['projeto'] = df['projeto'].astype(str)
        
        projetos_unicos = df['projeto'].unique()
        
        if len(projetos_unicos) > 1:
            mensagem = f"Múltiplos códigos de projeto encontrados no arquivo: {', '.join(projetos_unicos)}"
            logger.error(mensagem)
            raise ValidationError(mensagem)
        
        if len(projetos_unicos) == 1 and str(projetos_unicos[0]) != str(codigo_projeto_upload):
            mensagem = f"Código de projeto no arquivo ({projetos_unicos[0]}) difere do código informado no upload ({codigo_projeto_upload})"
            logger.error(mensagem)
            raise ValidationError(mensagem)
    
    return True

def normalizar_dados(df):
    """
    Aplica as normalizações necessárias nos dados.
    """
    # Cria uma cópia para evitar o warning SettingWithCopyWarning
    df_norm = df.copy()
    
    # 0. Normalizar empresa - garantir que seja string e tenha 3 dígitos
    if 'empresa' in df_norm.columns:
        df_norm['empresa'] = df_norm['empresa'].astype(str).apply(lambda x: x.zfill(3))
    
    # 1. Normalizar campo placa
    if 'placa' in df_norm.columns:
        # Substituir _ por - e espaços por -
        df_norm['placa'] = df_norm['placa'].astype(str).apply(
            lambda x: x.replace('_', '-').replace(' ', '-')
        )
        
        # Extrair o "miolo" da placa - retirar o que estiver antes do primeiro
        # hífen e depois do último hífen
        df_norm['placa'] = df_norm['placa'].astype(str).apply(normalizar_formato_placa)
    
    # 2. Normalizar poço - adicionar zero quando necessário
    if 'poco' in df_norm.columns:
        df_norm['poco'] = df_norm['poco'].astype(str).apply(normalizar_poco)
    
    # 3. Normalizar resultado - mapear para valores legíveis
    if 'resultado' in df_norm.columns:
        df_norm['resultado'] = df_norm['resultado'].apply(mapear_resultado)
    
    # Log das normalizações para depuração
    logger.info(f"Dados normalizados. Exemplo de empresa: {df_norm['empresa'].iloc[0] if 'empresa' in df_norm.columns and len(df_norm) > 0 else 'N/A'}")
    
    return df_norm

def normalizar_formato_placa(valor):
    """
    Normaliza o formato da placa seguindo as regras:
    1. Remover o que estiver à esquerda do primeiro hífen (incluindo o hífen)
    2. Remover o que estiver à direita do último hífen (incluindo o hífen)
    3. Ajustar para que cada parte tenha 3 caracteres
    """
    try:
        partes = valor.split('-')
        
        if len(partes) < 2:
            return valor
        
        # Remove o primeiro e o último elemento
        partes = partes[1:-1]
        
        if len(partes) < 2:
            return valor
        
        # Preencher com zeros à esquerda
        partes[0] = partes[0].zfill(3)
        partes[1] = partes[1].zfill(3)
        
        return '-'.join(partes)
    except:
        return valor

def normalizar_poco(valor):
    """
    Normaliza o formato do poço adicionando zero entre letras e números
    quando for necessário ter 3 caracteres.
    Exemplo: A1 -> A01, F9 -> F09
    """
    try:
        if len(valor) < 3:
            # Separar a parte alfabética da numérica
            parte_letra = ''.join(c for c in valor if c.isalpha())
            parte_numero = ''.join(c for c in valor if c.isdigit())
            
            # Adicionar zero se necessário
            if len(parte_numero) == 1:
                return f"{parte_letra}0{parte_numero}"
            else:
                return f"{parte_letra}{parte_numero}"
        return valor
    except:
        return valor

def mapear_resultado(valor):
    """
    Mapeia o resultado para o formato padrão.
    """
    mapeamento = {
        'Negative Control (NC)': 'NTC',
        'Homozygous POSITIVO/POSITIVO': 'POS:POS',
        'Homozygous NEGATIVO/NEGATIVO': 'NEG:NEG',
        'Heterozygous NEGATIVO/POSITIVO': 'NEG:POS',
        'Y:X': 'NEG:POS',
        'NTC': 'NTC',
        'X:X': 'POS:POS',
        '?': '-',
        'Y:Y': 'NEG:NEG',
        'X:Y': 'NEG:POS',
        'Heterozygous NEG/POS': 'NEG:POS',
        'Homozygous NEG/NEG': 'NEG:NEG',
        'Homozygous POS/POS': 'POS:POS',
        'Undetermined': '-'
    }
    
    return mapeamento.get(valor, valor)


