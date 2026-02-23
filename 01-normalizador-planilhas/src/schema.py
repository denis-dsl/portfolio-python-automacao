"""Normalização e mapeamento de nomes de colunas (schema)."""

from __future__ import annotations

import re
import unicodedata


def canon_col(name: str) -> str:
    """Converte nome de coluna para uma forma canônica (sem acentos, sem símbolos)."""
    s = str(name).strip().lower()

    # remove acentos
    s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

    # separadores comuns viram espaço
    s = re.sub(r"[_\-\/]+", " ", s)

    # remove tudo que não é letra/número/espaço
    s = re.sub(r"[^a-z0-9 ]+", "", s)

    # compacta espaços
    s = re.sub(r"\s+", " ", s).strip()

    return s


# Mapa: canon_col(coluna_origem) -> nome padrão interno
COLUMN_ALIASES: dict[str, str] = {
    # cliente/contrato
    "cliente": "Cliente",
    "nome cliente": "Cliente",
    "contrato": "Contrato",
    "nr contrato": "Contrato",
    "numero contrato": "Contrato",
    # taxa
    "taxa": "Taxa",
    "tx": "Taxa",
    # emissão
    "emissao": "Emissão",
    "emissao contrato": "Emissão",
    "data emissao": "Emissão",
    "data de emissao": "Emissão",
    # prazo
    "prazo": "Prazo",
    "prazo meses": "Prazo",
    # valores
    "vlr liberado": "Vlr Liberado",
    "valor liberado": "Vlr Liberado",
    "valor liberacao": "Vlr Liberado",
    "valor cancelado": "Valor Cancelado",
    "vlr cancelado": "Valor Cancelado",
    "valor pago": "VALOR PAGO",
    "vlr pago": "VALOR PAGO",
    "data pagamento": "Data Pagamento",
    "data do pagamento": "Data Pagamento",
    "pago": "Pago",
    "ted devolvida": "TED/Devolvida",
    "ted devolvido": "TED/Devolvida",
    "teddevolvida": "TED/Devolvida",
    "valor devolvido": "Valor Devolvido",
    "valor devolucao": "Valor Devolvido",
}

# Colunas mínimas para o pipeline funcionar bem
REQUIRED_COLUMNS: set[str] = {
    "Cliente",
    "Contrato",
    "Emissão",
    "Vlr Liberado",
}
