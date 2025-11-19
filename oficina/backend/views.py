from django.shortcuts import render
from django.db import models
from django.utils import timezone
from datetime import datetime
from rest_framework import viewsets
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from .models import Usuario, Veiculo, Peca, Orcamento, OrdemServico, ItemPeca
from .serializers import UsuarioSerializer, VeiculoSerializer, PecaSerializer, OrcamentoSerializer, OrdemServicoSerializer, ItemPecaSerializer

# permissões custom pra cada tipo de usuário
class IsCliente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo == 'cliente'

class IsMecanico(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo == 'mecanico'

class IsGerente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo == 'gerente'

class IsMecanicoOrGerente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo in ['mecanico', 'gerente']


class UsuarioViewSet(viewsets.ModelViewSet):

    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    
    def get_queryset(self):


        queryset = Usuario.objects.all()
        tipo = self.request.query_params.get('tipo', None)
        if tipo is not None:
            queryset = queryset.filter(tipo=tipo)
        return queryset

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


        queryset = super().get_queryset()
        
        # Filtro por fabricante
        fabricante = self.request.query_params.get('fabricante')
        if fabricante:
            queryset = queryset.filter(fabricante__icontains=fabricante)
            
        # Filtro por status
        status_filtro = self.request.query_params.get('status')
        if status_filtro:
            queryset = queryset.filter(status=status_filtro)
            
        # Filtro por estoque míni
        estoque_minimo = self.request.query_params.get('estoque_minimo')
        if estoque_minimo == 'true':
            queryset = queryset.filter(quantidade_estoque__lte=models.F('estoque_minimo'))
        elif estoque_minimo == 'false':
            queryset = queryset.filter(quantidade_estoque__gt=models.F('estoque_minimo'))
            
        return queryset
        
    @action(detail=True, methods=['get'])

    def verificar_estoque(self, request, pk=None):
      
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

    queryset = Orcamento.objects.all().select_related('veiculo', 'mecanico_responsavel')

    serializer_class = OrcamentoSerializer

    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['veiculo__placa', 'mecanico_responsavel__username', 'descricao_problema']

    ordering_fields = ['data_criacao', 'data_validade', 'valor_total', 'status']

    ordering = ['-data_criacao']
    
    def get_queryset(self):

        user = self.request.user

        queryset = Orcamento.objects.select_related('veiculo', 'mecanico_responsavel')
        
        #filtro de permissão

        if user.tipo == 'cliente':
            # Procliente ver apenas orçamentos dos seus próprios veículos
            queryset = queryset.filter(veiculo__cliente=user)
        elif user.tipo == 'mecanico':
            # Mecânico vê orçamentos atribuídos a ele
            queryset = queryset.filter(mecanico_responsavel=user)
        elif user.tipo == 'gerente':
            # Gerente pode ver todos os orçamentos
            pass
        else:
            # Se não é nenhum tipo reconhecido, não vê nada
            queryset = queryset.none()
            
        #  filtros doquery params
        cliente = self.request.query_params.get('cliente')

        if cliente:
            queryset = queryset.filter(veiculo__cliente_id=cliente)
            
        status_filtro = self.request.query_params.get('status')

        if status_filtro:
            queryset = queryset.filter(status=status_filtro)
            
        # Filtro por período
        data_inicio = self.request.query_params.get('data_inicio')

        data_fim = self.request.query_params.get('data_fim')

        if data_inicio:

            queryset = queryset.filter(data_criacao__date__gte=data_inicio)

        if data_fim:

            queryset = queryset.filter(data_criacao__date__lte=data_fim)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):

        orcamento = self.get_object()
        
        # Apenas ocliente pode aprovar seu próprio orçamento
        if request.user.tipo != 'cliente' or orcamento.veiculo.cliente != request.user:
            return Response(
                {'erro': 'Apenas o cliente pode aprovar seu orçamento'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        sucesso, mensagem = orcamento.aprovar()

        if sucesso:
            return Response({'mensagem': mensagem}, status=status.HTTP_200_OK)
        
        else:
            return Response({'erro': mensagem}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def rejeitar(self, request, pk=None):


        orcamento = self.get_object()
        motivo = request.data.get('motivo', '')
        
        # Apenas o cliente pode rejeitar seu próprio orçamento
        if request.user.tipo != 'cliente' or orcamento.veiculo.cliente != request.user:
            return Response(
                {'erro': 'Apenas o cliente pode rejeitar seu orçamento'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if orcamento.status != 'pendente':
            return Response(
                {'erro': 'Apenas orçamentos pendentes podem ser rejeitados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orcamento.status = 'rejeitado'

        orcamento.observacoes = f"Rejeitado: {motivo}"

        orcamento.save()
        
        return Response({'mensagem': 'Orçamento rejeitado com sucesso'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def gerar_ordem_servico(self, request, pk=None):


        orcamento = self.get_object()
        
        # Apenas mecânico/gerente pode gerar uma ordem
        if request.user.tipo not in ['mecanico', 'gerente']:

            return Response(
                {'erro': 'Apenas mecânicos e gerentes podem gerar ordens de serviço'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar se orçamento táá aprovado
        if orcamento.status != 'aprovado':
            
            return Response(
                {'erro': 'Apenas orçamentos aprovados podem gerar ordem de serviço'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se já existe ordem para o orçamento
        if hasattr(orcamento, 'ordem_servico'):
            return Response(
                {'erro': 'Já existe uma ordem de serviço para este orçamento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar ordem de serviço

        from django.utils import timezone
        from datetime import timedelta
        
        data_inicio = timezone.now()

        data_previsao = (data_inicio + timedelta(days=7)).date()

        km_entrada = request.data.get('km_entrada', 0)
        
        ordem = OrdemServico.objects.create(
            orcamento=orcamento,
            data_inicio=data_inicio,
            data_previsao=data_previsao,
            km_entrada=km_entrada,
            status='em_andamento'
        )
        
        serializer = OrdemServicoSerializer(ordem)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class OrdemServicoViewSet(viewsets.ModelViewSet):

    queryset = OrdemServico.objects.all().select_related('orcamento__veiculo').prefetch_related('itens_pecas')

    serializer_class = OrdemServicoSerializer

    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['orcamento__veiculo__placa', 'status']

    ordering_fields = ['data_inicio', 'data_previsao', 'data_conclusao', 'status']

    ordering = ['-data_inicio']
    
    @action(detail=True, methods=['post'])
    def adicionar_peca(self, request, pk=None):


        try:

            ordem = self.get_object()

            user = request.user
            
            if user.tipo not in ['mecanico', 'gerente']:
                
                return Response(
                    {'erro': 'Apenas mecânicos e gerentes podem adicionar peças'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verificar se a ordem táem andamento
            if ordem.status not in ['em_andamento', 'aguardando_pecas']:
                return Response(
                    {'erro': f'Peças só podem ser adicionadas em ordens em andamento ou aguardando peças'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extrair os  dados da requisição

            peca_id = request.data.get('peca_id')

            quantidade = request.data.get('quantidade')

            preco_unitario_cobrado = request.data.get('preco_unitario_cobrado')
            
            # Validações

            if not peca_id:
                return Response({'erro': 'peca_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            if not quantidade or quantidade <= 0:
                return Response({'erro': 'quantidade tem que ser maior que zero'}, status=status.HTTP_400_BAD_REQUEST)
            if not preco_unitario_cobrado or preco_unitario_cobrado < 0:
                return Response({'erro': 'preco_unitario_cobrado deve ser maior que zero'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                peca = Peca.objects.get(id=peca_id)
            except Peca.DoesNotExist:
                return Response({'erro': 'Peça nno encontrada'}, status=status.HTTP_404_NOT_FOUND)
            
            # Verificar disponibilidade
            disponivel, mensagem = peca.verificar_disponibilidade(quantidade)
            if not disponivel:
                return Response({'erro': mensagem}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar se peça já existe na ordem
            if ordem.itens_pecas.filter(peca=peca).exists():
                return Response({'erro': 'Peça já adicionada a essa  ordem'}, status=status.HTTP_400_BAD_REQUEST)
            
            # c  riar item
            item = ItemPeca.objects.create(
                ordem_servico=ordem,
                peca=peca,
                quantidade=quantidade,
                preco_unitario_cobrado=preco_unitario_cobrado
            )
            
            serializer = ItemPecaSerializer(item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'erro': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        try:
            ordem = self.get_object()
            user = request.user
            
            if user.tipo not in ['mecanico', 'gerente']:
                return Response(
                    {'erro': 'Apenas mecânicos e gerentes podem concluir ordens de serviço'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            if ordem.status != 'em_andamento':
                return Response(
                    {'erro': f'Apenas ordens em andamento podem ser concluídas. Status atual: {ordem.get_status_display()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if not ordem.itens_pecas.exists():
                return Response(
                    {'erro': 'Ordem de serviço deve ter pelo menos uma peça para ser concluída'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
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
                
            ordem.status = 'concluido'
            ordem.data_conclusao = timezone.now()
            ordem.save()
            
            
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
                {'erro': f'Erro: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class ItemPecaViewSet(viewsets.ModelViewSet):

    queryset = ItemPeca.objects.all().select_related('ordem_servico', 'peca')

    serializer_class = ItemPecaSerializer

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['peca__nome', 'peca__codigo', 'ordem_servico__id']

    ordering_fields = ['quantidade', 'preco_unitario_cobrado']
    
    ordering = ['peca__nome'] 