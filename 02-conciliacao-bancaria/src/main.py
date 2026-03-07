"""
CLI - Conciliação bancária (Projeto 02).
Portfólio de Automação em Python
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from conciliar import conciliar, ConciliaConfig

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "conciliacao.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# -----------------------------
# Helpers
# -----------------------------
def carregar_arquivos(extrato_path: Path, sistema_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega os arquivos de extrato e sistema em DataFrames."""
    if not extrato_path.exists():
        logger.error("Arquivo de extrato não encontrado: %s", extrato_path)
        raise FileNotFoundError(f"Não achei: {extrato_path}")

    if not sistema_path.exists():
        logger.error("Arquivo de sistema não encontrado: %s", sistema_path)
        raise FileNotFoundError(f"Não achei: {sistema_path}")

    extrato_df = pd.read_excel(extrato_path)
    sistema_df = pd.read_excel(sistema_path)
    return extrato_df, sistema_df


def salvar_relatorio(saida: Path, resultado: dict[str, pd.DataFrame]) -> None:
    """Salva o dicionário de DataFrames em um Excel com múltiplas abas."""
    saida.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(saida, engine="openpyxl") as writer:
        for aba, df in resultado.items():
            df.to_excel(writer, sheet_name=aba[:31], index=False)

    logger.info("Relatório gerado em: %s", saida)


def validar_colunas(extrato_df: pd.DataFrame, sistema_df: pd.DataFrame) -> list[str]:
    """
    Valida se as colunas mínimas existem nos arquivos.
    Retorna uma lista de mensagens de erro (vazia se estiver ok).
    """
    erros: list[str] = []

    extrato_cols = {c.strip().lower() for c in extrato_df.columns}
    sistema_cols = {c.strip().lower() for c in sistema_df.columns}

    extrato_obrig = {"data", "descricao", "valor"}
    sistema_obrig = {"data", "historico", "valor"}

    faltando_extrato = extrato_obrig - extrato_cols
    faltando_sistema = sistema_obrig - sistema_cols

    if faltando_extrato:
        erros.append(f"Extrato: faltando colunas: {sorted(faltando_extrato)}")

    if faltando_sistema:
        erros.append(f"Sistema: faltando colunas: {sorted(faltando_sistema)}")

    return erros


def gerar_exemplo(extrato_path: Path, sistema_path: Path) -> None:
    """Gera arquivos exemplo de extrato e sistema (xlsx)."""
    extrato_path.parent.mkdir(parents=True, exist_ok=True)
    sistema_path.parent.mkdir(parents=True, exist_ok=True)

    extrato = pd.DataFrame([
        {"data": "10/02/2026", "descricao": "PIX RECEBIDO JOAO",
         "valor": 1500.00, "documento": "E2E123"},
        {"data": "11/02/2026", "descricao": "TED ENVIADA MARIA",
         "valor": -800.00, "documento": "TED998"},
        {"data": "12/02/2026", "descricao": "TARIFA BANCARIA",
         "valor": -12.50, "documento": ""},
        {"data": "13/02/2026", "descricao": "PIX RECEBIDO TATIANA",
         "valor": 900.00, "documento": "E2E999"},
    ])

    sistema = pd.DataFrame([
        {"data": "10/02/2026", "historico": "Recebimento João",
         "valor": 1500.00, "id_lancamento": "L001"},
        {"data": "11/02/2026", "historico": "Pagamento Maria",
         "valor": -900.00, "id_lancamento": "L002"},
        {"data": "12/02/2026", "historico": "Tarifa bancária",
         "valor": -12.50, "id_lancamento": "L003"},
    ])

    extrato.to_excel(extrato_path, index=False)
    sistema.to_excel(sistema_path, index=False)

    logger.info("Arquivos exemplo gerados:")
    logger.info("Extrato: %s", extrato_path)
    logger.info("Sistema: %s", sistema_path)


