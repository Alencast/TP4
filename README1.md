# Sistema de Gerenciamento de Oficina Mecânica

Sistema desenvolvido usando Django REST Framework para gerenciar uma oficina mecânica 


## Como Executar

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar Migrações
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Criar Superusuário
```bash
python manage.py createsuperuser
```

### 4. Executar Servidor
```bash
python manage.py runserver
```

### 5. Acessos
- **API**: http://127.0.0.1:8000/api/
- **Admin**: http://127.0.0.1:8000/admin/


**Configuração atual**: SQLite (desenvolvimento)
**Configuração para produção**: PostgreSQL (comentada no settings.py)

Para usar PostgreSQL em produção, descomente as configurações no `settings.py` e instale:
```bash
pip install psycopg2-binary
```

##  **Endpoints da ap**

### Usuários
```
GET/POST   /api/usuarios/              - Listar/Criar usuários
GET/PUT    /api/usuarios/{id}/         - Detalhar/Atualizar usuário
GET        /api/usuarios/?tipo=cliente - Filtrar por tipo
```

### Veículos
```
GET/POST   /api/veiculos/              - Listar/Criar veículos
GET/PUT    /api/veiculos/{id}/         - Detalhar/Atualizar veículo
```

### Peças
```
GET/POST   /api/pecas/                     - Listar/Criar peças
GET/PUT    /api/pecas/{id}/                - Detalhar/Atualizar peça
GET        /api/pecas/{id}/verificar_estoque/ - Verificar disponibilidade
GET        /api/pecas/?fabricante=toyota   - Filtrar por fabricante
GET        /api/pecas/?status=disponivel   - Filtrar por status
GET        /api/pecas/?estoque_minimo=true - Filtrar estoque baixo
```

### Orçamentos
```
GET/POST   /api/orcamentos/                    - Listar/Criar orçamentos
GET/PUT    /api/orcamentos/{id}/               - Detalhar/Atualizar orçamento
POST       /api/orcamentos/{id}/aprovar/       - Aprovar orçamento (Cliente)
POST       /api/orcamentos/{id}/rejeitar/      - Rejeitar com motivo
POST       /api/orcamentos/{id}/gerar_ordem_servico/ - Gerar OS (Mecânico/Gerente)
GET        /api/orcamentos/?cliente=1&status=pendente - Filtros
```

### Ordens de Serviço
```
GET/POST   /api/ordens-servico/                    - Listar/Criar ordens
GET/PUT    /api/ordens-servico/{id}/               - Detalhar/Atualizar ordem
POST       /api/ordens-servico/{id}/adicionar_peca/ - Adicionar peça
POST       /api/ordens-servico/{id}/concluir/      - Concluir ordem
```

### Itens de Peça
```
GET/POST   /api/itens-peca/            - Listar/Criar itens
GET/PUT    /api/itens-peca/{id}/       - Detalhar/Atualizar item
```

##  **Exemplos de json pra testar**

### Criar Usuário
```json
POST /api/usuarios/
{
    "username": "placido",
    "first_name": "placido",
    "last_name": "neto", 
    "email": "placido@email.com",
    "password": "senha123",
    "tipo": "cliente",
    "cpf": "12345678901",
    "telefone": "(11) 99999-9999",
    "data_nascimento": "1990-01-15"
}
```

### Criar Veículo
```json
POST /api/veiculos/
{
    "placa": "ABC1234",
    "marca": "Honda",
    "modelo": "Civic",
    "ano": 2020,
    "cor": "Prata",
    "cliente": 1,
    "observacoes": "Veículo em bom estado"
}
```

### Criar Peça
```json
POST /api/pecas/
{
    "codigo": "FLT001",
    "nome": "Filtro de Óleo",
    "descricao": "Filtro de óleo para motor 1.0",
    "fabricante": "Mann",
    "quantidade_estoque": 10,
    "preco_unitario": "25.90",
    "estoque_minimo": 5,
    "status": "disponivel"
}
```

### Criar Orçamento
```json
POST /api/orcamentos/
{
    "veiculo": 1,
    "data_validade": "2024-12-31",
    "descricao_problema": "Troca de filtro de óleo e óleo do motor conforme revisão programada",
    "valor_mao_obra": "50.00",
    "valor_pecas": "75.90"
}
```

### Aprovar Orçamento
```json
POST /api/orcamentos/1/aprovar/
```

### Gerar Ordem de Serviço  
```json
POST /api/orcamentos/1/gerar_ordem_servico/
{
    "data_inicio": "2024-01-15 08:00:00",
    "data_previsao": "2024-01-15", 
    "km_entrada": 50000
}
```

### Adicionar Peça à Ordem
```json
POST /api/ordens-servico/1/adicionar_peca/
{
    "peca_id": 1,
    "quantidade": 1,
    "preco_unitario_cobrado": "25.90"
}
```

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
