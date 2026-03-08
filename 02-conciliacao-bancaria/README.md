# Projeto 02 — Conciliação Bancária em Python

Ferramenta CLI para conciliar lançamentos entre **extrato bancário** e **sistema/ERP**, com regras progressivas de correspondência, geração de relatório Excel e logging estruturado.

---

# Objetivo

Automatizar a conciliação entre dois conjuntos de lançamentos financeiros, identificando:

- lançamentos conciliados
- lançamentos presentes apenas no extrato
- lançamentos presentes apenas no sistema
- divergências de valor na mesma data

---

# Funcionalidades

- Conciliação por **documento exato**
  - `extrato.documento == sistema.id_lancamento`
- Conciliação por **documento dentro do histórico**
  - quando o documento do extrato aparece no campo `historico` do sistema
- Conciliação por **valor + janela de dias**
- Matching por **similaridade de texto**
  - entre `descricao` do extrato e `historico` do sistema
- Pareamento **1:1**
  - evita usar o mesmo lançamento do sistema em mais de uma conciliação
- Detecção de **divergências**
  - mesma data, valores diferentes
- Relatório Excel com múltiplas abas
- Logging estruturado em console e arquivo
- CLI com subcomandos:
  - `conciliar`
  - `validar`
  - `gerar-exemplo`

---

# Estrutura do projeto
├── data/<br>
│ ├── extrato.xlsx<br>
│ └── sistema.xlsx<br>
├── logs/<br>
│ └── conciliacao.log<br>
├── output/<br>
│ └── conciliado.xlsx<br>
├── src/<br>
│ ├── conciliar.py<br>
│ └── main.py<br>
├── requirements.txt<br>
└── README.md<br>

---

# Requisitos

- Python 3.11+
- Dependências instaladas via `requirements.txt`

---

# Instalação

## 1. Criar ambiente virtual

python -m venv venv

## 2. Ativar ambiente virtual

Windows PowerShell
venv\Scripts\activate

## 3. Instalar dependências

python -m pip install -r requirements.txt

## Dependências

Arquivo requirements.txt:

pandas
openpyxl

# Formato esperado dos arquivos
## Extrato bancário

Colunas mínimas obrigatórias:

- data
- descricao
- valor

## Coluna opcional:

- documento

# Exemplo:

| data | descricao | valor | documento |
|------|-----------|------|-----------|
| 10/02/2026 | PIX RECEBIDO JOAO | 1500 | L001 |
| 12/02/2026 | TARIFA BANCARIA | -12.50 | |

# Sistema / ERP
## Colunas mínimas obrigatórias:

- data
- historico
- valor

## Coluna opcional:

- id_lancamento

## Exemplo:

| data | historico | valor | id_lancamento |
|------|-----------|------|---------------|
| 10/02/2026 | Recebimento João | 1500 | L001 |
| 12/02/2026 | Tarifa bancária | -12.50 | L003 |

# Como usar
### Ajuda geral

python src/main.py -h

## 1. Gerar arquivos de exemplo

### Cria arquivos de teste na pasta data:

python src/main.py gerar-exemplo

## 2. Validar colunas dos arquivos

### Verifica se os arquivos possuem as colunas mínimas necessárias.

python src/main.py validar

## 3. Executar a conciliação
### Execução padrão

python src/main.py conciliar

### Com parâmetros personalizados
python src/main.py conciliar --dias 2 --tolerancia-valor 0.05

### Desabilitar matching por texto
python src/main.py conciliar --sem-texto

### Ignorar data na chave
python src/main.py conciliar --nao-usar-data

### Usar arquivos específicos
python src/main.py conciliar \
--extrato "C:\temp\extrato.xlsx" \
--sistema "C:\temp\sistema.xlsx" \
--saida "C:\temp\saida.xlsx"

### Parâmetros principais do subcomando conciliar

--extrato                   caminho do arquivo de extrato

--sistema                   caminho do arquivo do sistema

--saida                     caminho do relatório final

--tolerancia-valor          tolerância numérica para comparação de valores

--dias                      janela de dias permitida para conciliação

--usar-data                 considera data na chave de conciliação

--nao-usar-data             ignora data na chave

--use-texto                 habilita matching textual

--sem-texto                 desabilita matching textual

--limite-similaridade       define o score mínimo para aceitar matching por texto


# Estratégia de conciliação

O motor de conciliação segue a seguinte ordem de prioridade:

## 1. Documento exato

### Concilia quando:
documento == id_lancamento

### Status gerado:
OK (DOC)

## 2. Documento dentro do histórico

Quando o documento do extrato aparece dentro do campo historico do sistema.

### Status gerado:
OK (DOC-HIST)

## 3. Valor + janela de dias + similaridade textual

Se não houver match por documento, o sistema tenta:

- Mesmo valor

- Diferença de data dentro da janela configurada

- Melhor similaridade entre descricao e historico

### Status gerado:
OK (JANELA+TEXTO)

## 4. Valor + janela de dias

Quando o matching por texto está desativado.

### Status gerado:
OK (JANELA)

## Saída gerada
### Relatório Excel
Arquivo gerado:
output/conciliado.xlsx

### Abas geradas:
conciliados
so_no_extrato
so_no_sistema
divergencias
resumo

# Log de execução

Arquivo:
logs/conciliacao.log

### Exemplo de log:

```text
2026-03-07 | INFO | Extrato carregado com 4 registros
2026-03-07 | INFO | Sistema carregado com 3 registros
2026-03-07 | INFO | Conciliados: 2
2026-03-07 | INFO | Só no extrato: 2
2026-03-07 | INFO | Só no sistema: 1
2026-03-07 | INFO | Divergências: 1
```

# Tratamento de erros

A aplicação possui códigos de saída consistentes:

# Código	Significado
0	        Execução com sucesso
1	        Erro inesperado
2	        Erro de entrada ou validação

| Código | Significado |
|------|--------|
| 0 | Execução com sucesso |
| 1 | Erro inesperado |
| 2 | Erro de entrada ou validação |

Exemplos:

- Arquivo não encontrado

- Colunas obrigatórias ausentes

- Dados inválidos

#  Casos cobertos pelo projeto

PIX com identificador direto
Documento presente no histórico do sistema
Lançamentos compensados em dias diferentes
Descrições diferentes mas semanticamente próximas
Divergências na mesma data
Lançamentos sem correspondência

# Tecnologias utilizadas

Python
pandas
openpyxl
argparse
logging
dataclasses

# Melhorias futuras

Empacotamento como .exe
Interface gráfica
Testes automatizados
Otimização para grandes volumes
Matching com tolerância de valor
Regras específicas por tipo de transação (PIX, TED, boleto, tarifas)

# Autor

Projeto desenvolvido como parte de um portfólio de automação em Python.
