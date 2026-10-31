"""Gravação dos leads no Google Sheets (com cópia em CSV local se o Sheets não estiver configurado)."""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from .perguntas import HABITOS, PRAZOS

log = logging.getLogger(__name__)
FUSO = ZoneInfo("America/Sao_Paulo")
CSV_LOCAL = Path(__file__).resolve().parent.parent / "dados" / "leads_local.csv"

COLUNAS = [
    "data_hora", "id_sessao", "origem", "status",
    "nome", "empresa", "whatsapp", "email", "preocupacao", "consentimento_lgpd",
    "tipo", "segmento", "funcionarios", "tempo_empresa",
    "faturamento", "custo_variavel_pct", "despesas_fixas", "parcelas", "caixa",
    "prazo_recebimento", "estoque", "qtd_nao_sei",
    *[h["col"] for h in HABITOS],
    "nota", "classificacao",
    "nota_controle", "nota_caixa", "nota_margem", "nota_dividas", "nota_planejamento",
    "sobra_mensal", "ponto_equilibrio", "margem_seguranca_pct", "folego_caixa_dias",
    "margem_contribuicao_pct", "peso_dividas_pct", "meses_estoque",
    "alerta_1", "alerta_2", "alerta_3", "todos_alertas",
]


def _texto(valor: str | None) -> str:
    """Texto digitado pelo cliente: impede que vire fórmula ou número no Sheets."""
    valor = (valor or "").strip()
    return "'" + valor if valor[:1] in ("=", "+", "-", "@") else valor


def montar_linha(id_sessao: str, origem: str, contato: dict, perfil: dict,
                 numeros: dict, habitos: dict, r: dict) -> list:
    def num(chave):
        v = numeros.get(chave)
        return "não sei" if v is None else v

    def arred(v, casas=0):
        return "" if v is None else round(v, casas)

    prazo = numeros.get("prazo")
    alertas = [a["titulo"] for a in r["alertas"]] + ["", "", ""]
    p = r["pilares"]

    valores = {
        "data_hora": datetime.now(FUSO).strftime("%d/%m/%Y %H:%M:%S"),
        "id_sessao": id_sessao,
        "origem": origem,
        "status": "Novo",
        "nome": _texto(contato["nome"]),
        "empresa": _texto(contato.get("empresa")),
        "whatsapp": "'" + contato["whatsapp"].strip(),
        "email": _texto(contato.get("email")),
        "preocupacao": contato.get("preocupacao") or "",
        "consentimento_lgpd": "Sim",
        "tipo": perfil["tipo"],
        "segmento": perfil["segmento"],
        "funcionarios": perfil["funcionarios"],
        "tempo_empresa": perfil["tempo"],
        "faturamento": num("fat"),
        "custo_variavel_pct": num("var"),
        "despesas_fixas": num("fix"),
        "parcelas": num("parc"),
        "caixa": num("caixa"),
        "prazo_recebimento": "não sei" if prazo is None else PRAZOS[prazo],
        "estoque": "" if perfil["tipo"] == "Serviços" else num("est"),
        "qtd_nao_sei": r["qtd_nao_sei"],
        "nota": r["nota"],
        "classificacao": r["classe"][0],
        "nota_controle": p["Controle"],
        "nota_caixa": p["Caixa"],
        "nota_margem": p["Margem e preço"],
        "nota_dividas": p["Dívidas"],
        "nota_planejamento": p["Planejamento"],
        "sobra_mensal": arred(r["sobra"]),
        "ponto_equilibrio": arred(r["pe"]),
        "margem_seguranca_pct": "" if r["ms"] is None else round(r["ms"] * 100, 1),
        "folego_caixa_dias": arred(r["fol"]),
        "margem_contribuicao_pct": "" if r["v"] is None else round((1 - r["v"]) * 100, 1),
        "peso_dividas_pct": "" if r["div"] is None else round(r["div"] * 100, 1),
        "meses_estoque": ("" if not (r["core"] and r["est"] is not None and r["v"])
                          else round(r["est"] / (r["F"] * r["v"]), 1)),
        "alerta_1": alertas[0],
        "alerta_2": alertas[1],
        "alerta_3": alertas[2],
        "todos_alertas": " | ".join(a["titulo"] for a in r.get("todos_alertas", r["alertas"])),
    }
    for h in HABITOS:
        valores[h["col"]] = habitos.get(h["id"], "")
    return [valores[c] for c in COLUNAS]


def _sheets_configurado() -> bool:
    try:
        return "gcp_service_account" in st.secrets and "planilha" in st.secrets
    except Exception:  # sem secrets.toml
        return False


@st.cache_resource(show_spinner=False)
def _aba():
    import gspread

    cliente = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    planilha = cliente.open_by_key(st.secrets["planilha"]["id"])
    nome_aba = st.secrets["planilha"].get("aba", "Leads")
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome_aba, rows=1000, cols=len(COLUNAS))
    if aba.row_values(1) != COLUNAS:  # aba nova ou colunas mudaram em nova versão do app
        if aba.col_count < len(COLUNAS):
            aba.add_cols(len(COLUNAS) - aba.col_count)
        aba.update([COLUNAS], "A1")
        aba.freeze(rows=1)
    return aba


def salvar(linha: list) -> tuple[bool, str]:
    """Retorna (ok, destino). Nunca levanta exceção: o cliente sempre vê o resultado."""
    if _sheets_configurado():
        try:
            _aba().append_row(linha, value_input_option="USER_ENTERED")
            return True, "sheets"
        except Exception as e:  # rede, permissão, cota
            log.exception("Falha ao gravar no Google Sheets: %s", e)
            _aba.clear()  # força reconectar na próxima tentativa
    try:
        CSV_LOCAL.parent.mkdir(exist_ok=True)
        if CSV_LOCAL.exists():
            with CSV_LOCAL.open(encoding="utf-8-sig") as f:
                cabecalho = f.readline().strip().split(";")
            if cabecalho != COLUNAS:  # versão antiga: guarda e começa um arquivo novo
                CSV_LOCAL.rename(CSV_LOCAL.with_name(f"leads_local_antigo_{datetime.now():%Y%m%d%H%M%S}.csv"))
        novo = not CSV_LOCAL.exists()
        with CSV_LOCAL.open("a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            if novo:
                w.writerow(COLUNAS)
            w.writerow([v.lstrip("'") if isinstance(v, str) else v for v in linha])
        return (not _sheets_configurado()), "csv"
    except Exception as e:
        log.exception("Falha ao gravar CSV local: %s", e)
        return False, "nenhum"
