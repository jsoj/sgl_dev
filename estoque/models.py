from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum, Avg, F
from django.utils import timezone
from decimal import Decimal

# Modelos Auxiliares

class UnidadeMedida(models.Model):
    """
    Representa as unidades de medida para os produtos (ex: Litro, Peça, mL).
    """
    nome = models.CharField(max_length=50, unique=True, verbose_name="Nome da Unidade") # Ex: Peça, Caixa, Litro, Mililitro
    simbolo = models.CharField(max_length=10, unique=True, verbose_name="Símbolo") # Ex: pç, cx, L, mL, µL
    # Para conversão, podemos definir uma unidade base para cada "tipo" de medida (ex: mL para volume)
    # e um fator para converter ESTA unidade para a unidade base.
    # Ex: Unidade 'Litro', simbolo 'L', unidade_base_referencia='Mililitro', fator_para_base=1000
    # Ex: Unidade 'Mililitro', simbolo 'mL', unidade_base_referencia='Mililitro', fator_para_base=1
    # Esta é uma forma de simplificar. Outra seria ter um modelo de ConversaoUnidade.
    # Por ora, vamos manter simples e a lógica de conversão será mais explícita.

    def __str__(self):
        return f"{self.nome} ({self.simbolo})"

    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nome']

class CategoriaProduto(models.Model):
    """
    Categorias para agrupar produtos (ex: Placas PCR, Reagentes).
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Categoria de Produto"
        verbose_name_plural = "Categorias de Produtos"
        ordering = ['nome']

class Fornecedor(models.Model):
    """
    Fornecedores dos produtos.
    """
    nome = models.CharField(max_length=255, unique=True, verbose_name="Nome do Fornecedor")
    contato = models.TextField(blank=True, null=True, verbose_name="Informações de Contato")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['nome']

class LocalEstoque(models.Model):
    """
    Locais físicos de estoque (ex: Agromarkers, Latitude).
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Local")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Local de Estoque"
        verbose_name_plural = "Locais de Estoque"
        ordering = ['nome']

# Modelo Principal de Produto

class Produto(models.Model):
    """
    Representa um item individual do estoque.
    """
    nome_padrao = models.CharField(max_length=255, verbose_name="Nome Padrão Interno", help_text="Nome principal para identificação interna.")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição Detalhada")
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.PROTECT, related_name="produtos", verbose_name="Categoria")
    unidade_medida_primaria = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        related_name="produtos_unidade_primaria",
        verbose_name="Unidade de Medida Primária",
        help_text="Unidade usada para contagem de saldo e relatórios principais."
    )
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="SKU (Código Único)", help_text="Se aplicável.")
    # Para rastrear nomes específicos de fornecedores
    # Se um produto pode ter múltiplos nomes de fornecedor, criar um modelo intermediário (ProdutoFornecedorNome)
    # Por simplicidade, vamos permitir um nome alternativo e um fornecedor principal aqui.
    nome_alternativo_fornecedor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome no Fornecedor", help_text="Nome específico utilizado por um fornecedor.")
    fornecedor_principal = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, blank=True, null=True, related_name="produtos_fornecidos", verbose_name="Fornecedor Principal")

    def __str__(self):
        return f"{self.nome_padrao} ({self.unidade_medida_primaria.simbolo})"

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome_padrao']

# Modelos de Estoque e Transações

class ItemEstoque(models.Model):
    """
    Representa a quantidade de um Produto específico em um LocalEstoque.
    """
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="itens_estoque", verbose_name="Produto")
    local = models.ForeignKey(LocalEstoque, on_delete=models.CASCADE, related_name="itens_estoque", verbose_name="Local de Estoque")
    quantidade = models.DecimalField(
        max_digits=15, decimal_places=5, default=Decimal('0.00000'), verbose_name="Quantidade em Estoque",
        help_text="Saldo atual na unidade de medida primária do produto."
    )
    saldo_minimo = models.DecimalField(
        max_digits=15, decimal_places=5, default=Decimal('0.00000'), verbose_name="Saldo Mínimo",
        help_text="Nível mínimo desejado para este item neste local."
    )
    ultima_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    def __str__(self):
        return f"{self.produto.nome_padrao} em {self.local.nome}: {self.quantidade} {self.produto.unidade_medida_primaria.simbolo}"

    def esta_abaixo_minimo(self):
        return self.quantidade < self.saldo_minimo
    esta_abaixo_minimo.boolean = True
    esta_abaixo_minimo.short_description = "Abaixo do Mínimo?"

    def media_consumo_mensal(self, meses=1):
        """
        Calcula a média de consumo para este item de estoque nos últimos X meses.
        Assume que 'SAIDA' é o tipo de transação que representa consumo.
        """
        if meses <= 0:
            return Decimal('0.0')

        data_inicio = timezone.now() - timezone.timedelta(days=meses * 30) # Aproximação de meses
        transacoes_saida = MovimentacaoEstoque.objects.filter(
            item_estoque=self,
            tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.SAIDA,
            data_movimentacao__gte=data_inicio
        )
        
        total_consumido = transacoes_saida.aggregate(total=Sum('quantidade_convertida'))['total'] or Decimal('0.0')
        
        # Calcula o número real de dias no período para maior precisão se necessário,
        # mas para média mensal, dividir por `meses` é geralmente suficiente.
        # dias_no_periodo = (timezone.now().date() - data_inicio.date()).days
        # if dias_no_periodo == 0: return Decimal('0.0')
        # media_diaria = total_consumido / Decimal(dias_no_periodo)
        # return media_diaria * Decimal(30) # Média mensal estimada

        return total_consumido / Decimal(meses) if total_consumido > 0 else Decimal('0.0')


    class Meta:
        unique_together = (('produto', 'local'),) # Garante um registro único por produto/local
        verbose_name = "Item em Estoque"
        verbose_name_plural = "Itens em Estoque"
        ordering = ['produto__nome_padrao', 'local__nome']


