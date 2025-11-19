from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

# Create your models here.

class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('mecanico', 'Mecânico'),
        ('gerente', 'Gerente'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='cliente'
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        help_text='CPF no formato 000.000.000-00'
    )
    telefone = models.CharField(
        max_length=20,
        help_text='Telefone com DDD'
    )
    data_nascimento = models.DateField(
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.username} - {self.get_tipo_display()}"
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

class Veiculo(models.Model):
    placa = models.CharField(
        max_length=10,
        unique=True,
        help_text='Placa do veículo no formato ABC-1234 ou ABC1D23'
    )
    marca = models.CharField(
        max_length=50,
        help_text='Marca do veículo (ex: Toyota, Honda, Volkswagen)'
    )
    modelo = models.CharField(
        max_length=50,
        help_text='Modelo do veículo (ex: Corolla, Civic, Golf)'
    )
    ano = models.IntegerField(
        help_text='Ano de fabricação do veículo'
    )
    cor = models.CharField(
        max_length=30,
        help_text='Cor do veículo'
    )
    cliente = models.ForeignKey(

        'Usuario',
        on_delete=models.CASCADE,
        related_name='veiculos',
        help_text='Proprietário do veículo'
    )
    observacoes = models.TextField(
        blank=True,
        help_text='Observações adicionais sobre o veículo'
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True
    )
    
    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.placa}"
    
    class Meta:
        

        verbose_name = 'Veículo'
        verbose_name_plural = 'Veículos'
        ordering = ['marca', 'modelo', 'ano']

class Peca(models.Model):
    STATUS_CHOICES = [

        ('disponivel', 'Disponível'),
        ('esgotado', 'Esgotado'),
        ('descontinuado', 'Descontinuado'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    fabricante = models.CharField(max_length=50)
    quantidade_estoque = models.IntegerField(default=0)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    estoque_minimo = models.IntegerField(default=5)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='disponivel')
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def verificar_disponibilidade(self, quantidade_desejada):
  
            
        if self.status == 'esgotado':
            return False, 'Peça está esgotada'
            
        if self.quantidade_estoque < quantidade_desejada:
            return False, f'Estoque insuficiente. Disponível: {self.quantidade_estoque}, Solicitado: {quantidade_desejada}'
            
        return True, 'Peça tá disponível'
        
    def reduzir_estoque(self, quantidade):
     
        if self.quantidade_estoque >= quantidade:
            self.quantidade_estoque -= quantidade
            
            # Atualizar status baseado no estoque
            if self.quantidade_estoque == 0:
                self.status = 'esgotado'

            elif self.status == 'esgotado' and self.quantidade_estoque > 0:
                self.status = 'disponivel'
                
            self.save()
            return True
        return False
        
    def adicionar_estoque(self, quantidade):
        
        self.quantidade_estoque += quantidade
        
        # marcar como disponível se o estoque aumentou
        if self.status == 'esgotado' and self.quantidade_estoque > 0:
            self.status = 'disponivel'
            
        self.save()
    
    class Meta:
        verbose_name = 'Peça'
        verbose_name_plural = 'Peças'
        ordering = ['nome']

class Orcamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('expirado', 'Expirado'),
    ]
    
    veiculo = models.ForeignKey('Veiculo', on_delete=models.CASCADE, related_name='orcamentos')
    mecanico_responsavel = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='orcamentos_responsavel')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_validade = models.DateField()
    descricao_problema = models.TextField()
    valor_mao_obra = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pecas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True)
    desconto_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Orçamento #{self.id} - {self.veiculo}"
    
    def save(self, *args, **kwargs):
     
        self.valor_total = self.valor_mao_obra + self.valor_pecas

        super().save(*args, **kwargs)
        
    def aprovar(self):
   
        from django.utils import timezone
        from datetime import timedelta
        
        hoje = timezone.now().date()
        
        # Verificar expirou
        if self.data_validade < hoje:

            self.status = 'expirado'

            self.save()
            return False, 'Orçamento expirado'
            
        # Verificar se tá pendente
        if self.status != 'pendente':
            return False, 'Apenas orçamentos pendentes podem ser aprovados'
     
            
        self.status = 'aprovado'


        self.save()

        return True, 'Aprovado com sucesso'
    
    class Meta:

        
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-data_criacao']



