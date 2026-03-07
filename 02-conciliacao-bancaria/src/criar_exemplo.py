''' Cria exemplo '''

from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

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

extrato.to_excel(DATA / "extrato.xlsx", index=False)
sistema.to_excel(DATA / "sistema.xlsx", index=False)

print("✅ Arquivos criados na pasta data/")