class MovimentacaoEstoque(models.Model):
    """
    Registra todas as entradas, saídas e ajustes de estoque.
    """
    class TipoMovimentacao(models.TextChoices):
        ENTRADA = 'ENTRADA', 'Entrada'
        SAIDA = 'SAIDA', 'Saída'
        AJUSTE_POSITIVO = 'AJUSTE_P', 'Ajuste Positivo'
        AJUSTE_NEGATIVO = 'AJUSTE_N', 'Ajuste Negativo'
        AJUSTE_SALDO = 'AJUSTE_S', 'Ajuste de Saldo (Define Novo Saldo)' # Para contagem/inventário

    item_estoque = models.ForeignKey(ItemEstoque, on_delete=models.PROTECT, related_name="movimentacoes", verbose_name="Item de Estoque")
    tipo_movimentacao = models.CharField(max_length=10, choices=TipoMovimentacao.choices, verbose_name="Tipo de Movimentação")
    
    quantidade_movimentada = models.DecimalField(
        max_digits=15, decimal_places=5, verbose_name="Quantidade Movimentada",
        help_text="Quantidade na unidade da movimentação. Para 'Ajuste de Saldo', este é o NOVO saldo."
    )
    unidade_medida_movimentacao = models.ForeignKey(
        UnidadeMedida, on_delete=models.PROTECT, verbose_name="Unidade da Movimentação",
        help_text="Unidade em que a quantidade movimentada foi medida."
    )
    
    # Armazena a quantidade convertida para a unidade primária do produto do ItemEstoque.
    # Isso é crucial para atualizar o saldo do ItemEstoque corretamente.
    quantidade_convertida = models.DecimalField(
        max_digits=15, decimal_places=5, editable=False, verbose_name="Quantidade Convertida (Primária)",
        help_text="Quantidade convertida para a unidade primária do produto."
    )

    data_movimentacao = models.DateTimeField(default=timezone.now, verbose_name="Data e Hora")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário Responsável")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas/Observações")
    # Opcional: Referência a um projeto do app principal
    # projeto_relacionado = models.ForeignKey('app_principal.Projeto', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_movimentacao_display()} de {self.item_estoque.produto.nome_padrao} em {self.data_movimentacao.strftime('%d/%m/%Y %H:%M')}"

    def _realizar_conversao_unidade(self):
        """
        Converte a 'quantidade_movimentada' da 'unidade_medida_movimentacao'
        para a 'unidade_medida_primaria' do 'item_estoque.produto'.
        Esta é uma função placeholder. A lógica real de conversão precisa ser implementada
        baseada em como você define os fatores de conversão entre unidades.
        Exemplo simplificado:
        """
        un_mov = self.unidade_medida_movimentacao
        un_prim = self.item_estoque.produto.unidade_medida_primaria
        qtd_mov = self.quantidade_movimentada

        if un_mov == un_prim:
            return qtd_mov

        # Lógica de conversão (EXEMPLO MUITO SIMPLIFICADO - NECESSITA IMPLEMENTAÇÃO ROBUSTA)
        # Você precisará de uma tabela de fatores de conversão ou uma lógica mais elaborada.
        # Ex: mL para L, L para mL, µL para mL, etc.
        # Supondo que temos um dicionário de fatores para mL (unidade base para volume)
        fatores_para_ml = {
            'L': Decimal('1000.0'),
            'mL': Decimal('1.0'),
            'µL': Decimal('0.001'),
        }

        simbolo_mov = un_mov.simbolo
        simbolo_prim = un_prim.simbolo

        if simbolo_mov in fatores_para_ml and simbolo_prim in fatores_para_ml:
            qtd_em_ml = qtd_mov * fatores_para_ml[simbolo_mov]
            qtd_convertida_final = qtd_em_ml / fatores_para_ml[simbolo_prim]
            return qtd_convertida_final
        else:
            # Se não houver regra de conversão direta, levanta um erro ou retorna a quantidade original com aviso.
            # É crucial ter uma forma de definir essas conversões.
            raise ValidationError(
                f"Não foi possível converter de {un_mov.simbolo} para {un_prim.simbolo}. "
                "Configure as regras de conversão."
            )
        # return self.quantidade_movimentada # Placeholder

    def clean(self):
        super().clean()
        if self.quantidade_movimentada <= 0 and self.tipo_movimentacao != self.TipoMovimentacao.AJUSTE_SALDO:
             if not (self.tipo_movimentacao == self.TipoMovimentacao.AJUSTE_NEGATIVO and self.quantidade_movimentada < 0): # Permitir negativo para ajuste negativo
                raise ValidationError({'quantidade_movimentada': "A quantidade movimentada deve ser positiva para este tipo de movimentação."})
        
        if self.tipo_movimentacao == self.TipoMovimentacao.AJUSTE_SALDO and self.quantidade_movimentada < 0:
            raise ValidationError({'quantidade_movimentada': "Para 'Ajuste de Saldo', a quantidade deve ser o novo saldo total e não pode ser negativa."})


    def save(self, *args, **kwargs):
        # Garantir que o ItemEstoque exista ou seja criado antes da movimentação
        # Normalmente, o ItemEstoque já existirá. Se não, pode ser criado aqui ou
        # a interface do usuário deve garantir sua criação prévia.
        
        # 1. Realizar a conversão da unidade
        self.quantidade_convertida = self._realizar_conversao_unidade()

        # 2. Lógica para atualizar o saldo do ItemEstoque ANTES de salvar a movimentação
        #    para garantir atomicidade ou usar transações de banco de dados.
        #    Usar F() expressions para evitar race conditions.
        
        item = self.item_estoque # Objeto ItemEstoque
        # qtd_a_aplicar_no_saldo = Decimal('0.0') # Quantidade que efetivamente altera o saldo # Removido pois não estava sendo usado efetivamente no fluxo de atualização com F()

        if self.pk is None: # Apenas executa a lógica de atualização de saldo para novas movimentações
            if self.tipo_movimentacao == self.TipoMovimentacao.ENTRADA:
                # qtd_a_aplicar_no_saldo = self.quantidade_convertida # Removido
                item.quantidade = F('quantidade') + self.quantidade_convertida
            elif self.tipo_movimentacao == self.TipoMovimentacao.SAIDA:
                # Validação de saldo deve idealmente acontecer no clean() do form ou do model,
                # mas uma checagem aqui antes de F() é uma boa prática defensiva,
                # embora F() expressions operem no nível do BD.
                # Para uma validação rigorosa que impeça o save, o clean() é melhor.
                # A validação aqui pode não impedir a query se o valor for negativo no BD antes do refresh.
                # No entanto, a validação no clean() do form do admin ou um check explícito antes de .save()
                # é mais robusto para a UI.
                # if item.quantidade < self.quantidade_convertida: # Esta checagem aqui é MENOS EFETIVA que no clean()
                #     raise ValidationError(f"Saldo insuficiente para {item.produto.nome_padrao} em {item.local.nome}. Saldo: {item.quantidade}, Saída: {self.quantidade_convertida}")
                # qtd_a_aplicar_no_saldo = -self.quantidade_convertida # Removido
                item.quantidade = F('quantidade') - self.quantidade_convertida
            elif self.tipo_movimentacao == self.TipoMovimentacao.AJUSTE_POSITIVO:
                # qtd_a_aplicar_no_saldo = self.quantidade_convertida # Removido
                item.quantidade = F('quantidade') + self.quantidade_convertida
            elif self.tipo_movimentacao == self.TipoMovimentacao.AJUSTE_NEGATIVO:
                # qtd_a_aplicar_no_saldo = -self.quantidade_convertida # Removido
                item.quantidade = F('quantidade') - self.quantidade_convertida
            elif self.tipo_movimentacao == self.TipoMovimentacao.AJUSTE_SALDO:
                # diferenca = self.quantidade_convertida - item.quantidade # Removido
                # qtd_a_aplicar_no_saldo = diferenca # Removido
                item.quantidade = self.quantidade_convertida # Define o novo saldo diretamente

            item.save(update_fields=['quantidade', 'ultima_atualizacao'])
            item.refresh_from_db() # Recarrega o item para ter o valor atualizado de 'quantidade' após F() expression

        super().save(*args, **kwargs) # Salva a movimentação em si

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data_movimentacao']