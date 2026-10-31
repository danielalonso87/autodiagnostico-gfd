"""
Testa a conexão com o Google Sheets usando o .streamlit/secrets.toml.

Uso (na pasta do projeto):
    python ferramentas/testar_planilha.py

Se der certo, aparece o nome da planilha e a aba "Leads" é criada com o cabeçalho.
Nenhum lead é gravado.
"""

import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import gspread  # noqa: E402

from diagnostico.planilha import COLUNAS  # noqa: E402


def main() -> None:
    caminho = RAIZ / ".streamlit" / "secrets.toml"
    if not caminho.exists():
        sys.exit("Não achei .streamlit/secrets.toml. Copie o secrets.toml.example e preencha.")
    segredos = tomllib.loads(caminho.read_text(encoding="utf-8"))

    try:
        cliente = gspread.service_account_from_dict(segredos["gcp_service_account"])
        planilha = cliente.open_by_key(segredos["planilha"]["id"])
    except gspread.exceptions.SpreadsheetNotFound:
        sys.exit("Planilha não encontrada. Confira o ID e se ela foi compartilhada como Editor com "
                 f"{segredos['gcp_service_account'].get('client_email')}")
    except gspread.exceptions.APIError as e:
        sys.exit(f"Erro da API do Google: {e}\nConfira se as APIs Google Sheets e Google Drive estão ativadas.")

    nome_aba = segredos["planilha"].get("aba", "Leads")
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome_aba, rows=1000, cols=len(COLUNAS))
    if aba.row_values(1) != COLUNAS:
        if aba.col_count < len(COLUNAS):
            aba.add_cols(len(COLUNAS) - aba.col_count)
        aba.update([COLUNAS], "A1")
        aba.freeze(rows=1)

    print(f"OK! Conectado à planilha '{planilha.title}', aba '{nome_aba}' pronta com {len(COLUNAS)} colunas.")


if __name__ == "__main__":
    main()
