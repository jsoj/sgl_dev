import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.conf import settings
from django.db.models import prefetch_related_objects
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def generate_project_pdf(projeto):
    """
    Gera um PDF com as informações completas do projeto
    """
    # Pré-carregar os marcadores para evitar queries adicionais
    try:
        # Carregar explicitamente as relações muitos para muitos
        prefetch_related_objects([projeto], 'marcador_trait', 'marcador_customizado')
        
        # Debug para verificar se os marcadores estão sendo carregados
        trait_count = projeto.marcador_trait.count()
        custom_count = projeto.marcador_customizado.count()
        logger.info(f"Projeto {projeto.id}: {trait_count} traits, {custom_count} customizados")
        
        # Debug: listar marcadores para verificar
        traits = list(projeto.marcador_trait.all())
        customs = list(projeto.marcador_customizado.all())
        
        for trait in traits:
            logger.info(f"Trait loaded: {trait.id} - {trait.nome}")
        
        for custom in customs:
            logger.info(f"Custom loaded: {custom.id} - {custom.nome}")
    except Exception as e:
        logger.error(f"Erro ao carregar marcadores: {e}")
    
    # Configuração do buffer e documento
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=36, leftMargin=36,
                           topMargin=36, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []
    
    # Adicionar logo
    logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo_agromarkers.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo_agromarkers.png')
    
    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo.drawHeight = 2 * inch
        logo.drawWidth = 2 * inch
        elements.append(logo)
    
    # Estilo para o título
    title_style = styles['Heading1']
    title_style.alignment = 1  # Centro
    
    # Título
    elements.append(Paragraph(f"Detalhes do Projeto: {projeto.codigo_projeto}", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Função para criar tabelas de informação com tabulação
    def create_info_table(data_list):
        table = Table(data_list, colWidths=[2*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table
    
    # Seção de informações básicas
    section_style = styles['Heading2']
    elements.append(Paragraph("Informações Básicas", section_style))
    
    # Dados da empresa
    elements.append(Paragraph("<b>Dados da Empresa</b>", styles['Heading3']))
    
    empresa_data = [
        ["Nome:", projeto.empresa.nome],
        ["Código:", projeto.empresa.codigo],
        ["CNPJ:", projeto.empresa.cnpj]
    ]
    
    if projeto.empresa.email:
        empresa_data.append(["Email:", projeto.empresa.email])
    if projeto.empresa.telefone:
        empresa_data.append(["Telefone:", projeto.empresa.telefone])
    
    elements.append(create_info_table(empresa_data))
    elements.append(Spacer(1, 0.15*inch))
    
    # Dados do projeto
    elements.append(Paragraph("<b>Dados do Projeto</b>", styles['Heading3']))
    
    projeto_data = [
        ["Código do Projeto:", projeto.codigo_projeto],
        ["Nome do Projeto (Cliente):", projeto.nome_projeto_cliente or 'Não informado'],
        ["Responsável:", projeto.responsavel],
        ["Quantidade de Amostras:", str(projeto.quantidade_amostras)],
        ["Número de Placas 96:", str(projeto.numero_placas_96 or 'Não calculado')]
    ]
    
    if projeto.codigo_ensaio:
        projeto_data.append(["Código de Ensaio:", projeto.codigo_ensaio])
    if projeto.setor_cliente:
        projeto_data.append(["Setor Cliente:", projeto.setor_cliente])
    if projeto.local_cliente:
        projeto_data.append(["Local Cliente:", projeto.local_cliente])
    if projeto.ano_plantio_ensaio:
        projeto_data.append(["Ano de Plantio:", projeto.ano_plantio_ensaio])
    if projeto.prioridade:
        projeto_data.append(["Prioridade:", projeto.prioridade])
    if hasattr(projeto, 'numero_ordem_servico') and projeto.numero_ordem_servico:
        projeto_data.append(["Número Ordem de Serviço:", projeto.numero_ordem_servico])
    if hasattr(projeto, 'quantidade_material') and projeto.quantidade_material:
        projeto_data.append(["Quantidade de Material:", str(projeto.quantidade_material)])
    
    elements.append(create_info_table(projeto_data))
    elements.append(Spacer(1, 0.2*inch))
    
    # Seção de cultivo e tecnologia
    elements.append(Paragraph("Cultivo e Tecnologias", section_style))
    
    cultivo_data = []
    if projeto.cultivo:
        cultivo_data.append(["Cultivo:", projeto.cultivo.nome])
    
    cultivo_data.append(["Origem da Amostra:", projeto.get_origem_amostra_display() if projeto.origem_amostra else 'Não informado'])
    cultivo_data.append(["Tipo de Amostra:", projeto.get_tipo_amostra_display() if projeto.tipo_amostra else 'Não informado'])
    cultivo_data.append(["Aplicado Herbicida:", 'Sim' if projeto.herbicida else 'Não'])
    cultivo_data.append(["Marcador Já Analisado:", 'Sim' if projeto.marcador_analisado else 'Não'])
    
    if projeto.marcador_analisado:
        cultivo_data.append(["Resultado Anterior:", projeto.get_se_marcador_analisado_display() if projeto.se_marcador_analisado else 'Não informado'])
    
    elements.append(create_info_table(cultivo_data))
    elements.append(Spacer(1, 0.15*inch))
    
    # Tecnologias
    elements.append(Paragraph("<b>Tecnologias</b>", styles['Heading3']))
    
    tecnologia_data = []
    if projeto.tecnologia_parental1:
        tecnologia_data.append(["Tecnologia Parental 1:", projeto.tecnologia_parental1.nome])
        if projeto.tecnologia_parental1.caracteristica:
            tecnologia_data.append(["Característica:", projeto.tecnologia_parental1.caracteristica])
    
    if projeto.tecnologia_parental2:
        tecnologia_data.append(["Tecnologia Parental 2:", projeto.tecnologia_parental2.nome])
        if projeto.tecnologia_parental2.caracteristica:
            tecnologia_data.append(["Característica:", projeto.tecnologia_parental2.caracteristica])
    
    if projeto.tecnologia_target:
        tecnologia_data.append(["Tecnologia Target:", projeto.tecnologia_target.nome])
        if projeto.tecnologia_target.caracteristica:
            tecnologia_data.append(["Característica:", projeto.tecnologia_target.caracteristica])
    
    if projeto.proporcao:
        tecnologia_data.append(["Proporção Esperada:", f"{projeto.proporcao}%"])
    
    if tecnologia_data:
        elements.append(create_info_table(tecnologia_data))
    else:
        elements.append(Paragraph("Nenhuma tecnologia associada ao projeto", styles['Normal']))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Seção de marcadores
    elements.append(Paragraph("Marcadores", section_style))
    
    # Marcadores Trait
    elements.append(Paragraph("<b>Marcadores Trait:</b>", styles['Heading3']))
    
    # Usar uma abordagem diferente para acessar os marcadores
    try:
        # Forçar avaliação da query para marcadores trait
        traits = list(projeto.marcador_trait.all())
        if traits:
            trait_data = []
            trait_data.append(['Nome', 'Característica'])
            for m in traits:
                trait_data.append([m.nome, m.caracteristica or ''])
            
            trait_table = Table(trait_data, colWidths=[1.5*inch, 4*inch])
            trait_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elements.append(trait_table)
        else:
            elements.append(Paragraph("Nenhum marcador trait selecionado", styles['Normal']))
    except Exception as e:
        logger.error(f"Erro ao processar marcadores trait: {e}")
        elements.append(Paragraph(f"Erro ao processar marcadores trait: {str(e)}", styles['Normal']))
    
    elements.append(Spacer(1, 0.15*inch))
    
    # Marcadores Customizados
    elements.append(Paragraph("<b>Marcadores Customizados:</b>", styles['Heading3']))
    
    try:    
        # Forçar avaliação da query para marcadores customizados                                        
        customs = list(projeto.marcador_customizado.all())
        if customs:                        
            custom_data = []
            custom_data.append(['Nome', 'Característica'])
            for m in customs:
                custom_data.append([m.nome, m.caracteristica or ''])
            
            custom_table = Table(custom_data, colWidths=[1.5*inch, 4*inch])
            custom_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elements.append(custom_table)
        else:
            elements.append(Paragraph("Nenhum marcador customizado selecionado", styles['Normal']))
    except Exception as e:
        logger.error(f"Erro ao processar marcadores customizados: {e}")
        elements.append(Paragraph(f"Erro ao processar marcadores customizados: {str(e)}", styles['Normal']))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Status e Etapa
    elements.append(Paragraph("Status do Projeto", section_style))
    
    status_data = []
    if projeto.status:
        status_data.append(["Status:", projeto.status.nome])
    if projeto.etapa:
        status_data.append(["Etapa:", projeto.etapa.nome])
    
    if status_data:
        elements.append(create_info_table(status_data))
    else:
        elements.append(Paragraph("Nenhuma informação de status disponível", styles['Normal']))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Cronograma
    elements.append(Paragraph("Cronograma", section_style))
    
    # Tabela com as datas
    data = [
        ["Data", "Valor"],
        ["Data Planejada de Envio", projeto.data_planejada_envio.strftime("%d/%m/%Y") if projeto.data_planejada_envio else "Não definida"],
        ["Data de Envio", projeto.data_envio.strftime("%d/%m/%Y") if projeto.data_envio else "Não realizado"],
        ["Data Planejada de Liberação", projeto.data_planejada_liberacao_resultados.strftime("%d/%m/%Y") if projeto.data_planejada_liberacao_resultados else "Não definida"],
        ["Data de Recebimento no Laboratório", projeto.data_recebimento_laboratorio.strftime("%d/%m/%Y") if projeto.data_recebimento_laboratorio else "Não recebido"],
        ["Data de Liberação de Resultados", projeto.data_liberacao_resultados.strftime("%d/%m/%Y") if projeto.data_liberacao_resultados else "Não liberado"],
        ["Data de Validação pelo Cliente", projeto.data_validacao_cliente.strftime("%d/%m/%Y") if projeto.data_validacao_cliente else "Não validado"],
        ["Data Prevista de Destruição", projeto.data_prevista_destruicao.strftime("%d/%m/%Y") if projeto.data_prevista_destruicao else "Não definida"],
        ["Data de Destruição", projeto.data_destruicao.strftime("%d/%m/%Y") if projeto.data_destruicao else "Não realizada"],
    ]
    
    # Adicionar mais datas se existirem
    if hasattr(projeto, 'data_extracao') and projeto.data_extracao:
        data.append(["Data de Extração", projeto.data_extracao.strftime("%d/%m/%Y")])
    if hasattr(projeto, 'data_pcr') and projeto.data_pcr:
        data.append(["Data de PCR", projeto.data_pcr.strftime("%d/%m/%Y")])
    if hasattr(projeto, 'data_analise_dados') and projeto.data_analise_dados:
        data.append(["Data de Análise de Dados", projeto.data_analise_dados.strftime("%d/%m/%Y")])
    
    # Criar tabela de datas
    table = Table(data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Comentários
    if projeto.comentarios:
        elements.append(Paragraph("Comentários", section_style))
        comment_style = ParagraphStyle('Comment',
                                      parent=styles['Normal'],
                                      leftIndent=20,
                                      rightIndent=20,
                                      spaceAfter=10,
                                      spaceBefore=10,
                                      borderWidth=1,
                                      borderColor=colors.grey,
                                      borderPadding=10,
                                      borderRadius=5)
        elements.append(Paragraph(projeto.comentarios, comment_style))
    
    # Rodapé
    footer_style = ParagraphStyle('Footer',
                                parent=styles['Normal'],
                                fontSize=8,
                                textColor=colors.grey,
                                alignment=1)  # Centralizado
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Documento gerado automaticamente em {projeto.data_alteracao.strftime('%d/%m/%Y')}", footer_style))
    elements.append(Paragraph("© Agromarkers - Todos os direitos reservados", footer_style))
    
    # Construir documento
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf
