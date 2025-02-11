import pandas as pd
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, Any, Optional
import traceback
from app.models import ResultadoAmostra, ResultadoUpload

logger = logging.getLogger(__name__)

class ResultadoProcessor:
    """Serviço para processar arquivos de resultado e criar registros no banco"""
    
    # Mapeamento de resultados para formato legível
    RESULTADO_MAPPING = {
        'X:X': 'POS/POS',
        'Y:Y': 'NEG/NEG',
        'X:Y': 'POS/NEG',
        'Y:X': 'POS/NEG',
        'NTC': 'CTL',
        '?': '-'
    }
    
    def __init__(self, upload_id: int):
        self.upload = ResultadoUpload.objects.get(id=upload_id)
        self.projeto = self.upload.projeto
        self.placa_1536 = self.upload.placa_1536
    
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