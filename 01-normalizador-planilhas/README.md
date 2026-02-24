# 01 - Excel Normalizer (CLI)

Ferramenta de linha de comando para **normalização, validação e auditoria de planilhas Excel** com dados inconsistentes.

Projeto com foco em cenários corporativos onde arquivos recebidos possuem:
- formatos mistos (pt-BR / en-US)
- datas inconsistentes
- valores monetários mal formatados
- regras de negócio violadas
- ausência de rastreabilidade de execução

---

## 🎯 Objetivo

Automatizar a limpeza e padronização de planilhas, gerando:

- Arquivo limpo
- Relatório de inconsistências
- Summary com métricas de transformação
- Pasta de execução versionada por timestamp

---

## 🚀 Funcionalidades

- CLI com Typer
- Geração de dados fictícios:
  - `--mode simple` (stress test)
  - `--mode realistic` (simulação financeira coerente)
- Normalização:
  - Datas (DD/MM/YYYY, ISO, strings com ruído)
  - Moedas (`3.000,00`, `3,000.00`, etc.)
  - Flags (`SIM`, `NÃO`, `NAO`, vazio)
- Validação com severidade (`WARN` / `ERROR`)
- Modo `--strict`
- Artifacts auditáveis por execução

---

## 🛠 Como usar (Python)

Dentro da pasta do projeto:

```powershell
python -m src.main generate --mode realistic --rows 200 --out data\input.xlsx
python -m src.main normalize data\input.xlsx output\clean.xlsx --strict