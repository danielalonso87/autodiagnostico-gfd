"""Textos e opções do formulário. Edite aqui para mudar perguntas sem mexer na lógica."""

TIPOS = ["Produtos", "Serviços", "Os dois"]

SEGMENTOS = [
    "Comércio / loja",
    "Alimentação (restaurante, lanchonete, padaria)",
    "Saúde (clínica, consultório)",
    "Beleza e estética",
    "Oficina e serviços automotivos",
    "Construção e reformas",
    "Indústria / fabricação",
    "Educação",
    "Serviços profissionais (escritório, agência)",
    "Outro",
]

FUNCIONARIOS = ["Só eu", "2 a 5", "6 a 20", "21 a 50", "Mais de 50"]
TEMPO_EMPRESA = ["Menos de 1 ano", "1 a 3 anos", "3 a 10 anos", "Mais de 10 anos"]

PRAZOS = ["À vista / Pix", "Até 30 dias", "30 a 60 dias", "Mais de 60 dias"]

# Campos numéricos. "kind": money (R$), pct (%), choice (lista PRAZOS)
NUMEROS = [
    {
        "id": "fat",
        "kind": "money",
        "q": "Quanto a empresa fatura por mês, em média?",
        "help": "Tudo o que entra de vendas num mês normal, antes de pagar qualquer conta.",
    },
    {"id": "var", "kind": "pct"},  # texto depende do tipo de empresa (ver texto_custo_variavel)
    {
        "id": "fix",
        "kind": "money",
        "q": "Quanto custam as despesas fixas por mês?",
        "help": "Aluguel, salários e encargos, seu pró-labore, contador, sistemas, internet, luz. "
        "Tudo o que você paga vendendo ou não.",
    },
    {
        "id": "parc",
        "kind": "money",
        "q": "Quanto você paga de parcelas de empréstimos e financiamentos por mês?",
        "help": "Some as parcelas de empréstimos, financiamentos e parcelamentos de impostos da empresa. "
        "Sem dívidas? Coloque 0.",
    },
    {
        "id": "caixa",
        "kind": "money",
        "q": "Quanto a empresa tem em caixa hoje?",
        "help": "Saldo em conta mais aplicações que dá para resgatar rápido. Não conte o dinheiro pessoal.",
    },
    {
        "id": "prazo",
        "kind": "choice",
        "q": "Em quanto tempo, em média, você recebe as vendas?",
        "help": "Considere a forma de pagamento mais comum dos seus clientes.",
    },
    {
        "id": "est",
        "kind": "money",
        "q": "Quanto você tem em estoque hoje, a preço de custo?",
        "help": "Valor que você pagou pelas mercadorias ou matéria-prima paradas.",
        "so_produto": True,
    },
]


def texto_custo_variavel(tipo: str | None) -> dict:
    if tipo == "Serviços":
        return {
            "q": "De cada venda, quanto vai embora em custos que acompanham a venda? (%)",
            "help": "Em % do preço: imposto da nota, comissões, taxa de cartão, material usado "
            "e terceiros contratados para aquele serviço.",
            "ex": "Exemplo: um serviço de R$ 1.000 que gera R$ 150 de impostos e taxas e "
            "R$ 200 de material e terceiros → 35%.",
        }
    return {
        "q": "De cada venda, quanto vai embora em mercadoria e custos da venda? (%)",
        "help": "Em % do preço: custo da mercadoria ou matéria-prima, imposto da nota, "
        "comissões e taxa de cartão.",
        "ex": "Exemplo: vende por R$ 100, a mercadoria custou R$ 40 e impostos e taxas dão "
        "R$ 12 → 52%.",
    }


def numeros_visiveis(tipo: str | None) -> list[dict]:
    return [f for f in NUMEROS if not f.get("so_produto") or tipo != "Serviços"]


# Hábitos. inv=True: "Sim" é ruim.
HABITOS = [
    {"id": "h1", "col": "conta_separada", "q": "A conta da empresa é separada da sua conta pessoal?"},
    {"id": "h2", "col": "registra_entradas_saidas", "q": "Você registra todas as entradas e saídas de dinheiro?"},
    {"id": "h3", "col": "sabe_lucro_mes", "q": "Você sabe quanto a empresa lucrou no mês passado?"},
    {"id": "h4", "col": "prolabore_fixo", "q": "Você tira um pró-labore fixo, em vez de retirar dinheiro quando precisa?"},
    {"id": "h5", "col": "previsao_caixa", "q": "Você acompanha quanto vai entrar e sair de dinheiro nas próximas semanas?"},
    {"id": "h6", "col": "faltou_dinheiro_contas", "q": "Nos últimos 6 meses, faltou dinheiro para pagar alguma conta em dia?", "inv": True},
    {"id": "h7", "col": "preco_por_custo", "q": "Você calcula o preço de venda a partir dos seus custos?"},
    {"id": "h8", "col": "sabe_margem_produto", "q": "Você sabe quais produtos ou serviços dão mais lucro?"},
    {
        "id": "h9",
        "col": "usa_credito_caro",
        "q": "Você usa cheque especial, cartão ou antecipação de recebíveis para fechar o mês?",
        "inv": True,
    },
    {"id": "h10", "col": "tem_meta_orcamento", "q": "A empresa tem meta de faturamento e orçamento para o ano?"},
]
RESPOSTAS = ["Sim", "Às vezes", "Não"]

PREOCUPACOES = [
    "O dinheiro não sobra no fim do mês",
    "Não sei se tenho lucro",
    "Não sei se meu preço está certo",
    "Dívidas e empréstimos",
    "Quero crescer, mas não sei se posso investir",
    "Organizar as finanças",
]

CHECKLIST_REUNIAO = [
    "Extrato da conta da empresa dos últimos 3 meses",
    "Lista das despesas fixas (aluguel, folha, sistemas)",
    "Empréstimos e financiamentos em aberto, com parcelas e prazos",
    "Se tiver: relatório de vendas do sistema ou da maquininha",
]
