"""Cálculos do diagnóstico. Python puro, sem Streamlit, para poder testar."""

from __future__ import annotations

from .perguntas import HABITOS, numeros_visiveis

NOTA_NIVEL = {"good": 1.0, "warn": 0.5, "bad": 0.0}
ROTULO_NIVEL = {"good": "Saudável", "warn": "Atenção", "bad": "Crítico"}


def brl(valor: float) -> str:
    sinal = "− " if valor < 0 else ""
    inteiro = f"{round(abs(valor)):,}".replace(",", ".")
    return f"{sinal}R$ {inteiro}"


def pct(x: float, casas: int = 0) -> str:
    return f"{x * 100:.{casas}f}".replace(".", ",") + "%"


def _nv(nivel: str | None) -> float:
    """Nota de um indicador; sem dado vale 0,25 (não saber já é um problema)."""
    return 0.25 if nivel is None else NOTA_NIVEL[nivel]


def _hv(habitos: dict, hid: str) -> float:
    inv = next(h.get("inv", False) for h in HABITOS if h["id"] == hid)
    resp = habitos.get(hid)
    v = 1.0 if resp == "Sim" else 0.5 if resp == "Às vezes" else 0.0
    return 1 - v if inv else v


def _media(habitos: dict, ids: list[str]) -> float:
    return sum(_hv(habitos, i) for i in ids) / len(ids)


def calcular(tipo: str | None, numeros: dict, habitos: dict) -> dict:
    """
    numeros: {"fat": 80000, "var": 45, "fix": 35000, "parc": 5000, "caixa": 20000,
              "prazo": 1 (índice de PRAZOS), "est": None}
             valor None = "não sei".
    habitos: {"h1": "Sim" | "Às vezes" | "Não", ...}
    """
    campos = numeros_visiveis(tipo)
    nao_sei = [f["id"] for f in campos if numeros.get(f["id"]) is None]

    F = numeros.get("fat")
    v = numeros.get("var")
    v = None if v is None else v / 100
    C = numeros.get("fix")
    P = numeros.get("parc")
    K = numeros.get("caixa")
    prazo = numeros.get("prazo")
    est = numeros.get("est") if tipo != "Serviços" else None
    Pz = P or 0

    r: dict = {
        "F": F, "v": v, "C": C, "P": P, "K": K, "prazo": prazo, "est": est,
        "nao_sei": nao_sei, "qtd_nao_sei": len(nao_sei), "total_campos": len(campos),
        "core": bool(F and F > 0 and v is not None and v < 1 and C is not None),
        "mc": None, "sobra": None, "pe": None, "ms": None, "fol": None, "div": None,
        "nivel_sobra": None, "nivel_ms": None, "nivel_mc": None, "nivel_fol": None, "nivel_div": None,
    }

    if r["core"]:
        r["mc"] = F * (1 - v)
        r["sobra"] = r["mc"] - C - Pz
        r["pe"] = (C + Pz) / (1 - v)
        r["ms"] = (F - r["pe"]) / F
        s = r["sobra"] / F
        r["nivel_sobra"] = "bad" if s < 0 else "warn" if s < 0.08 else "good"
        r["nivel_ms"] = "bad" if r["ms"] < 0 else "warn" if r["ms"] < 0.15 else "good"
        r["nivel_mc"] = "warn" if (1 - v) < 0.25 else "good"

    if K is not None and C is not None and (C + Pz) > 0:
        r["fol"] = K / ((C + Pz) / 30)
        r["nivel_fol"] = "bad" if r["fol"] < 30 else "warn" if r["fol"] < 90 else "good"

    if P is not None and F:
        r["div"] = P / F
        r["nivel_div"] = "bad" if r["div"] > 0.2 else "warn" if r["div"] > 0.1 else "good"

    H = habitos
    pilares = {
        "Controle": _media(H, ["h1", "h2", "h3"]) * 70 + (1 - len(nao_sei) / len(campos)) * 30,
        "Caixa": _media(H, ["h4", "h5", "h6"]) * 60 + _nv(r["nivel_fol"]) * 40,
        "Margem e preço": _media(H, ["h7", "h8"]) * 60 + _nv(r["nivel_ms"]) * 40,
        "Dívidas": _hv(H, "h9") * 50 + _nv(r["nivel_div"]) * 50,
        "Planejamento": _media(H, ["h5", "h10"]) * 100,
    }
    r["pilares"] = {k: round(val) for k, val in pilares.items()}
    r["nota"] = round(sum(r["pilares"].values()) / len(r["pilares"]))

    n = r["nota"]
    if n < 40:
        r["classe"] = ("Crítica", "bad", "Há riscos que podem comprometer a empresa nos próximos meses.")
    elif n < 60:
        r["classe"] = ("Atenção", "warn", "A empresa funciona, mas está vulnerável a qualquer imprevisto.")
    elif n < 80:
        r["classe"] = ("Estável", "good", "A base é boa. Há ajustes a fazer para crescer com segurança.")
    else:
        r["classe"] = ("Saudável", "good", "Boa saúde financeira. O próximo passo é planejar o crescimento.")

    r["todos_alertas"] = _alertas(r, H)
    r["alertas"] = r["todos_alertas"][:3]
    return r


