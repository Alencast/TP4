from django.db import models
from django.contrib.auth.models import AbstractUser

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

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15)
    data_cadastro = models.DateTimeField(auto_now_add=True)    

    def __str__(self):
        return self.nome

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
    
    def __str__(self):
        return f"Orçamento #{self.id} - {self.veiculo}"
    
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
        if self.data_conclusao and self.data_conclusao < self.data_inicio:
            raise ValidationError('Data de conclusão não pode ser anterior à data de início.')
        if self.km_entrada < 0:
            raise ValidationError('Quilometragem deve ser um valor positivo.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
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
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        if self.preco_unitario_cobrado < 0:
            raise ValidationError('Preço unitário deve ser um valor positivo.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
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