# -----------------------------
# CLI
# -----------------------------
def build_parser() -> argparse.ArgumentParser:
    """Cria o parser principal com subcomandos."""
    parser = argparse.ArgumentParser(
        prog="conciliacao-bancaria",
        description="CLI de conciliação bancária (extrato x sistema).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # conciliar
    p_conc = sub.add_parser("conciliar", help="Executa conciliação e gera relatório.")
    p_conc.add_argument("--extrato", default=str(DATA / "extrato.xlsx"),
                        help="Caminho do extrato (.xlsx).")
    p_conc.add_argument("--sistema", default=str(DATA / "sistema.xlsx"),
                        help="Caminho do sistema (.xlsx).")
    p_conc.add_argument("--saida", default=str(OUT / "conciliado.xlsx"),
                        help="Caminho da saída (.xlsx).")

    p_conc.add_argument("--tolerancia-valor", type=float, default=0.01,
                        help="Tolerância de valor (ex: 0.01).")
    p_conc.add_argument("--dias", type=int, default=1,
                        help="Janela de dias (±N). Use 0 para desativar.")
    p_conc.add_argument("--usar-data", action="store_true",
                        help="Considera data na chave (default).")
    p_conc.add_argument("--nao-usar-data", action="store_true",
                        help="Ignora data na chave (só valor).")

    p_conc.add_argument("--use-texto", action="store_true",
                        help="Habilita matching por texto (default).")
    p_conc.add_argument("--sem-texto", action="store_true",
                        help="Desabilita matching por texto.")
    p_conc.add_argument("--limite-similaridade", type=float, default=0.55,
                        help="Limite mínimo (0 a 1).")

    # validar
    p_val = sub.add_parser("validar", help="Valida colunas mínimas dos arquivos.")
    p_val.add_argument("--extrato", default=str(DATA / "extrato.xlsx"),
                       help="Caminho do extrato (.xlsx).")
    p_val.add_argument("--sistema", default=str(DATA / "sistema.xlsx"),
                       help="Caminho do sistema (.xlsx).")

    # gerar-exemplo
    p_ex = sub.add_parser("gerar-exemplo", help="Gera arquivos exemplo de extrato e sistema.")
    p_ex.add_argument("--extrato", default=str(DATA / "extrato.xlsx"),
                      help="Onde salvar o extrato exemplo.")
    p_ex.add_argument("--sistema", default=str(DATA / "sistema.xlsx"),
                      help="Onde salvar o sistema exemplo.")

    return parser


def cmd_conciliar(args: argparse.Namespace) -> None:
    """Executa o subcomando conciliar."""
    extrato_path = Path(args.extrato)
    sistema_path = Path(args.sistema)
    saida_path = Path(args.saida)

    usar_data = True
    if args.nao_usar_data:
        usar_data = False
    if args.usar_data:
        usar_data = True

    use_texto = True
    if args.sem_texto:
        use_texto = False
    if args.use_texto:
        use_texto = True

    logger.info("Iniciando conciliação")
    logger.info("Extrato: %s", extrato_path)
    logger.info("Sistema: %s", sistema_path)
    logger.info("Saída: %s", saida_path)

    extrato_df, sistema_df = carregar_arquivos(extrato_path, sistema_path)

    # valida rápido colunas antes de conciliar
    erros = validar_colunas(extrato_df, sistema_df)
    if erros:
        for e in erros:
            logger.error(e)
        raise SystemExit(2)

    logger.info("Extrato carregado com %d registros", len(extrato_df))
    logger.info("Sistema carregado com %d registros", len(sistema_df))

    config = ConciliaConfig(
        tolerancia_valor=args.tolerancia_valor,
        usar_data=usar_data,
        tolerancia_dias=args.dias,
        use_texto=use_texto,
        limite_similaridade=args.limite_similaridade,
    )

    logger.info(
        "Config: tolerancia_valor=%.4f | usar_data=%s | dias=%d | use_texto=%s | limite_sim=%.2f",
        config.tolerancia_valor,
        config.usar_data,
        config.tolerancia_dias,
        config.use_texto,
        config.limite_similaridade,
    )

    resultado = conciliar(extrato_df, sistema_df, config=config)
    salvar_relatorio(saida_path, resultado)

    logger.info("Conciliados: %d", len(resultado["conciliados"]))
    logger.info("Só no extrato: %d", len(resultado["so_no_extrato"]))
    logger.info("Só no sistema: %d", len(resultado["so_no_sistema"]))
    logger.info("Divergências: %d", len(resultado["divergencias"]))
    logger.info("Resumo:\n%s", resultado["resumo"].to_string(index=False))
    logger.info("Finalizado com sucesso")


def cmd_validar(args: argparse.Namespace) -> None:
    """Executa o subcomando validar."""
    extrato_path = Path(args.extrato)
    sistema_path = Path(args.sistema)

    extrato_df, sistema_df = carregar_arquivos(extrato_path, sistema_path)
    erros = validar_colunas(extrato_df, sistema_df)

    if erros:
        for e in erros:
            logger.error(e)
        raise SystemExit(2)

    logger.info("Validação OK. Colunas mínimas presentes.")


def cmd_gerar_exemplo(args: argparse.Namespace) -> None:
    """Executa o subcomando gerar-exemplo."""
    gerar_exemplo(Path(args.extrato), Path(args.sistema))


def main() -> None:
    """
    Ponto de entrada principal da aplicação CLI.

    Responsável por:
    - Interpretar argumentos de linha de comando.
    - Direcionar para o subcomando apropriado (conciliar, validar, gerar-exemplo).
    - Tratar exceções de forma controlada.
    - Garantir códigos de saída padronizados:
        0 -> sucesso
        1 -> erro inesperado
        2 -> erro de uso/dados/entrada
    """

    parser = build_parser()

    try:
        args = parser.parse_args()

        if args.command == "conciliar":
            cmd_conciliar(args)
        elif args.command == "validar":
            cmd_validar(args)
        elif args.command == "gerar-exemplo":
            cmd_gerar_exemplo(args)
        else:
            logger.error("Comando inválido.")
            raise SystemExit(2)

    except FileNotFoundError as e:
        logger.error("%s", e)
        raise SystemExit(2) from e

    except ValueError as e:
        logger.error("Dados inválidos: %s", e)
        raise SystemExit(2) from e

    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()