def _alertas(r: dict, H: dict) -> list[dict]:
    A: list[dict] = []
    F = r["F"]

    def add(peso, nivel, titulo, texto):
        A.append({"peso": peso, "nivel": nivel, "titulo": titulo, "texto": texto})

    if r["core"] and r["ms"] < 0:
        add(100, "bad", "A empresa está vendendo menos do que custa",
            f"Para pagar as despesas fixas e as parcelas, você precisaria faturar {brl(r['pe'])} por mês. "
            f"Hoje fatura {brl(F)}, o que deixa um buraco de cerca de {brl(-r['sobra'])} todo mês.")
    if r["fol"] is not None and r["fol"] < 30:
        add(95, "bad", f"O caixa paga só {max(0, round(r['fol']))} dias de contas fixas",
            "Se as vendas pararem ou atrasarem, o dinheiro em conta acaba em menos de um mês. "
            "Uma reserva confortável costuma cobrir de 3 a 6 meses de despesas fixas.")
    if r["qtd_nao_sei"] >= 2:
        add(90, "warn", f"Você não soube {r['qtd_nao_sei']} dos {r['total_campos']} números básicos",
            "Sem esses números, decisões de preço, contratação e investimento são tomadas no escuro. "
            "Organizar essa informação é o primeiro passo de qualquer melhoria.")
    if r["core"] and 0 <= r["ms"] < 0.15:
        add(85, "warn", "Uma queda pequena nas vendas já leva ao prejuízo",
            f"Se o faturamento cair {pct(r['ms'])}, a empresa passa a operar no vermelho. "
            "Um mês fraco ou um cliente grande a menos já basta.")
    if H.get("h6") in ("Sim", "Às vezes"):
        add(80, "bad", "Já faltou dinheiro para pagar contas em dia",
            "Atrasar contas gera juros e multas e tira seu poder de negociação com fornecedores. "
            "Normalmente é sinal de que não existe previsão de caixa.")
    if r["div"] is not None and r["div"] > 0.15:
        add(78, r["nivel_div"], f"As parcelas consomem {pct(r['div'])} do faturamento",
            f"São {brl(r['P'])} por mês saindo antes de você pagar qualquer outra conta. "
            "Vale olhar taxas, prazos e a possibilidade de renegociar.")
    if r["prazo"] is not None and r["prazo"] >= 2 and (r["fol"] is None or r["fol"] < 90):
        add(75, "warn", "Você vende a prazo e tem pouco caixa para esperar",
            "As contas vencem antes de o dinheiro das vendas entrar. Esse descompasso é uma das causas "
            "mais comuns de aperto em empresas que vendem bem.")
    if H.get("h1") and H.get("h1") != "Sim":
        add(72, "warn", "Dinheiro pessoal e da empresa misturados",
            "Quando as contas se misturam, fica impossível saber se a empresa dá lucro ou se é o seu "
            "dinheiro pessoal que está bancando ela.")
    if H.get("h9") == "Sim":
        add(70, "warn", "O mês fecha com crédito caro",
            "Cheque especial, rotativo do cartão e antecipação têm juros altos. Usados todo mês, "
            "viram uma bola de neve.")
    if _media(H, ["h7", "h8"]) < 0.5:
        add(68, "warn", "Preço definido sem olhar os custos",
            "Sem saber a margem de cada produto ou serviço, você pode estar vendendo muito justamente "
            "o que dá menos lucro, ou até prejuízo.")
    if r["core"] and r["est"] is not None and r["v"] > 0:
        meses = r["est"] / (F * r["v"])
        if meses > 2:
            add(65, "warn", f"O estoque equivale a {meses:.1f} meses de vendas".replace(".", ","),
                "É dinheiro parado na prateleira que poderia estar no caixa. Vale entender o que gira "
                "e o que está encalhado.")
    if H.get("h4") and H.get("h4") != "Sim":
        add(60, "warn", "Retiradas sem regra",
            "Tirar dinheiro conforme a necessidade bagunça o caixa e esconde o lucro real. "
            "Um pró-labore fixo resolve as duas coisas.")
    if H.get("h5") and H.get("h5") != "Sim":
        add(55, "warn", "Sem previsão de caixa",
            "Sem enxergar as próximas semanas, os apertos só aparecem quando já é tarde para reagir.")
    if H.get("h10") and H.get("h10") != "Sim":
        add(50, "warn", "Sem meta nem orçamento",
            "Sem meta, não há como saber se o mês foi bom ou ruim, nem quanto dá para investir "
            "com segurança.")

    A.sort(key=lambda a: a["peso"], reverse=True)
    return A


def simular_queda(r: dict, queda: float) -> dict:
    """queda entre 0 e 1. Mantém fixos e parcelas; custo variável proporcional."""
    F2 = r["F"] * (1 - queda)
    sobra2 = F2 * (1 - r["v"]) - r["C"] - (r["P"] or 0)
    if sobra2 >= 0:
        caixa = "Não diminui"
    elif r["K"] is None:
        caixa = "Sem dado de caixa"
    else:
        dias = round(r["K"] / (-sobra2) * 30)
        caixa = "Zera em mais de 2 anos" if dias > 720 else f"Zera em {dias} dias"
    return {"faturamento": F2, "sobra": sobra2, "caixa": caixa}
