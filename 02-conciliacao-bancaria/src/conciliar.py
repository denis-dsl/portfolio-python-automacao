"""
Módulo responsável pela lógica de conciliação bancária.

Projeto 02 - Conciliação Bancária
Portfólio de Automação em Python

Este módulo contém:
- Padronização dos dados do extrato e sistema
- Criação de chave de conciliação
- Identificação de:
    * Lançamentos conciliados
    * Lançamentos somente no extrato
    * Lançamentos somente no sistema
    * Divergências de valor na mesma data
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
import logging

from dataclasses import dataclass
from typing import Optional
import pandas as pd


logger = logging.getLogger(__name__)

def _normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para comparação:
    - remove acentos
    - uppercase
    - remove pontuação
    - remove espaços duplicados
    """
    if texto is None:
        return ""

    texto = str(texto)

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.upper()

    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    # remove stopwords comuns de extrato (ajuda muito)
    stop = {"PIX", "TED", "DOC", "RECEBIDO", "RECEBIMENTO", "ENVIADA", "ENVIADO", "PAGAMENTO"}
    tokens = [t for t in texto.split() if t not in stop]
    return " ".join(tokens)


def _similaridade(a: str, b: str) -> float:
    """
    Retorna similaridade entre 0 e 1.
    """
    a_n = _normalizar_texto(a)
    b_n = _normalizar_texto(b)
    if not a_n and not b_n:
        return 1.0
    if not a_n or not b_n:
        return 0.0
    return SequenceMatcher(None, a_n, b_n).ratio()


def _doc_valido(doc: object) -> bool:
    """Retorna True se o documento existe e não é vazio."""
    if doc is None:
        return False
    doc_str = str(doc).strip()
    return doc_str != "" and doc_str.lower() != "nan"


def _contem_documento(historico: object, documento: str) -> bool:
    """True se o documento aparece dentro do histórico (case-insensitive)."""
    if not documento:
        return False
    hist = "" if historico is None else str(historico)
    return documento.lower() in hist.lower()


@dataclass
class ConciliaConfig:
    """
    Configurações utilizadas no processo de conciliação.

    Attributes:
        tolerancia_valor (float):
            Define a tolerância para comparação de valores.
            Exemplo: 0.01 permite diferença de até 1 centavo.

        usar_data (bool):
            Define se a data deve ser considerada na chave de conciliação.
            Se False, a conciliação será feita apenas pelo valor.

        tolerancia_dias (int):
            Janela de dias permitida para conciliação entre extrato e sistema.
            Exemplo: 1 permite diferença de até ±1 dia.

        use_texto (bool):
            Ativa o uso de similaridade textual entre descrição do extrato
            e histórico do sistema para ajudar no pareamento.

        limite_similaridade (float):
            Limite mínimo de similaridade textual (0 a 1) para aceitar
            um pareamento quando o matching por texto estiver ativado.

        priorizar_documento (bool):
            Se True, tenta conciliar primeiro por identificadores únicos
            como documento do extrato e id_lancamento do sistema.
            Também tenta encontrar o documento dentro do histórico.
    """

    # tolerância para bater valores (ex: 0.01 = 1 centavo)
    tolerancia_valor: float = 0.01
    # conciliar por data? (se False, concilia só pelo valor)
    usar_data: bool = True
    tolerancia_dias: int = 0
    use_texto: bool = True
    limite_similaridade: float = 0.55  # 0 a 1 (0.55 é um bom começo)
    priorizar_documento: bool = True

def _padronizar_dataframe_extrato(df: pd.DataFrame) -> pd.DataFrame:
    """
    Espera colunas (mínimo): data, descricao, valor
    Opcional: documento
    """
    df = df.copy()

    # normaliza nomes
    df.columns = [c.strip().lower() for c in df.columns]

    # valida mínimo
    obrigatorias = {"data", "descricao", "valor"}
    faltando = obrigatorias - set(df.columns)
    if faltando:
        raise ValueError(f"Extrato: faltando colunas obrigatórias: {sorted(faltando)}")

    # tipos
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    # limpa texto
    df["descricao"] = df["descricao"].astype(str).str.strip()

    # opcional
    if "documento" not in df.columns:
        df["documento"] = ""

    # remove linhas inválidas
    df = df.dropna(subset=["data", "valor"])

    return df


