# Python Automation Portfolio

Coleção de projetos de automação em Python com foco corporativo, qualidade de código e execução via GitHub Actions.

![CI Global](https://github.com/denis-dsl/portfolio-python-automacao/actions/workflows/ci.yml/badge.svg)
![Projeto 01](https://github.com/denis-dsl/portfolio-python-automacao/actions/workflows/normalizador.yml/badge.svg)
![Projeto 02](https://github.com/denis-dsl/portfolio-python-automacao/actions/workflows/conciliacao.yml/badge.svg)

## Objetivo

Este repositório reúne projetos práticos de automação desenvolvidos em Python, com ênfase em:

- organização de código
- qualidade e padronização
- testes automatizados
- evidências de execução
- integração contínua com GitHub Actions

## Projetos

### 01 - Excel Normalizer
CLI para geração, validação e normalização de planilhas Excel, com saída auditável e evidências de processamento.

**Principais pontos:**
- geração de dados de exemplo
- normalização de planilhas
- exportação de evidências
- lint e testes automatizados
- envio de artifacts por workflow

➡ Veja detalhes em `01-normalizador-planilhas/README.md`

---

### 02 - Conciliação Bancária
Automação para validação e conciliação de arquivos bancários, com geração de saída consolidada e log de execução.

**Principais pontos:**
- geração de arquivos de exemplo
- validação de entrada
- conciliação automatizada
- saída em Excel
- log do processo
- envio de artifacts por workflow

➡ Veja detalhes em `02-conciliacao-bancaria/README.md`

## Workflows

O repositório possui workflows separados para responsabilidades diferentes:

- **CI Global**: validação manual do repositório
- **Projeto 01 - Excel Normalizer**: execução do projeto, geração de evidências e envio por e-mail
- **Projeto 02 - Conciliação Bancária**: execução do projeto, geração de evidências e envio por e-mail

## Tecnologias utilizadas

- Python
- Pytest
- Ruff
- GitHub Actions
- OpenPyXL / automação de planilhas
- CLI em Python

## Estrutura do repositório

```text
.github/workflows/
01-normalizador-planilhas/
02-conciliacao-bancaria/
README.md
```

## Diferenciais do portfólio

- projetos organizados por domínio
- pipelines separados por responsabilidade
- evidências de execução
- automação com foco em cenário corporativo
- preocupação com manutenção e escalabilidade

## Autor

Denis dos Santos Lima
GitHub: denis-dsl