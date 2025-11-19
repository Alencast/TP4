from rest_framework import serializers
from .models import Cliente, Veiculo, Peca, Orcamento, OrdemServico, ItemPeca

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        
class VeiculoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.username', read_only=True)
    
    class Meta:
        model = Veiculo
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Adicionar informações do cliente na resposta
        representation['cliente_info'] = {
            'id': instance.cliente.id,
            'username': instance.cliente.username,
            'nome_completo': f"{instance.cliente.first_name} {instance.cliente.last_name}".strip(),
            'tipo': instance.cliente.get_tipo_display()
        }
        return representation
        
class PecaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Peca
        fields = '__all__'
        
class OrcamentoSerializer(serializers.ModelSerializer):
    veiculo_info = serializers.CharField(source='veiculo.__str__', read_only=True)
    mecanico_nome = serializers.CharField(source='mecanico_responsavel.get_full_name', read_only=True)
    
    class Meta:
        model = Orcamento
        fields = '__all__'
        
class ItemPecaSerializer(serializers.ModelSerializer):
    peca_nome = serializers.CharField(source='peca.nome', read_only=True)
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ItemPeca
        fields = '__all__'
        
class OrdemServicoSerializer(serializers.ModelSerializer):
    orcamento_info = serializers.CharField(source='orcamento.__str__', read_only=True)
    itens_pecas = ItemPecaSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrdemServico
        fields = '__all__' 