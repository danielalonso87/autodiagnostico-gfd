"""
Autodiagnóstico financeiro gratuito — Gestão Financeira Descomplicada.

Rodar localmente:  streamlit run app.py
Modo demonstração: http://localhost:8501/?demo=1  (pula o formulário, não grava nada)
Origem do lead:    ...?origem=youtube  (fica gravada na planilha)
"""

from __future__ import annotations

import html
import re
import uuid
from datetime import datetime
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from diagnostico import graficos, planilha
from diagnostico.calculos import ROTULO_NIVEL, brl, calcular, pct, simular_queda
from diagnostico.estilo import CSS
from diagnostico.perguntas import (
    CHECKLIST_REUNIAO, FUNCIONARIOS, HABITOS, PRAZOS, PREOCUPACOES, RESPOSTAS, SEGMENTOS,
    TEMPO_EMPRESA, TIPOS, numeros_visiveis, texto_custo_variavel,
)

st.set_page_config(page_title="Autodiagnóstico Financeiro | Gestão Financeira Descomplicada",
                   page_icon="📊", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

ETAPAS = ["perfil", "numeros", "habitos", "contato"]
TITULOS = {"perfil": "Sua empresa", "numeros": "Números", "habitos": "Rotina", "contato": "Contato"}


# ---------------------------------------------------------------- configuração
def cfg(secao: str, chave: str, padrao: str = "") -> str:
    try:
        return st.secrets[secao][chave]
    except Exception:
        return padrao


# Seu WhatsApp com DDI e DDD, só números (ex.: "5521999999999").
# Pode preencher aqui mesmo; se existir [app] whatsapp no secrets.toml, ele tem prioridade.
WHATSAPP_PADRAO = "5521986721336"
WHATSAPP = re.sub(r"\D", "", cfg("app", "whatsapp") or WHATSAPP_PADRAO)


# ---------------------------------------------------------------- estado
ss = st.session_state
# Mantém as respostas quando o widget sai da tela (navegação entre etapas)
for k in list(ss.keys()):
    if k.startswith("r_"):
        ss[k] = ss[k]

ss.setdefault("etapa", "intro")
ss.setdefault("erros", [])
ss.setdefault("id_sessao", uuid.uuid4().hex[:10])
ss.setdefault("rolar", 0)
if "origem" not in ss:
    qp = st.query_params
    ss.origem = qp.get("origem") or qp.get("utm_source") or "direto"

for k in ["r_tipo", "r_segmento", "r_func", "r_tempo", "r_prazo", "r_preocupacao"]:
    ss.setdefault(k, None)
for f in numeros_visiveis("Produtos"):
    ss.setdefault(f"r_{f['id']}", None)
    ss.setdefault(f"r_{f['id']}_ns", False)
for h in HABITOS:
    ss.setdefault(f"r_{h['id']}", None)
for k in ["r_nome", "r_empresa", "r_whats", "r_email"]:
    ss.setdefault(k, "")
ss.setdefault("r_lgpd", False)


def ir_para(etapa: str):
    ss.etapa = etapa
    ss.erros = []
    ss.rolar += 1


def rolar_topo():
    """Leva a página para o topo quando a etapa muda."""
    components.html(
        f"""<script>/*{ss.rolar}*/
        const d = window.parent.document;
        for (const s of ['[data-testid="stMain"]','[data-testid="stAppViewContainer"]','section.main']) {{
          const el = d.querySelector(s); if (el) el.scrollTo({{top:0}});
        }}
        window.parent.scrollTo({{top:0}});</script>""",
        height=0,
    )


# ---------------------------------------------------------------- coleta
def numeros_respondidos() -> dict:
    out = {}
    for f in numeros_visiveis(ss.r_tipo):
        if f["kind"] == "choice":
            out[f["id"]] = None if ss[f"r_{f['id']}_ns"] or ss.r_prazo is None else PRAZOS.index(ss.r_prazo)
        else:
            v = ss[f"r_{f['id']}"]
            out[f["id"]] = None if ss[f"r_{f['id']}_ns"] or v is None else float(v)
    return out


def habitos_respondidos() -> dict:
    return {h["id"]: ss[f"r_{h['id']}"] for h in HABITOS}


def validar(etapa: str) -> list[str]:
    faltas = []
    if etapa == "perfil":
        for k, nome in [("r_tipo", "o que a empresa vende"), ("r_segmento", "segmento"),
                        ("r_func", "número de pessoas"), ("r_tempo", "tempo de empresa")]:
            if not ss[k]:
                faltas.append(nome)
    elif etapa == "numeros":
        for f in numeros_visiveis(ss.r_tipo):
            chave = "r_prazo" if f["kind"] == "choice" else f"r_{f['id']}"
            if ss[chave] is None and not ss[f"r_{f['id']}_ns"]:
                faltas.append(f.get("q") or texto_custo_variavel(ss.r_tipo)["q"])
    elif etapa == "habitos":
        faltas = [h["q"] for h in HABITOS if not ss[f"r_{h['id']}"]]
    elif etapa == "contato":
        if not ss.r_nome.strip():
            faltas.append("seu nome")
        if len(re.sub(r"\D", "", ss.r_whats)) < 10:
            faltas.append("WhatsApp com DDD")
        if ss.r_email.strip() and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", ss.r_email.strip()):
            faltas.append("um e-mail válido (ou deixe em branco)")
        if not ss.r_lgpd:
            faltas.append("a autorização de contato")
    return faltas


def avancar():
    atual = ss.etapa
    faltas = validar(atual)
    if faltas:
        ss.erros = faltas
        return
    i = ETAPAS.index(atual)
    ir_para(ETAPAS[i + 1] if i < len(ETAPAS) - 1 else "processar")


def voltar():
    i = ETAPAS.index(ss.etapa)
    ir_para(ETAPAS[i - 1] if i > 0 else "intro")


def reiniciar():
    for k in [k for k in ss.keys() if k.startswith("r_")] + ["resultado", "salvo", "demo"]:
        if k in ss:
            del ss[k]
    ss.id_sessao = uuid.uuid4().hex[:10]
    ir_para("intro")


def carregar_demo():
    ss.update({
        "r_tipo": "Os dois", "r_segmento": "Oficina e serviços automotivos", "r_func": "6 a 20",
        "r_tempo": "3 a 10 anos", "r_fat": 80000, "r_var": 45, "r_fix": 35000, "r_parc": 5000,
        "r_caixa": 20000, "r_prazo": PRAZOS[1], "r_est_ns": True,
        "r_h1": "Às vezes", "r_h2": "Sim", "r_h3": "Não", "r_h4": "Não", "r_h5": "Não",
        "r_h6": "Às vezes", "r_h7": "Às vezes", "r_h8": "Não", "r_h9": "Às vezes", "r_h10": "Não",
        "r_nome": "Exemplo", "r_empresa": "Auto Center (exemplo)", "r_whats": "(21) 99999-9999",
    })
    ss.resultado = calcular(ss.r_tipo, numeros_respondidos(), habitos_respondidos())
    ss.demo = True
    ir_para("resultado")


# ---------------------------------------------------------------- componentes
def cabecalho():
    st.markdown(
        '<div class="gf-marca"><span class="sel">GF</span><div><b>Gestão Financeira Descomplicada</b>'
        "<span>Autodiagnóstico financeiro gratuito</span></div></div>",
        unsafe_allow_html=True,
    )


def progresso():
    i = ETAPAS.index(ss.etapa)
    st.progress((i + 1) / len(ETAPAS), text=f"Passo {i + 1} de {len(ETAPAS)} · {TITULOS[ss.etapa]}")


def navegacao(rotulo_avancar="Continuar"):
    if ss.erros:
        itens = "".join(f"\n- {html.escape(e)}" for e in ss.erros)
        st.error(f"Falta responder:{itens}" + ("\n\nSe não souber algum número, marque **Não sei**."
                                               if ss.etapa == "numeros" else ""))
    c1, _, c2 = st.columns([1, 2, 1.3])
    c1.button("Voltar", on_click=voltar, use_container_width=True)
    c2.button(rotulo_avancar, on_click=avancar, type="primary", use_container_width=True)


def campo_dinheiro(f: dict):
    with st.container(border=True):
        st.markdown(f"**{f['q']}**")
        st.caption(f["help"])
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.number_input("Valor em R$", min_value=0, step=1000, value=None, format="%d",
                        placeholder="Valor em R$", key=f"r_{f['id']}", label_visibility="collapsed",
                        disabled=ss[f"r_{f['id']}_ns"])
        c2.checkbox("Não sei", key=f"r_{f['id']}_ns")


def campo_percentual():
    t = texto_custo_variavel(ss.r_tipo)
    with st.container(border=True):
        st.markdown(f"**{t['q']}**")
        st.caption(t["help"])
        st.markdown(f'<div class="gf-exemplo">{t["ex"]}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.number_input("Percentual", min_value=0, max_value=95, step=5, value=None, format="%d",
                        placeholder="% do preço de venda", key="r_var", label_visibility="collapsed",
                        disabled=ss.r_var_ns)
        c2.checkbox("Não sei", key="r_var_ns")


def campo_prazo(f: dict):
    with st.container(border=True):
        st.markdown(f"**{f['q']}**")
        st.caption(f["help"])
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.pills("Prazo", PRAZOS, key="r_prazo", label_visibility="collapsed")
        c2.checkbox("Não sei", key="r_prazo_ns")


def cartao_kpi(rotulo: str, valor: str | None, sub: str, nivel: str | None, falta: str) -> str:
    if valor is None:
        return (f'<div class="gf-kpi"><div class="lab">{rotulo}<span class="gf-pill gf-none">Sem dado</span></div>'
                f'<div class="val">—</div><div class="sub">Faltou: {falta}.</div></div>')
    pill = f'<span class="gf-pill gf-{nivel}">{ROTULO_NIVEL[nivel]}</span>' if nivel else ""
    return (f'<div class="gf-kpi {nivel or ""}"><div class="lab">{rotulo}{pill}</div>'
            f'<div class="val">{valor}</div><div class="sub">{sub}</div></div>')


def faltou(ids: list[str]) -> str:
    nomes = {"fat": "faturamento", "var": "custos da venda", "fix": "despesas fixas",
             "parc": "parcelas", "caixa": "saldo em caixa"}
    nums = numeros_respondidos()
    return ", ".join(nomes[i] for i in ids if nums.get(i) is None) or "dados"


# ---------------------------------------------------------------- telas
def tela_intro():
    c1, c2 = st.columns([1.25, 1], gap="large")
    with c1:
        st.markdown('<span class="gf-eyebrow">Gratuito · cerca de 5 minutos</span>', unsafe_allow_html=True)
        st.title("Quantos dias sua empresa aguenta sem vender?")
        st.markdown(
            "Responda algumas perguntas com valores aproximados. No final você vê a **nota de saúde "
            "financeira** da empresa, os números que mais importam para o seu negócio e os **3 pontos "
            "que pedem atenção agora**."
        )
        st.info("Não precisa de planilha nem extrato. Se não souber algum número, marque **Não sei**. "
                "Isso também faz parte do diagnóstico.")
        st.button("Começar diagnóstico", type="primary", on_click=ir_para, args=("perfil",))
    with c2, st.container(border=True):
        st.markdown('<span class="gf-eyebrow">O que você recebe</span>', unsafe_allow_html=True)
        st.markdown("**1. Nota de 0 a 100**  \nSaúde financeira em 5 áreas: controle, caixa, margem, "
                    "dívidas e planejamento.")
        st.markdown("**2. Seus números-chave**  \nPonto de equilíbrio, fôlego de caixa, margem de "
                    "segurança e quanto sobra por mês.")
        st.markdown("**3. Os 3 riscos prioritários**  \nO que resolver primeiro, explicado sem financês.")


def tela_perfil():
    progresso()
    st.header("Conte um pouco sobre a empresa")
    with st.container(border=True):
        st.radio("**O que a empresa vende?**", TIPOS, index=None, horizontal=True, key="r_tipo",
                 captions=["Revende ou fabrica", "Clínica, oficina, agência…", "Ex.: oficina que vende peças"])
    with st.container(border=True):
        st.selectbox("**Qual o segmento?**", SEGMENTOS, index=None, placeholder="Escolha uma opção",
                     key="r_segmento")
    with st.container(border=True):
        st.pills("**Quantas pessoas trabalham na empresa?**", FUNCIONARIOS, key="r_func")
    with st.container(border=True):
        st.pills("**Há quanto tempo a empresa existe?**", TEMPO_EMPRESA, key="r_tempo")
    navegacao()


def tela_numeros():
    progresso()
    st.header("Os números do mês, de cabeça")
    st.markdown('<p class="gf-muted">Valores aproximados de um mês normal. Arredondar está ótimo.</p>',
                unsafe_allow_html=True)
    for f in numeros_visiveis(ss.r_tipo):
        if f["kind"] == "money":
            campo_dinheiro(f)
        elif f["kind"] == "pct":
            campo_percentual()
        else:
            campo_prazo(f)
    navegacao()


def tela_habitos():
    progresso()
    st.header("Como é a rotina financeira hoje")
    st.markdown('<p class="gf-muted">Responda pensando nos últimos 6 meses. Não existe resposta certa.</p>',
                unsafe_allow_html=True)
    for h in HABITOS:
        with st.container(border=True):
            c1, c2 = st.columns([1.6, 1], vertical_alignment="center")
            c1.markdown(f"**{h['q']}**")
            c2.segmented_control(h["q"], RESPOSTAS, key=f"r_{h['id']}", label_visibility="collapsed")
    navegacao()


def tela_contato():
    progresso()
    st.header("Para onde enviamos seu diagnóstico?")
    st.markdown('<p class="gf-muted">Seu resultado aparece logo depois. Também enviamos uma cópia pelo WhatsApp.</p>',
                unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.text_input("Seu nome *", key="r_nome", autocomplete="name")
        c2.text_input("Nome da empresa", key="r_empresa", autocomplete="organization")
        c1.text_input("WhatsApp com DDD *", key="r_whats", placeholder="(21) 99999-9999", autocomplete="tel")
        c2.text_input("E-mail", key="r_email", autocomplete="email")
        st.selectbox("O que mais te preocupa hoje na empresa?", PREOCUPACOES, index=None,
                     placeholder="Escolha (opcional)", key="r_preocupacao")
        st.checkbox("Autorizo o contato da Gestão Financeira Descomplicada pelo WhatsApp e e-mail informados "
                    "e o uso destas respostas apenas para preparar meu diagnóstico, conforme a LGPD.",
                    key="r_lgpd")
    navegacao("Ver meu diagnóstico")


def processar():
    nums, habs = numeros_respondidos(), habitos_respondidos()
    r = calcular(ss.r_tipo, nums, habs)
    ss.resultado = r
    with st.spinner("Calculando seu diagnóstico…"):
        linha = planilha.montar_linha(
            ss.id_sessao, ss.origem,
            {"nome": ss.r_nome.strip(), "empresa": ss.r_empresa.strip(), "whatsapp": ss.r_whats.strip(),
             "email": ss.r_email.strip(), "preocupacao": ss.r_preocupacao},
            {"tipo": ss.r_tipo, "segmento": ss.r_segmento, "funcionarios": ss.r_func, "tempo": ss.r_tempo},
            nums, habs, r,
        )
        ss.salvo = planilha.salvar(linha)
    ir_para("resultado")
    st.rerun()


def tela_resultado():
    r = ss.resultado
    nome = ss.r_empresa.strip() or ss.r_nome.strip() or "sua empresa"
    classe, nivel, frase = r["classe"]

    if ss.get("demo"):
        st.warning("Modo demonstração: dados de exemplo, nada foi gravado.")
    elif ss.get("salvo") == (True, "csv"):
        st.info("**Modo local:** a planilha do Google ainda não está conectada, então este diagnóstico foi "
                "salvo em `dados/leads_local.csv`. Veja a seção 2 do README para conectar.")
    elif ss.get("salvo") and not ss.salvo[0]:
        st.toast("Não conseguimos registrar suas respostas agora, mas seu diagnóstico está abaixo.")

    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    c1.markdown(f'<span class="gf-eyebrow">Diagnóstico · {datetime.now().strftime("%d/%m/%Y")}</span>',
                unsafe_allow_html=True)
    c1.header(f"Saúde financeira de {nome}")
    c2.button("Refazer", on_click=reiniciar, use_container_width=True)

    a, b = st.columns(2)
    with a, st.container(border=True):
        st.plotly_chart(graficos.anel_nota(r["nota"], nivel), use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown(f'<span class="gf-pill gf-{nivel}">{classe}</span>', unsafe_allow_html=True)
        st.markdown(f"**{frase}**")
        st.caption(f'Você marcou "não sei" em {r["qtd_nao_sei"]} de {r["total_campos"]} números.'
                   if r["qtd_nao_sei"] else "Você respondeu todos os números.")
    with b, st.container(border=True):
        st.markdown("**Nota por área**")
        st.plotly_chart(graficos.radar_pilares(r["pilares"]), use_container_width=True,
                        config={"displayModeBar": False})

    st.subheader("Seus números-chave")
    core, falta_core = r["core"], faltou(["fat", "var", "fix"])
    cartoes = [
        cartao_kpi("Sobra mensal estimada", brl(r["sobra"]) if core else None,
                   f"{pct(r['sobra'] / r['F'], 1)} do faturamento, depois de custos, despesas fixas e parcelas."
                   if core else "", r["nivel_sobra"], falta_core),
        cartao_kpi("Ponto de equilíbrio", brl(r["pe"]) if core else None,
                   "Faturamento mínimo por mês para não ter prejuízo.", r["nivel_ms"], falta_core),
        cartao_kpi("Margem de segurança", pct(r["ms"]) if core else None,
                   ("Faturamento abaixo do ponto de equilíbrio." if core and r["ms"] < 0
                    else "Quanto as vendas podem cair antes do prejuízo."), r["nivel_ms"], falta_core),
        cartao_kpi("Fôlego de caixa", f"{max(0, round(r['fol']))} dias" if r["fol"] is not None else None,
                   "Por quanto tempo o caixa paga as contas fixas e parcelas sem nenhuma venda.",
                   r["nivel_fol"], faltou(["caixa", "fix"])),
        cartao_kpi("Margem de contribuição", pct(1 - r["v"]) if core else None,
                   f"De cada R$ 100 vendidos, sobram R$ {round((1 - r['v']) * 100)} para pagar as despesas fixas."
                   if core else "", r["nivel_mc"], falta_core),
        cartao_kpi("Peso das dívidas", pct(r["div"]) if r["div"] is not None else None,
                   f"{brl(r['P'])} em parcelas por mês sobre o faturamento." if r["div"] is not None else "",
                   r["nivel_div"], faltou(["parc", "fat"])),
    ]
    st.markdown(f'<div class="gf-kpis">{"".join(cartoes)}</div>', unsafe_allow_html=True)
    st.write("")

    if core:
        with st.container(border=True):
            st.markdown("**Onde você está em relação ao ponto de equilíbrio**")
            st.plotly_chart(graficos.regua_equilibrio(r["F"], r["pe"]), use_container_width=True,
                            config={"displayModeBar": False, "staticPlot": True})
            folga = r["F"] - r["pe"]
            st.markdown(
                f'<div class="gf-legenda"><span>Seu faturamento: <b>{brl(r["F"])}</b></span>'
                f'<span>{"Folga de " + brl(folga) if folga >= 0 else "Faltam " + brl(-folga)} por mês</span></div>',
                unsafe_allow_html=True,
            )
            st.divider()
            queda = st.slider("E se as vendas caírem…", 0, 50, 10, 5, format="%d%%")
            s = simular_queda(r, queda / 100)
            cor_sobra = "var(--gf-bad)" if s["sobra"] < 0 else "var(--gf-good)"
            st.markdown(
                f'<div class="gf-sim">'
                f'<div><span>Faturamento</span><b>{brl(s["faturamento"])}</b></div>'
                f'<div><span>Sobra no mês</span><b style="color:{cor_sobra}">{brl(s["sobra"])}</b></div>'
                f'<div><span>Caixa</span><b style="color:{cor_sobra}">{s["caixa"]}</b></div></div>',
                unsafe_allow_html=True,
            )
            st.caption("Simulação mantendo despesas fixas e parcelas iguais e os custos da venda "
                       "proporcionais ao faturamento.")

    st.subheader("O que resolver primeiro")
    if r["alertas"]:
        for i, al in enumerate(r["alertas"], 1):
            st.markdown(
                f'<div class="gf-alerta"><span class="n gf-{al["nivel"]}">{i}</span>'
                f'<div><b>{html.escape(al["titulo"])}</b><p>{html.escape(al["texto"])}</p></div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("**Nenhum risco grave encontrado.** A base está organizada. Na reunião dá para olhar "
                   "crescimento e investimentos.")

    st.markdown(
        '<div class="gf-cta"><h3>Quer validar esses números com os dados reais?</h3>'
        "<p>Na reunião gratuita de 45 minutos, conferimos este diagnóstico com o extrato e os números da sua "
        "empresa e você sai com um plano de ação para os próximos 90 dias.</p></div>",
        unsafe_allow_html=True,
    )
    if WHATSAPP:
        msg = (f"Olá, Daniel! Fiz o autodiagnóstico da {nome} (nota {r['nota']}) "
               "e quero agendar a reunião gratuita.")
        _, b, _ = st.columns([1, 2, 1])
        b.link_button("Agendar pelo WhatsApp", f"https://wa.me/{WHATSAPP}?text={quote(msg)}",
                      type="primary", use_container_width=True)
    else:
        st.caption("Preencha WHATSAPP_PADRAO no início do app.py para mostrar o botão do WhatsApp.")

    with st.expander("O que separar para a reunião"):
        st.markdown("\n".join(f"- {item}" for item in CHECKLIST_REUNIAO))


# ---------------------------------------------------------------- roteamento
cabecalho()
if st.query_params.get("demo") == "1" and ss.etapa == "intro" and "resultado" not in ss:
    carregar_demo()

if ss.etapa == "processar":
    processar()

{
    "intro": tela_intro,
    "perfil": tela_perfil,
    "numeros": tela_numeros,
    "habitos": tela_habitos,
    "contato": tela_contato,
    "resultado": tela_resultado,
}[ss.etapa]()

rolar_topo()
