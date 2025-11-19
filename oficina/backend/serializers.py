from rest_framework import serializers
from .models import Usuario, Veiculo, Peca, Orcamento, OrdemServico, ItemPeca

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:

        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'tipo', 'cpf', 'telefone', 'data_nascimento', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):

        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class VeiculoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.username', read_only=True)
    
    class Meta:
        model = Veiculo
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Adicionar informações do cliente nas resposta
        representation['cliente_info'] = {
            'id': instance.cliente.id,
            'username': instance.cliente.username,
            'nome_completo': f"{instance.cliente.first_name} {instance.cliente.last_name}".strip(),
            'tipo': instance.cliente.get_tipo_display()
        }
        return representation
        
class PecaSerializer(serializers.ModelSerializer):
    em_estoque = serializers.SerializerMethodField()
    
    class Meta:
        model = Peca
        fields = '__all__'
        
    def get_em_estoque(self, obj):
  
        return obj.quantidade_estoque > obj.estoque_minimo
        
class ItemPecaSerializer(serializers.ModelSerializer):


    peca_nome = serializers.CharField(source='peca.nome', read_only=True)
    peca_codigo = serializers.CharField(source='peca.codigo', read_only=True)
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    estoque_disponivel = serializers.SerializerMethodField()
    
    class Meta:

        model = ItemPeca
        fields = '__all__'
        read_only_fields = ('estoque_reduzido',)
        
    def get_estoque_disponivel(self, obj):
        return obj.peca.quantidade_estoque
        
    def validate(self, attrs):
        peca = attrs.get('peca')
        quantidade = attrs.get('quantidade')
        
        if peca and quantidade:


            disponivel, mensagem = peca.verificar_disponibilidade(quantidade)
            if not disponivel:
                raise serializers.ValidationError({
                    'quantidade': mensagem,
                    'estoque_atual': peca.quantidade_estoque,
                    'status_peca': peca.get_status_display()
                })
                
        return attrs
        
    def create(self, validated_data):
      
        peca = validated_data['peca']
        quantidade = validated_data['quantidade']
        
        disponivel, mensagem = peca.verificar_disponibilidade(quantidade)
        if not disponivel:
            raise serializers.ValidationError(f'Erro de estoque: {mensagem}')
            
        return super().create(validated_data)
        
class OrcamentoSerializer(serializers.ModelSerializer):
    veiculo_info = serializers.CharField(source='veiculo.__str__', read_only=True)
    mecanico_nome = serializers.CharField(source='mecanico_responsavel.get_full_name', read_only=True)
    
    class Meta:
        model = Orcamento
        fields = '__all__'
        read_only_fields = ('mecanico_responsavel', 'valor_total', 'data_criacao')
        
    def validate_data_validade(self, value):


        from django.utils import timezone
        from datetime import date
        
        hoje = timezone.now().date()
        if value <= hoje:
            raise serializers.ValidationError(
                "Data de validade deve ser uma data futura."
            )
        return value
        
    def validate_valor_mao_obra(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Valor de mão de obra não pode ser negativo."
            )
        return value
        
    def validate_descricao_problema(self, value):

        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Descrição do problema deve ter no mínimo 20 caracteres."
            )
        return value
        
    def validate_veiculo(self, value):


        if not hasattr(value, 'cliente') or not value.cliente:

            raise serializers.ValidationError(
                "Veículo deve ter um cliente associado."
            )
        return value
        
    def validate(self, attrs):

      #calcular o total

        valor_mao_obra = attrs.get('valor_mao_obra', 0)
        valor_pecas = attrs.get('valor_pecas', 0)
        attrs['valor_total'] = valor_mao_obra + valor_pecas
        
        return attrs
        
    def create(self, validated_data):
    

        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:


            if request.user.tipo in ['mecanico', 'gerente']:
                validated_data['mecanico_responsavel'] = request.user
            else:
                raise serializers.ValidationError({
                    'mecanico_responsavel': 'Apenas mecânicos e gerentes podem criar orçamentos.'
                })
        else:
            raise serializers.ValidationError({
                'mecanico_responsavel': 'Usuário deve estar autenticado para criar orçamento.'
            })
            
        return super().create(validated_data)
        
class OrdemServicoSerializer(serializers.ModelSerializer):


    orcamento_info = serializers.CharField(source='orcamento.__str__', read_only=True)


    itens_pecas = ItemPecaSerializer(many=True, read_only=True)
    
    class Meta:

        
        model = OrdemServico
        fields = '__all__' 