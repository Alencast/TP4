# Sistema de Gerenciamento de Oficina

Sistema pra gerenciar uma oficina mecânica com rest.

## Ordem de Criação no Django Admin

Ordem de criação no admin pra testar

### 1. Usuários
Primeiro, crie usuários para cada tipo:
- **Cliente**: João Silva (CPF: 12345678901, tipo: Cliente)
- **Mecânico**: Carlos Santos (CPF: 98765432100, tipo: Mecanico)
- **Gerente**: Ana Costa (CPF: 11122233344, tipo: Gerente)

### 2. Peças
Crie algumas peças para o estoque:
- **Filtro de Óleo**: Preço R$ 25,00, Estoque: 10 unidades
- **Pastilha de Freio**: Preço R$ 80,00, Estoque: 5 unidades
- **Óleo do Motor**: Preço R$ 45,00, Estoque: 8 unidades

### 3. Veículos
Cadastre veículos para os clientes:
- **Proprietário**: João Silva
- **Marca/Modelo**: Honda Civic
- **Ano**: 2020
- **Placa**: ABC1234

### 4. Orçamentos
Crie um orçamento:
- **Cliente**: João Silva
- **Veículo**: Honda Civic (ABC1234)
- **Descrição**: Troca de filtro e óleo
- **Valor da Mão de Obra**: R$ 50,00
- **Status**: Pendente (inicial)

### 5. Aprovação do Orçamento
Para aprovar o orçamento, use uma destas opções no admin:

**Opção 1**: Na lista de orçamentos, mude o Status para "Aprovado"
**Opção 2**: Selecione o orçamento e use a ação "Aprovar orçamentos selecionados"
**Opção 3**: Entre no orçamento individual e mude o status

### 6. Ordem de Serviço
Após aprovação automática do orçamento, a ordem de serviço será criada:
- **Mecânico Responsável**: Carlos Santos
- **Status**: Em Andamento (inicial)

### 7. Itens da Peça
Na ordem de serviço, adicione as peças utilizadas:
- **Peça**: Filtro de Óleo, Quantidade: 1
- **Peça**: Óleo do Motor, Quantidade: 1


## Como Executar

1. Execute as migrações:
```
python manage.py makemigrations
python manage.py migrate
```

2. Crie um superusuário:
```
python manage.py createsuperuser
```

3. Execute o servidor:
```
python manage.py runserver
```

4. admin em: http://127.0.0.1:8000/admin/

## Endpoints da api

Base URL: http://127.0.0.1:8000/api/

### Usuários
```
GET     /api/usuarios/           - Listar todos os usuários (Cliente, Mecânico, Gerente)
POST    /api/usuarios/           - Criar usuário
GET     /api/usuarios/{id}/      - Detalhar usuário
PUT     /api/usuarios/{id}/      - Atualizar usuário
DELETE  /api/usuarios/{id}/      - Remover usuário
GET     /api/usuarios/?tipo=cliente - Filtrar por tipo (cliente, mecanico, gerente)
```

### Clientes (Modelo Separado)
```
GET     /api/clientes/           - Listar clientes (modelo separado)
POST    /api/clientes/           - Criar cliente
GET     /api/clientes/{id}/      - Detalhar cliente
PUT     /api/clientes/{id}/      - Atualizar cliente
DELETE  /api/clientes/{id}/      - Remover cliente
```

### Veículos
```
GET     /api/veiculos/           - Listar veículos
POST    /api/veiculos/           - Criar veículo
GET     /api/veiculos/{id}/      - Detalhar veículo
PUT     /api/veiculos/{id}/      - Atualizar veículo
DELETE  /api/veiculos/{id}/      - Remover veículo
```

### Peças
```
GET     /api/pecas/              - Listar peças
POST    /api/pecas/              - Criar peça
GET     /api/pecas/{id}/         - Detalhar peça
PUT     /api/pecas/{id}/         - Atualizar peça
DELETE  /api/pecas/{id}/         - Remover peça
POST    /api/pecas/{id}/verificar_estoque/ - Verificar estoque
```

### Orçamentos
```
GET     /api/orcamentos/         - Listar orçamentos
POST    /api/orcamentos/         - Criar orçamento
GET     /api/orcamentos/{id}/    - Detalhar orçamento
PUT     /api/orcamentos/{id}/    - Atualizar orçamento
DELETE  /api/orcamentos/{id}/    - Remover orçamento
POST    /api/orcamentos/{id}/aprovar/ - Aprovar orçamento
POST    /api/orcamentos/{id}/rejeitar/ - Rejeitar orçamento
POST    /api/orcamentos/{id}/gerar_ordem_servico/ - Gerar ordem de serviço
```


### Ordens de Serviço
```
GET     /api/ordens-servico/     - Listar ordens de serviço
POST    /api/ordens-servico/     - Criar ordem de serviço
GET     /api/ordens-servico/{id}/ - Detalhar ordem de serviço
PUT     /api/ordens-servico/{id}/ - Atualizar ordem de serviço
DELETE  /api/ordens-servico/{id}/ - Remover ordem de serviço
POST    /api/ordens-servico/{id}/concluir/ - Concluir ordem de serviço
```

### Itens de Peça
```
GET     /api/itens-peca/         - Listar itens de peça
POST    /api/itens-peca/         - Criar item de peça
GET     /api/itens-peca/{id}/    - Detalhar item de peça
PUT     /api/itens-peca/{id}/    - Atualizar item de peça
DELETE  /api/itens-peca/{id}/    - Remover item de peça
```

### json pra teste

**Criar um orçamento:**
```json
POST /api/orcamentos/
{
    "cliente": 1,
    "veiculo": 1,
    "descricao": "Troca de filtro e óleo",
    "valor_mao_obra": "50.00"
}
```

**Aprovar um orçamento:**
```
POST /api/orcamentos/1/aprovar/
```

**Verificar estoque de uma peça:**
```
POST /api/pecas/1/verificar_estoque/
```

**Filtrar orçamentos por cliente:**
```
GET /api/orcamentos/?cliente=1
```