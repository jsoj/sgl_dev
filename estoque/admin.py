from django.contrib import admin
from .models import (
    UnidadeMedida, CategoriaProduto, Fornecedor, LocalEstoque,
    Produto, ItemEstoque, MovimentacaoEstoque
)

@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'simbolo')
    search_fields = ('nome', 'simbolo')

@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'contato')
    search_fields = ('nome',)

@admin.register(LocalEstoque)
class LocalEstoqueAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome_padrao', 'categoria', 'unidade_medida_primaria', 'sku', 'fornecedor_principal')
    list_filter = ('categoria', 'unidade_medida_primaria', 'fornecedor_principal')
    search_fields = ('nome_padrao', 'sku', 'nome_alternativo_fornecedor', 'descricao')
    autocomplete_fields = ['categoria', 'unidade_medida_primaria', 'fornecedor_principal']

class MovimentacaoEstoqueInline(admin.TabularInline):
    model = MovimentacaoEstoque
    extra = 1
    fk_name = "item_estoque"
    fields = ('tipo_movimentacao', 'quantidade_movimentada', 'unidade_medida_movimentacao', 'data_movimentacao', 'usuario', 'notas')
    readonly_fields = ('quantidade_convertida',) # Calculado no save da movimentação
    autocomplete_fields = ['unidade_medida_movimentacao'] # 'usuario' removido de autocomplete_fields
    # raw_id_fields = ('usuario',) # Alternativa para campos de usuário com muitos usuários

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "usuario":
            kwargs['initial'] = request.user.id
            # Opcional: kwargs['widget'] = admin.widgets.HiddenInput() se não quiser que editem
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ItemEstoque)
class ItemEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'local', 'quantidade', 'saldo_minimo', 'esta_abaixo_minimo', 'ultima_atualizacao', 'media_consumo_display')
    list_filter = ('local', 'produto__categoria', 'produto__unidade_medida_primaria')
    search_fields = ('produto__nome_padrao', 'local__nome')
    readonly_fields = ('quantidade', 'ultima_atualizacao') # Saldo é atualizado por movimentações
    list_select_related = ('produto', 'local', 'produto__unidade_medida_primaria') # Otimização
    autocomplete_fields = ['produto', 'local']
    inlines = [MovimentacaoEstoqueInline] # Permite adicionar movimentações diretamente do ItemEstoque

    def get_queryset(self, request):
        # Otimiza a consulta para os campos usados em list_display
        return super().get_queryset(request).select_related('produto__unidade_medida_primaria', 'local')

    def media_consumo_display(self, obj):
        # Exibe a média de consumo formatada
        media = obj.media_consumo_mensal(meses=1) # Média do último mês
        return f"{media:.2f} {obj.produto.unidade_medida_primaria.simbolo}/mês"
    media_consumo_display.short_description = "Média Consumo (Mês)"


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = (
        'data_movimentacao', 'item_estoque_display', 'tipo_movimentacao',
        'quantidade_movimentada', 'unidade_medida_movimentacao',
        'quantidade_convertida', 'usuario'
    )
    list_filter = ('tipo_movimentacao', 'data_movimentacao', 'item_estoque__local', 'item_estoque__produto__categoria', 'usuario')
    search_fields = ('item_estoque__produto__nome_padrao', 'notas', 'usuario__username')
    readonly_fields = ('quantidade_convertida',)
    date_hierarchy = 'data_movimentacao'
    autocomplete_fields = ['item_estoque', 'unidade_medida_movimentacao'] # 'usuario' removido de autocomplete_fields
    # raw_id_fields = ('usuario',) # Alternativa para campos de usuário com muitos usuários
    list_select_related = ('item_estoque__produto', 'item_estoque__local', 'unidade_medida_movimentacao', 'usuario', 'item_estoque__produto__unidade_medida_primaria')

    def item_estoque_display(self, obj):
        return str(obj.item_estoque)
    item_estoque_display.short_description = "Item de Estoque"
    item_estoque_display.admin_order_field = 'item_estoque' # Permite ordenar por esta coluna

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id: # Define o usuário logado se não estiver preenchido
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        # Preencher unidade de movimentação com a primária do produto por padrão
        form = super().get_form(request, obj, **kwargs)
        if obj is None and 'item_estoque' in form.base_fields: # Apenas para criação e se item_estoque estiver no form
            # Esta lógica pode ser mais complexa se item_estoque for um autocomplete
            # e a unidade primária precisar ser carregada dinamicamente via JS.
            # Para um form simples, você poderia tentar obter o produto do item_estoque se já selecionado.
            pass
        return form