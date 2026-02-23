"""Validação e relatório de inconsistências (WARN/ERROR) com auditoria."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class Issue:
    severity: str  # "ERROR" | "WARN"
    row: int | None
    contrato: str | None
    cliente: str | None
    message: str


def _s(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def validate_dataframe(df: pd.DataFrame) -> list[Issue]:
    """Valida regras de negócio e devolve lista de issues."""
    issues: list[Issue] = []

    for idx, row in df.iterrows():
        cliente = _s(row.get("Cliente"))
        contrato = _s(row.get("Contrato"))

        pago = row.get("Pago")
        data_pag = row.get("Data Pagamento")
        vlr_pago = row.get("VALOR PAGO")

        ted = row.get("TED/Devolvida")
        vlr_dev = row.get("Valor Devolvido")

        # Contrato/Cliente vazios = ERROR
        if not contrato:
            issues.append(Issue("ERROR", idx, None, cliente, "Contrato vazio"))
        if not cliente:
            issues.append(Issue("ERROR", idx, contrato, None, "Cliente vazio"))

        # Pago = SIM -> precisa data e valor
        if pago == "SIM":
            if pd.isna(data_pag):
                issues.append(
                    Issue("ERROR", idx, contrato, cliente, "Pago=SIM mas Data Pagamento vazio")
                )
            if pd.isna(vlr_pago):
                issues.append(
                    Issue("ERROR", idx, contrato, cliente, "Pago=SIM mas VALOR PAGO vazio")
                )

        # Se não pago, mas valor pago preenchido -> WARN (às vezes é pré-lançamento)
        if pago != "SIM" and (not pd.isna(vlr_pago)):
            issues.append(
                Issue("WARN", idx, contrato, cliente, "Pago!=SIM mas VALOR PAGO preenchido")
            )

        # TED/Devolvida = SIM -> precisa valor devolvido
        if ted == "SIM" and pd.isna(vlr_dev):
            issues.append(
                Issue(
                    "ERROR", idx, contrato, cliente, "TED/Devolvida=SIM mas Valor Devolvido vazio"
                )
            )

    return issues


def write_issues_csv(issues: Iterable[Issue], path: Path) -> bool:
    """Escreve issues em CSV. Retorna True se houver issues."""
    issues = list(issues)
    if not issues:
        if path.exists():
            path.unlink()
        return False

    rows = [
        {
            "Severidade": i.severity,
            "Linha": i.row,
            "Contrato": i.contrato,
            "Cliente": i.cliente,
            "Mensagem": i.message,
        }
        for i in issues
    ]
    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return True


def has_errors(issues: Iterable[Issue]) -> bool:
    """True se houver pelo menos um ERROR."""
    return any(i.severity == "ERROR" for i in issues)