def _padronizar_dataframe_sistema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Espera colunas (mínimo): data, historico, valor
    Opcional: id_lancamento
    """
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    obrigatorias = {"data", "historico", "valor"}
    faltando = obrigatorias - set(df.columns)
    if faltando:
        raise ValueError(f"Sistema: faltando colunas obrigatórias: {sorted(faltando)}")

    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["historico"] = df["historico"].astype(str).str.strip()

    if "id_lancamento" not in df.columns:
        df["id_lancamento"] = ""

    df = df.dropna(subset=["data", "valor"])
    return df


def _criar_chave(df: pd.DataFrame, usar_data: bool, tolerancia: float) -> pd.DataFrame:
    """
    Cria uma chave para conciliação.
    - Valor é arredondado pela tolerância (ex: 0.01)
    - Data pode entrar ou não na chave
    """
    df = df.copy()

    # quantiza valor por tolerância
    # Ex: tolerancia=0.01 -> 1500.004 vira 1500.00
    if tolerancia <= 0:
        raise ValueError("tolerancia_valor deve ser > 0")

    casas = 0
    # tenta estimar casas decimais (0.01 -> 2, 0.1 -> 1, 1 -> 0)
    s = f"{tolerancia:.10f}".rstrip("0")
    if "." in s:
        casas = len(s.split(".")[1])

    df["_valor_q"] = df["valor"].round(casas)

    if usar_data:
        df["_data_q"] = df["data"].dt.strftime("%Y-%m-%d")
        df["_chave"] = df["_data_q"] + "|" + df["_valor_q"].map(lambda x: f"{x:.{casas}f}")
    else:
        df["_chave"] = df["_valor_q"].map(lambda x: f"{x:.{casas}f}")

    return df


def conciliar(
    extrato_df: pd.DataFrame,
    sistema_df: pd.DataFrame,
    config: Optional[ConciliaConfig] = None
) -> dict[str, pd.DataFrame]:
    """
    Executa a conciliação entre lançamentos do extrato bancário e do sistema.

    O processo segue uma ordem de prioridade para encontrar correspondências:

    1. Documento exato:
       - Concilia quando `extrato.documento == sistema.id_lancamento`.

    2. Documento dentro do histórico:
       - Concilia quando o valor de `documento` aparece dentro do campo
         `historico` do sistema.

    3. Conciliação por valor e janela de dias:
       - Procura lançamentos com o mesmo valor e diferença de data dentro
         do limite definido em `config.tolerancia_dias`.

    4. Similaridade textual (opcional):
       - Quando `config.use_texto=True`, utiliza similaridade entre
         `descricao` (extrato) e `historico` (sistema) para escolher
         o melhor candidato.

    O resultado é classificado em quatro categorias:
        - conciliados
        - so_no_extrato
        - so_no_sistema
        - divergencias (mesma data, valor diferente)

    Parameters
    ----------
    extrato_df : pd.DataFrame
        DataFrame contendo os lançamentos do extrato bancário.

    sistema_df : pd.DataFrame
        DataFrame contendo os lançamentos registrados no sistema/ERP.

    config : ConciliaConfig, optional
        Configurações que controlam o comportamento da conciliação.

    Returns
    -------
    dict[str, pd.DataFrame]
        Dicionário contendo os DataFrames resultantes:
        {
            "conciliados": lançamentos conciliados,
            "so_no_extrato": lançamentos presentes apenas no extrato,
            "so_no_sistema": lançamentos presentes apenas no sistema,
            "divergencias": lançamentos com mesma data mas valores diferentes,
            "resumo": contagem agregada de cada categoria
        }
    """
    config = config or ConciliaConfig()

    e = _padronizar_dataframe_extrato(extrato_df)
    s = _padronizar_dataframe_sistema(sistema_df)

    e = _criar_chave(e, usar_data=config.usar_data, tolerancia=config.tolerancia_valor)
    s = _criar_chave(s, usar_data=config.usar_data, tolerancia=config.tolerancia_valor)

    # 1)
    # ========================================
    # MATCH COM JANELA DE DIAS
    # ========================================

    if config.tolerancia_dias > 0:
        conciliados_list: list[dict] = []
        extrato_conciliado_idx: set[int] = set()
        sistema_conciliado_idx: set[int] = set()

        for _, row_e in e.iterrows():
            # sistema disponível (evita conciliar o mesmo item do sistema 2x)
            s_disponivel = s.loc[~s.index.isin(sistema_conciliado_idx)]

            row_s = None
            score = None
            status = None

            # ---------------------------------------------------------
            # 0) PRIORIDADE: documento (extrato) == id_lancamento (sistema)
            # ---------------------------------------------------------
            doc_str = str(row_e.get("documento", "")).strip()

            if config.priorizar_documento and _doc_valido(doc_str):
                candidatos_doc = s_disponivel[
                    s_disponivel["id_lancamento"].astype(str).str.strip() == doc_str
                ]

                if not candidatos_doc.empty:
                    row_s = candidatos_doc.iloc[0]
                    status = "OK (DOC)"
                    score = None  # não faz sentido score aqui

            # 0.2) PRIORIDADE: documento aparece no histórico
            if row_s is None and config.priorizar_documento and _doc_valido(doc_str):
                mask_doc_hist = [
                    _contem_documento(historico, doc_str)
                    for historico in s_disponivel["historico"]
                ]
                candidatos_hist = s_disponivel[mask_doc_hist]

                if not candidatos_hist.empty:
                    row_s = candidatos_hist.iloc[0]
                    status = "OK (DOC-HIST)"
                    score = None

            # ---------------------------------------------------------
            # 1) Se não conciliou por DOC, segue o fluxo normal
            # ---------------------------------------------------------
            if row_s is None:
                candidatos = s_disponivel[
                    (s_disponivel["valor"].round(2) == round(row_e["valor"], 2))
                    & (
                        (s_disponivel["data"] - row_e["data"]).abs().dt.days
                        <= config.tolerancia_dias
                    )
                ]

                if candidatos.empty:
                    continue

                if config.use_texto:
                    candidatos = candidatos.copy()
                    descricao_extrato = row_e["descricao"]

                    scores = []
                    diff_valores = []

                    for _, cand in candidatos.iterrows():
                        scores.append(_similaridade(descricao_extrato, cand["historico"]))
                        diff_valores.append(abs(float(row_e["valor"]) - float(cand["valor"])))

                    candidatos["_score_texto"] = scores
                    candidatos["_diff_valor"] = diff_valores

                    candidatos = candidatos.sort_values(
                        by=["_score_texto", "_diff_valor"],
                        ascending=[False, True],
                    )

                    melhor = candidatos.iloc[0]
                    score = float(melhor["_score_texto"])

                    if score < config.limite_similaridade:
                        continue

                    row_s = melhor
                    status = "OK (JANELA+TEXTO)"

                else:
                    candidatos = candidatos.copy()

                    candidatos["_diff_valor"] = [
                        abs(float(row_e["valor"]) - float(v))
                        for v in candidatos["valor"]
                    ]

                    candidatos = candidatos.sort_values("_diff_valor")

                    row_s = candidatos.iloc[0]
                    status = "OK (JANELA)"

            # ---------------------------------------------------------
            # 2) Registrar conciliação (vale para DOC e para fluxo normal)
            # ---------------------------------------------------------
            extrato_conciliado_idx.add(row_e.name)
            sistema_conciliado_idx.add(row_s.name)

            conciliados_list.append({
                "data_extrato": row_e["data"],
                "descricao": row_e["descricao"],
                "documento": row_e["documento"],
                "valor_extrato": row_e["valor"],
                "data_sistema": row_s["data"],
                "historico": row_s["historico"],
                "id_lancamento": row_s["id_lancamento"],
                "valor_sistema": row_s["valor"],
                "score_texto": score,
                "status": status,
            })

        conciliados = pd.DataFrame(conciliados_list)

        # linhas não conciliadas (modo janela)
        so_no_extrato = e.loc[
            ~e.index.isin(extrato_conciliado_idx),
            ["data", "descricao", "documento", "valor"],
        ].copy()
        so_no_extrato["status"] = "SÓ NO EXTRATO"

        so_no_sistema = s.loc[
            ~s.index.isin(sistema_conciliado_idx),
            ["data", "historico", "id_lancamento", "valor"],
        ].copy()
        so_no_sistema["status"] = "SÓ NO SISTEMA"

    else:
        # modo antigo por chave
        m = e.merge(
            s,
            on="_chave",
            how="inner",
            suffixes=("_extrato", "_sistema"),
        )

        conciliados = m[[
            "data_extrato", "descricao", "documento", "valor_extrato",
            "data_sistema", "historico", "id_lancamento", "valor_sistema",
        ]].copy()
        conciliados["score_texto"] = pd.NA
        conciliados["status"] = "OK"

        # Só no extrato (modo chave)
        so_no_extrato = e.merge(s[["_chave"]], on="_chave", how="left", indicator=True)
        so_no_extrato = so_no_extrato[so_no_extrato["_merge"] == "left_only"].drop(
            columns=["_merge"]
        )
        so_no_extrato = so_no_extrato[["data", "descricao", "documento", "valor"]].copy()
        so_no_extrato["status"] = "SÓ NO EXTRATO"

        # Só no sistema (modo chave)
        so_no_sistema = s.merge(e[["_chave"]], on="_chave", how="left", indicator=True)
        so_no_sistema = so_no_sistema[so_no_sistema["_merge"] == "left_only"].drop(
            columns=["_merge"]
        )
        so_no_sistema = so_no_sistema[["data", "historico", "id_lancamento", "valor"]].copy()
        so_no_sistema["status"] = "SÓ NO SISTEMA"

    # 4) Divergências (mesma data, valor diferente) - pareamento 1:1
    divergencias_list: list[dict] = []

    if config.usar_data:
        # usa cópias sem os conciliados do modo janela (se existir)
        e_div = e.copy()
        s_div = s.copy()

        # agrupa por data
        for data_ref, e_dia in e_div.groupby(e_div["data"].dt.date):
            s_dia = s_div[s_div["data"].dt.date == data_ref]

            if s_dia.empty:
                continue

            usados_sistema: set[int] = set()

            for _, row_e in e_dia.iterrows():
                # candidatos ainda não usados do sistema no mesmo dia
                s_disp = s_dia.loc[~s_dia.index.isin(usados_sistema)]
                if s_disp.empty:
                    continue

                # escolhe candidato pelo texto se estiver habilitado, senão pega o primeiro
                if config.use_texto:
                    descricao_extrato = row_e["descricao"]
                    scores = []
                    for historico in s_disp["historico"]:
                        scores.append(_similaridade(descricao_extrato, historico))
                    s_disp = s_disp.copy()
                    s_disp["_score_texto"] = scores
                    s_disp = s_disp.sort_values("_score_texto", ascending=False)
                    row_s = s_disp.iloc[0]
                    score = float(row_s["_score_texto"])
                else:
                    row_s = s_disp.iloc[0]
                    score = None

                usados_sistema.add(row_s.name)

                # se valor for diferente, registra divergência
                if round(float(row_e["valor"]), 2) != round(float(row_s["valor"]), 2):
                    divergencias_list.append({
                        "data_extrato": row_e["data"],
                        "descricao": row_e["descricao"],
                        "documento": row_e["documento"],
                        "valor_extrato": row_e["valor"],
                        "data_sistema": row_s["data"],
                        "historico": row_s["historico"],
                        "id_lancamento": row_s["id_lancamento"],
                        "valor_sistema": row_s["valor"],
                        "score_texto": pd.NA if status in {"OK (DOC)", "OK (DOC-HIST)"} else score,
                        "diferenca": float(row_e["valor"]) - float(row_s["valor"]),
                        "status": "DIVERGÊNCIA (MESMA DATA)",
                    })

    divergencias = pd.DataFrame(divergencias_list)

    resumo = pd.DataFrame([
        {"metrica": "conciliados", "qtd": int(len(conciliados))},
        {"metrica": "so_no_extrato", "qtd": int(len(so_no_extrato))},
        {"metrica": "so_no_sistema", "qtd": int(len(so_no_sistema))},
        {"metrica": "divergencias", "qtd": int(len(divergencias))},
    ])

    return {
        "conciliados": conciliados,
        "so_no_extrato": so_no_extrato,
        "so_no_sistema": so_no_sistema,
        "divergencias": divergencias,
        "resumo": resumo,
    }
