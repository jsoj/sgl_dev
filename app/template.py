from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import barcode
from barcode.writer import ImageWriter
import os
from datetime import datetime

def mm_to_points(mm_value):
    """Converte milímetros para pontos"""
    return mm_value * 2.83464567  # 1mm = 2.83464567 points

def generate_barcode(codigo, filename):
    """Gera código de barras EAN13"""
    import os
    
    # Cria diretório temp no nível do projeto
    base_dir = os.path.dirname(os.path.dirname(__file__))
    temp_dir = os.path.join(base_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Remove .png e garante extensão única
    filename = filename.rstrip('.png') + '.png'
    
    # Caminho completo
    filepath = os.path.join(temp_dir, filename)
    
    codigo = str(codigo).zfill(12)
    ean = barcode.get('ean13', codigo, writer=ImageWriter())
    return ean.save(filepath)

class PlateLayoutPDF:
    def __init__(self, projeto, empresa, output_path="plate_layout.pdf"):
        """
        Inicializa o gerador de PDF
        :param projeto: Objeto do modelo Projeto
        :param empresa: Objeto do modelo Empresa
        :param output_path: Caminho onde o PDF será salvo
        """
        self.projeto = projeto
        self.empresa = empresa
        self.output_path = output_path
        self.c = canvas.Canvas(output_path, pagesize=A4)
        
        # Dimensões da página A4 em mm
        self.page_width = 210
        self.page_height = 297
        
        # Dimensões da placa em mm
        self.plate_width = 127.76
        self.plate_height = 85.48
        self.well_diameter = 4.5
        
        # Margens
        self.margin_left = 5
        self.margin_top = 5
        
        # Logging para debug
        print(f"Inicializando PlateLayoutPDF para projeto {projeto.codigo_projeto}")
        print(f"Output path: {output_path}")

    def calculate_plates_needed(self):
        """Calcula número de placas necessárias baseado na quantidade de amostras"""
        amostras_por_placa = 90  # 96 poços - 4 controles
        return -(-self.projeto.quantidade_amostras // amostras_por_placa)  # Arredonda para cima

    def calculate_well_position(self, well_number):
        """
        Calcula a posição do poço (A01-H12) baseado no número sequencial.
        """
        row = chr(65 + ((well_number - 1) // 12))  # A-H
        col = ((well_number - 1) % 12) + 1
        return f"{row}{col:02d}"

    def draw_plate(self, x_start, y_start, plate_number):
        """
        Desenha uma placa individual com 96 poços
        :param x_start: Posição inicial X em mm
        :param y_start: Posição inicial Y em mm
        :param plate_number: Número da placa
        """
        try:
            print(f"Desenhando placa {plate_number}")
            # Retângulo da placa
            self.c.roundRect(
                mm_to_points(x_start),
                mm_to_points(y_start),
                mm_to_points(self.plate_width),
                mm_to_points(self.plate_height),
                mm_to_points(5)
            )

            # Informações do projeto
            header_y = y_start + self.plate_height - 15
            self.c.setFont("Helvetica", 10)
            
            # Nome do projeto e informações
            projeto_info = self.projeto.nome_projeto_cliente or "RV_CZ_MULTPOP_F3_4_2_2"  # Valor padrão se estiver vazio
            plate_code = f"{self.empresa.codigo}-{self.projeto.codigo_projeto}-{plate_number:03d}"
            
            # Desenha as informações com espaçamento correto
            self.c.drawString(
                mm_to_points(x_start + 5),
                mm_to_points(header_y + 10),
                f"PROJECT: {projeto_info}"
            )
            
            self.c.drawString(
                mm_to_points(x_start + 5),
                mm_to_points(header_y),
                f"Plate N°: {plate_code}"
            )
            
            self.c.drawString(
                mm_to_points(x_start + 5),
                mm_to_points(header_y - 10),
                f"N° DO ENVIO: 109"  # Número fixo conforme exemplo
            )

            # Grade de poços
            well_start_x = x_start + 14.38
            well_start_y = y_start + self.plate_height - 25  # Ajustado para dar mais espaço ao cabeçalho

            # Letras das linhas (A-H)
            self.c.setFont("Helvetica", 7)
            for row in range(8):
                self.c.drawString(
                    mm_to_points(well_start_x - 8),
                    mm_to_points(well_start_y - (row * self.well_diameter * 2) - 1.5),
                    chr(65 + row)
                )

            # Números das colunas (1-12)
            for col in range(12):
                self.c.drawString(
                    mm_to_points(well_start_x + (col * self.well_diameter * 2)),
                    mm_to_points(well_start_y + 6),
                    f"{col+1:02d}"
                )

            # Obter os poços de controle configurados
            control_wells = self.projeto.get_control_wells()
                
            # Poços e numeração
            self.c.setFont("Helvetica", 6)
            amostras_por_placa = 96 - len(control_wells)  # Ajustado para considerar os poços de controle
            amostra_inicial = ((plate_number - 1) * amostras_por_placa) + 1
            sample_number = amostra_inicial

            for row in range(8):
                for col in range(12):
                    x = well_start_x + (col * self.well_diameter * 2)
                    y = well_start_y - (row * self.well_diameter * 2)
                    
                    # Posição do poço
                    pos = f"{chr(65 + row)}{col+1:02d}"
                    
                    # Verifica se é poço de controle
                    is_control = pos in control_wells
                    
                    # Desenha círculo do poço
                    self.c.circle(
                        mm_to_points(x),
                        mm_to_points(y),
                        mm_to_points(self.well_diameter - 0.5),
                        fill=0  # Alterado para não preencher
                    )
                    
                    if is_control:
                        # Poços de controle
                        self.c.drawCentredString(
                            mm_to_points(x),
                            mm_to_points(y - 1),
                            "NTC"
                        )
                    else:
                        # Poços de amostras
                        if sample_number <= self.projeto.quantidade_amostras:
                            self.c.drawCentredString(
                                mm_to_points(x),
                                mm_to_points(y - 1),
                                str(sample_number)
                            )
                            sample_number += 1

        except Exception as e:
            print(f"Erro ao desenhar placa {plate_number}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise    

    def draw_well_grid(self, x_start, y_start, plate_number):
        """
        Desenha a grade de poços com letras e números
        """
        well_start_x = x_start + 14.38
        well_start_y = y_start + self.plate_height - 11.24
        
        # Letras das linhas (A-H)
        self.c.setFont("Helvetica", 7)
        for row in range(8):
            self.c.drawString(
                mm_to_points(well_start_x - 8),
                mm_to_points(well_start_y - (row * self.well_diameter * 2) - 1.5),
                chr(65 + row)
            )

        # Números das colunas (1-12)
        for col in range(12):
            self.c.drawString(
                mm_to_points(well_start_x + (col * self.well_diameter * 2)),
                mm_to_points(well_start_y + 6),
                f"{col+1:02d}"
            )

        # Desenhar poços
        self.draw_wells(well_start_x, well_start_y, plate_number)

    def draw_wells(self, well_start_x, well_start_y, plate_number):
        """
        Desenha os poços individuais com seus números
        """
        self.c.setFont("Helvetica", 6)
        amostras_por_placa = 90
        amostra_inicial = ((plate_number - 1) * amostras_por_placa) + 1
        sample_number = amostra_inicial

        for row in range(8):
            for col in range(12):
                x = well_start_x + (col * self.well_diameter * 2)
                y = well_start_y - (row * self.well_diameter * 2)
                
                # Verifica se é poço de controle (NTC)
                is_control = (col == 0 and row < 4)
                
                # Desenha círculo do poço
                self.c.circle(
                    mm_to_points(x),
                    mm_to_points(y),
                    mm_to_points(self.well_diameter - 0.5),
                    fill=1
                )
                
                # Texto do poço
                if is_control:
                    self.c.setFillColorRGB(0, 0, 0)
                    self.c.drawCentredString(
                        mm_to_points(x),
                        mm_to_points(y - 1),
                        "NTC"
                    )
                else:
                    if sample_number <= self.projeto.quantidade_amostras:
                        self.c.setFillColorRGB(0, 0, 0)
                        self.c.drawCentredString(
                            mm_to_points(x),
                            mm_to_points(y - 1),
                            str(sample_number)
                        )
                        sample_number += 1

    def generate_pdf(self):
        """Gera o PDF com duas placas por página"""
        try:
            print("Iniciando geração do PDF...")
            num_plates = self.calculate_plates_needed()
            current_plate = 1
            
            while current_plate <= num_plates:
                # Primeira placa na página
                self.draw_plate(
                    self.margin_left,
                    self.page_height - self.margin_top - self.plate_height,
                    current_plate
                )
                
                # Segunda placa na página (se houver)
                if current_plate + 1 <= num_plates:
                    self.draw_plate(
                        self.margin_left,
                        self.page_height - (2 * self.margin_top) - (2 * self.plate_height),
                        current_plate + 1
                    )
                
                # Nova página se não for a última
                if current_plate < num_plates:
                    self.c.showPage()
                
                current_plate += 2
            
            print("Finalizando e salvando PDF...")
            self.c.save()
            return self.output_path

        except Exception as e:
            print(f"Erro na geração do PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

# Exemplo de uso na criação do projeto
def generate_plate_template(projeto, empresa):
    """
    Gera o template PDF para um projeto
    :param projeto: Instância do modelo Projeto
    :param empresa: Instância do modelo Empresa
    :return: Caminho do arquivo PDF gerado
    """
    import os
    
    # Define o diretório base do projeto Django
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Gera nome único para o arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"template_{empresa.codigo}_{projeto.codigo_projeto}_{timestamp}.pdf"
    
    # Cria diretório temp com caminho absoluto
    temp_dir = os.path.join(BASE_DIR, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Caminho completo do arquivo
    output_path = os.path.join(temp_dir, filename)
    print(f"Gerando PDF em: {output_path}")
    
    # Gera o PDF
    generator = PlateLayoutPDF(projeto, empresa, output_path)
    pdf_path = generator.generate_pdf()
    
    return pdf_path



