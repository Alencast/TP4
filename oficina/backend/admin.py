from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Cliente, Veiculo, Usuario, Peca, Orcamento, OrdemServico, ItemPeca

# Register your models here.

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo', 'is_staff')
    list_filter = ('tipo', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'cpf')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('tipo', 'cpf', 'telefone', 'data_nascimento')
        }),
    )
    
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'data_cadastro')
    search_fields = ('nome', 'email')
    list_filter = ('data_cadastro',)

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'ano', 'cor', 'cliente', 'data_cadastro')
    list_filter = ('marca', 'ano', 'cor', 'data_cadastro')
    search_fields = ('placa', 'marca', 'modelo', 'cliente__username', 'cliente__first_name')
    list_select_related = ('cliente',)
    
    fieldsets = (
        ('Informações do Veículo', {
            'fields': ('placa', 'marca', 'modelo', 'ano', 'cor')
        }),
        ('Proprietário', {
            'fields': ('cliente',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'fabricante', 'quantidade_estoque', 'preco_unitario', 'status')
    list_filter = ('fabricante', 'status', 'data_cadastro')
    search_fields = ('codigo', 'nome', 'fabricante')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'nome', 'descricao', 'fabricante')
        }),
        ('Estoque e Preço', {
            'fields': ('quantidade_estoque', 'estoque_minimo', 'preco_unitario', 'status')
        })
    )
    
@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'veiculo', 'mecanico_responsavel', 'data_criacao', 'valor_total', 'status')
    list_filter = ('status', 'data_criacao', 'data_validade')
    search_fields = ('veiculo__placa', 'mecanico_responsavel__username', 'descricao_problema')
    list_select_related = ('veiculo', 'mecanico_responsavel')
    
    fieldsets = (
        ('Veículo e Responsável', {
            'fields': ('veiculo', 'mecanico_responsavel')
        }),
        ('Descrição e Prazos', {
            'fields': ('descricao_problema', 'data_validade')
        }),
        ('Valores', {
            'fields': ('valor_mao_obra', 'valor_pecas', 'valor_total', 'status')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )

class ItemPecaInline(admin.TabularInline):
    model = ItemPeca
    extra = 1
    fields = ('peca', 'quantidade', 'preco_unitario_cobrado')
    
@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'orcamento', 'data_inicio', 'data_previsao', 'status', 'km_entrada')
    list_filter = ('status', 'data_inicio', 'data_previsao')
    search_fields = ('orcamento__veiculo__placa', 'status')
    list_select_related = ('orcamento__veiculo',)
    inlines = [ItemPecaInline]
    
    fieldsets = (
        ('Orçamento', {
            'fields': ('orcamento',)
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_previsao', 'data_conclusao')
        }),
        ('Status e Informações', {
            'fields': ('status', 'km_entrada')
        })
    )
    
@admin.register(ItemPeca)
class ItemPecaAdmin(admin.ModelAdmin):
    list_display = ('peca', 'ordem_servico', 'quantidade', 'preco_unitario_cobrado', 'valor_total')
    list_filter = ('ordem_servico__status', 'peca__fabricante')
    search_fields = ('peca__nome', 'peca__codigo', 'ordem_servico__id')
    list_select_related = ('peca', 'ordem_servico')
    
    def valor_total(self, obj):
        return obj.valor_total
    valor_total.short_description = 'Valor Total'
    valor_total.admin_order_field = 'preco_unitario_cobrado'