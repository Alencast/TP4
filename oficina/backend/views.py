from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import filters
from .models import Cliente, Veiculo, Peca, Orcamento, OrdemServico, ItemPeca
from .serializers import ClienteSerializer, VeiculoSerializer, PecaSerializer, OrcamentoSerializer, OrdemServicoSerializer, ItemPecaSerializer

# Create your views here.

# Exemplo de uma viewset para o modelo Cliente


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    
class VeiculoViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.all().select_related('cliente')
    serializer_class = VeiculoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['placa', 'marca', 'modelo', 'cliente__username', 'cliente__first_name', 'cliente__last_name']
    ordering_fields = ['marca', 'modelo', 'ano', 'data_cadastro']
    ordering = ['marca', 'modelo']
    
class PecaViewSet(viewsets.ModelViewSet):
    queryset = Peca.objects.all()
    serializer_class = PecaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo', 'nome', 'fabricante']
    ordering_fields = ['nome', 'fabricante', 'preco_unitario', 'quantidade_estoque']
    ordering = ['nome']
    
class OrcamentoViewSet(viewsets.ModelViewSet):
    queryset = Orcamento.objects.all().select_related('veiculo', 'mecanico_responsavel')
    serializer_class = OrcamentoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['veiculo__placa', 'mecanico_responsavel__username', 'descricao_problema']
    ordering_fields = ['data_criacao', 'data_validade', 'valor_total', 'status']
    ordering = ['-data_criacao']
    
class OrdemServicoViewSet(viewsets.ModelViewSet):
    queryset = OrdemServico.objects.all().select_related('orcamento__veiculo').prefetch_related('itens_pecas')
    serializer_class = OrdemServicoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['orcamento__veiculo__placa', 'status']
    ordering_fields = ['data_inicio', 'data_previsao', 'data_conclusao', 'status']
    ordering = ['-data_inicio']
    
class ItemPecaViewSet(viewsets.ModelViewSet):
    queryset = ItemPeca.objects.all().select_related('ordem_servico', 'peca')
    serializer_class = ItemPecaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['peca__nome', 'peca__codigo', 'ordem_servico__id']
    ordering_fields = ['quantidade', 'preco_unitario_cobrado']
    ordering = ['peca__nome'] 