class OrdemServico(models.Model):
    STATUS_CHOICES = [


        ('aguardando', 'Aguardando'),
        ('em_andamento', 'Em Andamento'),
        ('aguardando_pecas', 'Aguardando Peças'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    orcamento = models.OneToOneField('Orcamento', on_delete=models.CASCADE, related_name='ordem_servico')
    data_inicio = models.DateTimeField()

    data_previsao = models.DateField()

    data_conclusao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aguardando')

    km_entrada = models.IntegerField(help_text='Quilometragem na entrada')
    
    def clean(self):
        from django.core.exceptions import ValidationError

        if self.data_conclusao and self.data_inicio and self.data_conclusao < self.data_inicio:

            raise ValidationError('Data de conclusão não pode ser anterior à data de início.')
        if self.km_entrada is not None and self.km_entrada < 0:
            raise ValidationError('Quilometragem deve ser um positivo.')
    
    def save(self, *args, **kwargs):
        # Verificar regras antes de criar
        if not self.pk:  # Nova ordem
            if self.orcamento.status != 'aprovado':
                raise ValueError('Ordem só pode ser criada para orçamento aprovado')
        self.full_clean()
        super().save(*args, **kwargs)
        
    def concluir(self):
        """Concluir ordem de serviço"""
        from django.utils import timezone
        
        if self.status != 'em_andamento':
            return False, 'Apenas ordens em andamento podem ser concluídas'
            
        # Registrar conclusão
        self.data_conclusao = timezone.now()
        self.status = 'concluido'
        
        # Calcular oalor final
        valor_pecas_utilizadas = sum(
            item.quantidade * item.preco_unitario_cobrado 
            for item in self.itens_pecas.all()
        )
    
        
        self.save()
        return True, 'Ordem concluída com sucesso'
    
    def __str__(self):
        return f"OS #{self.id} - {self.orcamento.veiculo}"
    
    class Meta:
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'
        ordering = ['-data_inicio']

class ItemPeca(models.Model):
    ordem_servico = models.ForeignKey('OrdemServico', on_delete=models.CASCADE, related_name='itens_pecas')
    peca = models.ForeignKey('Peca', on_delete=models.CASCADE, related_name='itens_utilizados')
    quantidade = models.IntegerField()
    preco_unitario_cobrado = models.DecimalField(max_digits=10, decimal_places=2)
    estoque_reduzido = models.BooleanField(default=False, help_text='Indica se o estoque já foi reduzido')
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
       
        if self.quantidade is not None and self.quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        if self.preco_unitario_cobrado is not None and self.preco_unitario_cobrado < 0:
            raise ValidationError('Preço unitário deve ser um valor positivo.')
            
  
        if not self.pk and self.peca and self.quantidade: 
            disponivel, mensagem = self.peca.verificar_disponibilidade(self.quantidade)
            if not disponivel:
                raise ValidationError(f'Erro de estoque: {mensagem}')
    
    def save(self, *args, **kwargs):
        # Verificar se é um novo item ou se a quantidade foi alterada
        novo_item = self.pk is None
        quantidade_alterada = False
        quantidade_anterior = 0
        
        if not novo_item:
            # Buscar quantidade anterior para comparar
            item_anterior = ItemPeca.objects.get(pk=self.pk)
            quantidade_anterior = item_anterior.quantidade
            quantidade_alterada = quantidade_anterior != self.quantidade
        
        
        self.full_clean()
        
       
        super().save(*args, **kwargs)
        
    
        if hasattr(self.ordem_servico, 'status') and self.ordem_servico.status == 'concluido':
            self.confirmar_uso_estoque()
            
    def confirmar_uso_estoque(self):
      
        if not self.estoque_reduzido:
            sucesso = self.peca.reduzir_estoque(self.quantidade)
            if sucesso:
                self.estoque_reduzido = True
                super().save(update_fields=['estoque_reduzido'])
                return True
            else:
                from django.core.exceptions import ValidationError
                raise ValidationError(f'Não foi possível reduzir estoque da peça {self.peca.codigo}')
        return False
        
    def reverter_uso_estoque(self):
       
        if self.estoque_reduzido:
            self.peca.adicionar_estoque(self.quantidade)
            self.estoque_reduzido = False
            super().save(update_fields=['estoque_reduzido'])
            
    def delete(self, *args, **kwargs):
      
        if self.estoque_reduzido:
            self.reverter_uso_estoque()
        super().delete(*args, **kwargs)
    
    @property
    def valor_total(self):
        return self.quantidade * self.preco_unitario_cobrado
    
    def __str__(self):
        return f"{self.peca.nome} (Qtd: {self.quantidade}) - OS #{self.ordem_servico.id}"
    
    class Meta:
        verbose_name = 'Item Peça'
        verbose_name_plural = 'Itens Peças'
        ordering = ['peca__nome']
        unique_together = ['ordem_servico', 'peca']


#gerenciar o estoque autmaticamente

@receiver(post_save, sender=OrdemServico)
def gerenciar_estoque_ordem_servico(sender, instance, **kwargs):
   
    if instance.status == 'concluido':
       
        for item in instance.itens_pecas.all():
            item.confirmar_uso_estoque()
    elif instance.status == 'cancelado':
    
        for item in instance.itens_pecas.all():
            item.reverter_uso_estoque()