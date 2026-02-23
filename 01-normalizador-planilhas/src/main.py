"""CLI do normalizador de planilhas."""

from __future__ import annotations

from pathlib import Path

import typer
from loguru import logger

from src.generate_data import generate_excel
from src.normalize import normalize_excel

app = typer.Typer(no_args_is_help=True)


@app.command()
def generate(
    rows: int = 200,
    out: str = "data/exemplo_sujo.xlsx",
    mode: str = typer.Option("realistic", help="simple|realistic"),
) -> None:
    """Gera uma planilha fictícia (simples ou realista) para testes."""
    out_path = Path(out)
    created = generate_excel(out_path, rows=rows, mode=mode)
    logger.info(f"Arquivo gerado: {created.resolve()}")


@app.command()
def normalize(
    input_file: str,
    output_file: str,
    strict: bool = typer.Option(False, help="Falha se houver inconsistências."),
) -> None:
    """Normaliza uma planilha Excel."""
    inp = Path(input_file)
    out = Path(output_file)

    if not inp.exists():
        raise typer.BadParameter(f"Arquivo de entrada não encontrado: {inp}")

    logger.info(f"Lendo arquivo: {inp}")
    logger.info(f"Salvando em: {out}")
    normalize_excel(inp, out, strict=strict)


if __name__ == "__main__":
    app()
