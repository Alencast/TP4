from django.shortcuts import render
from django.db import models
from django.utils import timezone
from datetime import datetime
from rest_framework import viewsets
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Usuario, Cliente, Veiculo, Peca, Orcamento, OrdemServico, ItemPeca
from .serializers import UsuarioSerializer, ClienteSerializer, VeiculoSerializer, PecaSerializer, OrcamentoSerializer, OrdemServicoSerializer, ItemPecaSerializer

# Create your views here.

# ViewSets para os modelos

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    
    def get_queryset(self):
        queryset = Usuario.objects.all()
        tipo = self.request.query_params.get('tipo', None)
        if tipo is not None:
            queryset = queryset.filter(tipo=tipo)
        return queryset

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
    
    def get_queryset(self):
        """Filtros customizados para fabricante, status e estoque_minimo"""
        queryset = super().get_queryset()
        
        # Filtro por fabricante
        fabricante = self.request.query_params.get('fabricante')
        if fabricante:
            queryset = queryset.filter(fabricante__icontains=fabricante)
            
        # Filtro por status
        status_filtro = self.request.query_params.get('status')
        if status_filtro:
            queryset = queryset.filter(status=status_filtro)
            
        # Filtro por estoque mínimo (peças abaixo do estoque mínimo)
        estoque_minimo = self.request.query_params.get('estoque_minimo')
        if estoque_minimo == 'true':
            queryset = queryset.filter(quantidade_estoque__lte=models.F('estoque_minimo'))
        elif estoque_minimo == 'false':
            queryset = queryset.filter(quantidade_estoque__gt=models.F('estoque_minimo'))
            
        return queryset
        
    @action(detail=True, methods=['get'])
    def verificar_estoque(self, request, pk=None):
        """
        Action customizada para verificar se há estoque suficiente
        Parâmetros: quantidade_desejada (query param)
        Retorna: se há estoque suficiente
        """
        try:
            peca = self.get_object()
            quantidade_desejada = request.query_params.get('quantidade_desejada')
            
            if not quantidade_desejada:
                return Response(
                    {'erro': 'Parâmetro quantidade_desejada é obrigatório'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                quantidade_desejada = int(quantidade_desejada)
            except ValueError:
                return Response(
                    {'erro': 'quantidade_desejada deve ser um número inteiro'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if quantidade_desejada <= 0:
                return Response(
                    {'erro': 'quantidade_desejada deve ser maior que zero'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            estoque_suficiente = peca.quantidade_estoque >= quantidade_desejada
            estoque_disponivel = peca.quantidade_estoque
            
            return Response({
                'peca': {
                    'id': peca.id,
                    'codigo': peca.codigo,
                    'nome': peca.nome,
                    'fabricante': peca.fabricante
                },
                'quantidade_desejada': quantidade_desejada,
                'estoque_disponivel': estoque_disponivel,
                'estoque_suficiente': estoque_suficiente,
                'diferenca': estoque_disponivel - quantidade_desejada,
                'status_estoque': peca.get_status_display(),
                'abaixo_minimo': estoque_disponivel <= peca.estoque_minimo
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'erro': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class OrcamentoViewSet(viewsets.ModelViewSet):
    serializer_class = OrcamentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['veiculo__placa', 'mecanico_responsavel__username', 'descricao_problema']
    ordering_fields = ['data_criacao', 'data_validade', 'valor_total', 'status']
    ordering = ['-data_criacao']
    
    def get_queryset(self):
        """Filtros baseados em permissões e parâmetros"""
        user = self.request.user
        queryset = Orcamento.objects.select_related('veiculo', 'mecanico_responsavel')
        
        # Aplicar filtros de permissão
        if user.tipo == 'cliente':
            # Cliente vê apenas orçamentos dos seus veículos
            queryset = queryset.filter(veiculo__cliente=user)
        elif user.tipo == 'mecanico':
            # Mecânico vê orçamentos atribuídos a ele
            queryset = queryset.filter(mecanico_responsavel=user)
        elif user.tipo == 'gerente':
            # Gerente vê todos os orçamentos
            pass
        else:
            # Se não é nenhum tipo reconhecido, não vê nada
            queryset = queryset.none()
            
        # Aplicar filtros de query params
        
        # Filtro por cliente (apenas para gerentes)
        if user.tipo == 'gerente':
            cliente_id = self.request.query_params.get('cliente')
            if cliente_id:
                queryset = queryset.filter(veiculo__cliente__id=cliente_id)
                
        # Filtro por status
        status_filtro = self.request.query_params.get('status')
        if status_filtro:
            queryset = queryset.filter(status=status_filtro)
            
        # Filtro por período
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        
        if data_inicio:
            try:
                data_inicio_parsed = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(data_criacao__date__gte=data_inicio_parsed)
            except ValueError:
                pass  # Ignora formato inválido
                
        if data_fim:
            try:
                data_fim_parsed = datetime.strptime(data_fim, '%Y-%m-%d').date()
                queryset = queryset.filter(data_criacao__date__lte=data_fim_parsed)
            except ValueError:
                pass  # Ignora formato inválido
                
        return queryset
        
    def perform_create(self, serializer):
        """Garantir que o usuário tenha permissão para criar orçamento"""
        if self.request.user.tipo not in ['mecanico', 'gerente']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Apenas mecânicos e gerentes podem criar orçamentos.')
        serializer.save()
        
    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        """Aprovar orçamento (apenas o cliente proprietário do veículo)"""
        try:
            orcamento = self.get_object()
            user = request.user
            
            # Verificar se é o cliente proprietário do veículo
            if user.tipo != 'cliente' or orcamento.veiculo.cliente != user:
                return Response(
                    {'erro': 'Apenas o cliente proprietário do veículo pode aprovar o orçamento'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Verificar se orçamento está pendente
            if orcamento.status != 'pendente':
                return Response(
                    {'erro': f'Não é possível aprovar orçamento com status: {orcamento.get_status_display()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar se orçamento não expirou
            if orcamento.data_validade < timezone.now().date():
                return Response(
                    {'erro': 'Orçamento expirado não pode ser aprovado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Aprovar orçamento
            orcamento.status = 'aprovado'
            orcamento.save()
            
            return Response(
                {
                    'mensagem': 'Orçamento aprovado com sucesso',
                    'orcamento_id': orcamento.id,
                    'status': orcamento.get_status_display()
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'erro': f'Erro ao aprovar orçamento: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=True, methods=['post'])
    def rejeitar(self, request, pk=None):
        """Rejeitar orçamento com motivo"""
        try:
            orcamento = self.get_object()
            user = request.user
            motivo = request.data.get('motivo', '').strip()
            
            # Verificar permissões: cliente proprietário ou mecânico responsável ou gerente
            if not (
                (user.tipo == 'cliente' and orcamento.veiculo.cliente == user) or
                (user.tipo == 'mecanico' and orcamento.mecanico_responsavel == user) or
                user.tipo == 'gerente'
            ):
                return Response(
                    {'erro': 'Sem permissão para rejeitar este orçamento'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Verificar se orçamento está pendente
            if orcamento.status != 'pendente':
                return Response(
                    {'erro': f'Não é possível rejeitar orçamento com status: {orcamento.get_status_display()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Validar motivo
            if len(motivo) < 10:
                return Response(
                    {'erro': 'Motivo da rejeição deve ter no mínimo 10 caracteres'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Rejeitar orçamento
            orcamento.status = 'rejeitado'
            # Adicionar motivo às observações
            orcamento.observacoes += f"\n\n[REJEITADO em {timezone.now().strftime('%d/%m/%Y %H:%M')} por {user.username}]\n{motivo}"
            orcamento.save()
            
            return Response(
                {
                    'mensagem': 'Orçamento rejeitado com sucesso',
                    'orcamento_id': orcamento.id,
                    'status': orcamento.get_status_display(),
                    'motivo': motivo
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'erro': f'Erro ao rejeitar orçamento: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=True, methods=['post'])
    def gerar_ordem_servico(self, request, pk=None):
        """Gerar Ordem de Serviço a partir de orçamento aprovado"""
        try:
            orcamento = self.get_object()
            user = request.user
            
            # Verificar permissões: apenas mecânico responsável ou gerente
            if not (
                (user.tipo == 'mecanico' and orcamento.mecanico_responsavel == user) or
                user.tipo == 'gerente'
            ):
                return Response(
                    {'erro': 'Apenas o mecânico responsável ou gerente pode gerar ordem de serviço'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Verificar se orçamento está aprovado
            if orcamento.status != 'aprovado':
                return Response(
                    {'erro': 'Apenas orçamentos aprovados podem gerar ordem de serviço'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar se já existe ordem de serviço
            if hasattr(orcamento, 'ordem_servico'):
                return Response(
                    {'erro': f'Já existe uma ordem de serviço (#{orcamento.ordem_servico.id}) para este orçamento'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Obter dados para a ordem de serviço
            data_inicio = request.data.get('data_inicio')
            data_previsao = request.data.get('data_previsao')
            km_entrada = request.data.get('km_entrada')
            
            # Validações dos dados
            if not all([data_inicio, data_previsao, km_entrada]):
                return Response(
                    {'erro': 'data_inicio, data_previsao e km_entrada são obrigatórios'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                data_inicio_parsed = datetime.strptime(data_inicio, '%Y-%m-%d %H:%M:%S')
                data_previsao_parsed = datetime.strptime(data_previsao, '%Y-%m-%d').date()
                km_entrada_int = int(km_entrada)
            except (ValueError, TypeError):
                return Response(
                    {'erro': 'Formato inválido: data_inicio (YYYY-MM-DD HH:MM:SS), data_previsao (YYYY-MM-DD), km_entrada (inteiro)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Criar ordem de serviço
            ordem_servico = OrdemServico.objects.create(
                orcamento=orcamento,
                data_inicio=data_inicio_parsed,
                data_previsao=data_previsao_parsed,
                km_entrada=km_entrada_int,
                status='aguardando'
            )
            
            return Response(
                {
                    'mensagem': 'Ordem de serviço criada com sucesso',
                    'ordem_servico_id': ordem_servico.id,
                    'orcamento_id': orcamento.id,
                    'data_inicio': ordem_servico.data_inicio,
                    'data_previsao': ordem_servico.data_previsao,
                    'km_entrada': ordem_servico.km_entrada,
                    'status': ordem_servico.get_status_display()
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'erro': f'Erro ao gerar ordem de serviço: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class OrdemServicoViewSet(viewsets.ModelViewSet):
    queryset = OrdemServico.objects.all().select_related('orcamento__veiculo').prefetch_related('itens_pecas')
    serializer_class = OrdemServicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['orcamento__veiculo__placa', 'status']
    ordering_fields = ['data_inicio', 'data_previsao', 'data_conclusao', 'status']
    ordering = ['-data_inicio']
    
    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        """Concluir ordem de serviço e confirmar uso das peças do estoque"""
        try:
            ordem = self.get_object()
            user = request.user
            
            # Verificar permissões
            if user.tipo not in ['mecanico', 'gerente']:
                return Response(
                    {'erro': 'Apenas mecânicos e gerentes podem concluir ordens de serviço'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Verificar se está em andamento
            if ordem.status != 'em_andamento':
                return Response(
                    {'erro': f'Apenas ordens em andamento podem ser concluídas. Status atual: {ordem.get_status_display()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar se há peças na ordem
            if not ordem.itens_pecas.exists():
                return Response(
                    {'erro': 'Ordem de serviço deve ter pelo menos uma peça para ser concluída'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar estoque de todas as peças antes de concluir
            estoque_insuficiente = []
            for item in ordem.itens_pecas.all():
                if not item.estoque_reduzido:  # Só verificar se ainda não foi reduzido
                    disponivel, mensagem = item.peca.verificar_disponibilidade(item.quantidade)
                    if not disponivel:
                        estoque_insuficiente.append({
                            'peca': item.peca.codigo,
                            'nome': item.peca.nome,
                            'quantidade_necessaria': item.quantidade,
                            'quantidade_disponivel': item.peca.quantidade_estoque,
                            'erro': mensagem
                        })
                        
            if estoque_insuficiente:
                return Response({
                    'erro': 'Estoque insuficiente para concluir ordem de serviço',
                    'pecas_com_problema': estoque_insuficiente
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Concluir ordem de serviço
            ordem.status = 'concluido'
            ordem.data_conclusao = timezone.now()
            ordem.save()
            
            # O signal post_save irá gerenciar o estoque automaticamente
            
            return Response({
                'mensagem': 'Ordem de serviço concluída com sucesso',
                'ordem_servico_id': ordem.id,
                'data_conclusao': ordem.data_conclusao,
                'pecas_utilizadas': [
                    {
                        'codigo': item.peca.codigo,
                        'nome': item.peca.nome,
                        'quantidade_utilizada': item.quantidade,
                        'estoque_atual': item.peca.quantidade_estoque
                    }
                    for item in ordem.itens_pecas.all()
                ]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'erro': f'Erro ao concluir ordem de serviço: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class ItemPecaViewSet(viewsets.ModelViewSet):
    queryset = ItemPeca.objects.all().select_related('ordem_servico', 'peca')
    serializer_class = ItemPecaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['peca__nome', 'peca__codigo', 'ordem_servico__id']
    ordering_fields = ['quantidade', 'preco_unitario_cobrado']
    ordering = ['peca__nome']
    
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