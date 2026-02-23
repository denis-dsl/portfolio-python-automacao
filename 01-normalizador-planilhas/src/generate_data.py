"""Criação de artifacts de execução (pasta por run + summary.json)."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from random import choice, randint, random
from typing import Any

import pandas as pd
from faker import Faker

fake = Faker("pt_BR")


def _money_mixed(value: float) -> str:
    """
    Devolve dinheiro em formatos misturados de propósito:
    - '3.000,00'
    - '3,000.00'
    - '3000.00'
    - '3.000'
    """
    fmt = choice(["pt", "en", "dot", "int"])
    if fmt == "pt":
        s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return s  # 3.000,00
    if fmt == "en":
        return f"{value:,.2f}"  # 3,000.00
    if fmt == "dot":
        return f"{value:.2f}"  # 3000.00
    return str(int(round(value)))  # 3000


def _date_mixed(d: date) -> str:
    """
    Datas em formatos misturados + casos com '() 02/01/2026'
    """
    fmt = choice(["ddmmyyyy", "yyyymmdd", "paren", "iso"])
    if fmt == "ddmmyyyy":
        return d.strftime("%d/%m/%Y")
    if fmt == "yyyymmdd":
        return d.strftime("%Y-%m-%d")
    if fmt == "iso":
        return d.isoformat()
    return f"() {d.strftime('%d/%m/%Y')}"

def _round2(x: float) -> float:
    return round(float(x), 2)

def _dv_mod11(number: str) -> str:
    """Dígito verificador Mod11 simples (pra parecer bancário)."""
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for i, ch in enumerate(reversed(number)):
        total += int(ch) * weights[i % len(weights)]
    dv = 11 - (total % 11)
    if dv >= 10:
        dv = 0
    return str(dv)

def _generate_contract() -> str:
    """
    Gera contrato bancário fictício:
    - 12 dígitos iniciando com 86 ou 97
    - + DV Mod11
    - formato: 861234567890-3
    """
    prefix = choice(["86", "97"])
    body = f"{randint(0, 9999999999):010d}"
    base = prefix + body
    return f"{base}-{_dv_mod11(base)}"

def _choose_scenario() -> str:
    """
    Distribuição (ajuste depois se quiser):
    25% emitido_aberto
    10% cancelado_total
    35% pago
    12% pago_devolvido
    10% refin_substituicao
    8%  cancelado_pos_pagamento
    """
    r = randint(1, 100)
    if r <= 25:
        return "emitido_aberto"
    if r <= 35:
        return "cancelado_total"
    if r <= 70:
        return "pago"
    if r <= 82:
        return "pago_devolvido"
    if r <= 92:
        return "refin_substituicao"
    return "cancelado_pos_pagamento"

def _simulate_contract_events(emissao: date, vlr_liberado: float) -> dict[str, Any]:
    scenario = _choose_scenario()

    pago: str = ""
    data_pagamento: str = ""
    valor_pago: float | None = None
    valor_cancelado: float | None = None
    ted: str = ""
    valor_devolvido: float | None = None

    def set_pago() -> None:
        nonlocal pago, data_pagamento, valor_pago
        pago = "SIM"
        data_pagamento = _date_mixed(emissao + timedelta(days=randint(0, 12)))
        # pago parcial ou total: 20% a 100%
        valor_pago = _round2(vlr_liberado * (0.2 + random() * 0.8))

    def set_nao_pago() -> None:
        nonlocal pago
        pago = "NÃO"

    if scenario == "emitido_aberto":
        # Contrato só emitido: nada aconteceu ainda
        if random() < 0.5:
            set_nao_pago()

    elif scenario == "cancelado_total":
        # Cenário 1: cancelou antes de pagar
        set_nao_pago()
        fee = 0.0 if random() < 0.85 else _round2(vlr_liberado * 0.01)
        valor_cancelado = _round2(max(vlr_liberado - fee, 0))

    elif scenario == "pago":
        set_pago()

    elif scenario == "pago_devolvido":
        set_pago()
        ted = "SIM"
        frac = 0.2 + random() * 0.8  # 20% a 100%
        valor_devolvido = _round2((valor_pago or 0) * frac)

    elif scenario == "refin_substituicao":
        # Cenário 3: encerrou por substituição/refin
        if random() < 0.6:
            set_pago()
            saldo = max(vlr_liberado - (valor_pago or 0), 0)
            ajuste = saldo * (random() * 0.03)  # até 3%
            valor_cancelado = _round2(max(saldo + ajuste, 0))
        else:
            set_nao_pago()
            frac = 0.6 + random() * 0.4  # 60% a 100%
            valor_cancelado = _round2(vlr_liberado * frac)

    else:  # cancelado_pos_pagamento (cenário 2)
        set_pago()
        saldo = max(vlr_liberado - (valor_pago or 0), 0)
        frac = 0.5 + random() * 0.5  # 50% a 100% do saldo
        valor_cancelado = _round2(saldo * frac)

        if random() < 0.25:
            ted = "SIM"
            valor_devolvido = _round2(min((valor_pago or 0) * (0.1 + random() * 0.5),
                                          (valor_pago or 0)))

    return {
        "Pago": pago,
        "Data Pagamento": data_pagamento,
        "VALOR PAGO": valor_pago,
        "Valor Cancelado": valor_cancelado,
        "TED/Devolvida": ted,
        "Valor Devolvido": valor_devolvido,
    }

def generate_excel(path: Path, rows: int = 200, mode: str = "realistic") -> Path:
    """
    Gera um Excel fictício semelhante a relatórios corporativos.
    """
    mode = mode.strip().lower()
    if mode not in {"simple", "realistic"}:
        raise ValueError("mode deve ser 'simple' ou 'realistic'")

    data: list[dict[str, Any]] = []
    start = date.today() - timedelta(days=60)

    for _ in range(rows):
        emissao = start + timedelta(days=randint(0, 60))
        vlr_liberado = _round2(randint(1500, 8000) + random())
        contrato = _generate_contract()

        # defaults
        pago = ""
        valor_cancelado: float | None = None
        valor_pago: float | None = None
        data_pagamento = ""
        ted = ""
        valor_devolvido: float | None = None

        if mode == "simple":
            # --- seu comportamento atual (preservado) ---
            pago = choice(["SIM", "NÃO", "", "NAO"])

            valor_cancelado = 0.0 if random() < 0.7 else _round2(randint(500, 6000) + random())

            if pago in {"SIM"}:
                valor_pago = _round2(randint(200, max(200, int(vlr_liberado))) + random())
                data_pagamento = _date_mixed(emissao + timedelta(days=randint(0, 10)))

            ted = choice(["SIM", "NÃO", ""])
            if ted == "SIM":
                valor_devolvido = _round2(randint(50, 1500) + random())

        else:
            # --- modo realista (coerente) ---
            events = _simulate_contract_events(emissao, vlr_liberado)
            pago = events["Pago"]
            data_pagamento = events["Data Pagamento"]
            valor_pago = events["VALOR PAGO"]
            valor_cancelado = events["Valor Cancelado"]
            ted = events["TED/Devolvida"]
            valor_devolvido = events["Valor Devolvido"]

        data.append(
            {
                "Cliente": fake.name().upper(),
                "Contrato": contrato,
                "Taxa": choice(["7.90", "10.50", "14.93", "9,20"]),
                "Emissão": _date_mixed(emissao),
                "Prazo": choice([6, 12, 15, 18, 24]),
                "Vlr Liberado": _money_mixed(vlr_liberado),
                "Valor Cancelado": _money_mixed(valor_cancelado) if valor_cancelado else "",
                "Pago": pago,
                "Data Pagamento": data_pagamento,
                "VALOR PAGO": _money_mixed(valor_pago) if valor_pago else "",
                "TED/Devolvida": ted,
                "Valor Devolvido": _money_mixed(valor_devolvido) if valor_devolvido else "",
            }
        )

    df = pd.DataFrame(data)

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)
    return path
