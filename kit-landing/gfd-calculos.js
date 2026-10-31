/*!
 * Autodiagnóstico Financeiro — Gestão Financeira Descomplicada
 * Cálculos e textos do diagnóstico (versão JavaScript).
 *
 * ATENÇÃO: este arquivo é uma tradução fiel de diagnostico/calculos.py e
 * diagnostico/perguntas.py. Não altere fórmulas, faixas ou textos aqui sem
 * alterar também no Python (e vice-versa). Para conferir que os dois dão o
 * mesmo resultado, rode:  python ferramentas/teste_paridade_js.py
 *
 * Sem dependências. Funciona no navegador (window.GFDCalc) e no Node (require).
 */
(function (raiz, fabrica) {
  if (typeof module === "object" && module.exports) module.exports = fabrica();
  else raiz.GFDCalc = fabrica();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  /* ------------------------------------------------------------ textos */
  var TIPOS = ["Produtos", "Serviços", "Os dois"];
  var TIPOS_LEGENDA = ["Revende ou fabrica", "Clínica, oficina, agência…", "Ex.: oficina que vende peças"];
  var SEGMENTOS = [
    "Comércio / loja",
    "Alimentação (restaurante, lanchonete, padaria)",
    "Saúde (clínica, consultório)",
    "Beleza e estética",
    "Oficina e serviços automotivos",
    "Construção e reformas",
    "Indústria / fabricação",
    "Educação",
    "Serviços profissionais (escritório, agência)",
    "Outro"
  ];
  var FUNCIONARIOS = ["Só eu", "2 a 5", "6 a 20", "21 a 50", "Mais de 50"];
  var TEMPO_EMPRESA = ["Menos de 1 ano", "1 a 3 anos", "3 a 10 anos", "Mais de 10 anos"];
  var PRAZOS = ["À vista / Pix", "Até 30 dias", "30 a 60 dias", "Mais de 60 dias"];

  var NUMEROS = [
    { id: "fat", kind: "money", q: "Quanto a empresa fatura por mês, em média?",
      help: "Tudo o que entra de vendas num mês normal, antes de pagar qualquer conta." },
    { id: "var", kind: "pct" },
    { id: "fix", kind: "money", q: "Quanto custam as despesas fixas por mês?",
      help: "Aluguel, salários e encargos, seu pró-labore, contador, sistemas, internet, luz. Tudo o que você paga vendendo ou não." },
    { id: "parc", kind: "money", q: "Quanto você paga de parcelas de empréstimos e financiamentos por mês?",
      help: "Some as parcelas de empréstimos, financiamentos e parcelamentos de impostos da empresa. Sem dívidas? Coloque 0." },
    { id: "caixa", kind: "money", q: "Quanto a empresa tem em caixa hoje?",
      help: "Saldo em conta mais aplicações que dá para resgatar rápido. Não conte o dinheiro pessoal." },
    { id: "prazo", kind: "choice", q: "Em quanto tempo, em média, você recebe as vendas?",
      help: "Considere a forma de pagamento mais comum dos seus clientes." },
    { id: "est", kind: "money", q: "Quanto você tem em estoque hoje, a preço de custo?",
      help: "Valor que você pagou pelas mercadorias ou matéria-prima paradas.", soProduto: true }
  ];

  function textoCustoVariavel(tipo) {
    if (tipo === "Serviços") {
      return {
        q: "De cada venda, quanto vai embora em custos que acompanham a venda? (%)",
        help: "Em % do preço: imposto da nota, comissões, taxa de cartão, material usado e terceiros contratados para aquele serviço.",
        ex: "Exemplo: um serviço de R$ 1.000 que gera R$ 150 de impostos e taxas e R$ 200 de material e terceiros → 35%."
      };
    }
    return {
      q: "De cada venda, quanto vai embora em mercadoria e custos da venda? (%)",
      help: "Em % do preço: custo da mercadoria ou matéria-prima, imposto da nota, comissões e taxa de cartão.",
      ex: "Exemplo: vende por R$ 100, a mercadoria custou R$ 40 e impostos e taxas dão R$ 12 → 52%."
    };
  }

  function numerosVisiveis(tipo) {
    return NUMEROS.filter(function (f) { return !f.soProduto || tipo !== "Serviços"; });
  }

  var HABITOS = [
    { id: "h1", col: "conta_separada", q: "A conta da empresa é separada da sua conta pessoal?" },
    { id: "h2", col: "registra_entradas_saidas", q: "Você registra todas as entradas e saídas de dinheiro?" },
    { id: "h3", col: "sabe_lucro_mes", q: "Você sabe quanto a empresa lucrou no mês passado?" },
    { id: "h4", col: "prolabore_fixo", q: "Você tira um pró-labore fixo, em vez de retirar dinheiro quando precisa?" },
    { id: "h5", col: "previsao_caixa", q: "Você acompanha quanto vai entrar e sair de dinheiro nas próximas semanas?" },
    { id: "h6", col: "faltou_dinheiro_contas", q: "Nos últimos 6 meses, faltou dinheiro para pagar alguma conta em dia?", inv: true },
    { id: "h7", col: "preco_por_custo", q: "Você calcula o preço de venda a partir dos seus custos?" },
    { id: "h8", col: "sabe_margem_produto", q: "Você sabe quais produtos ou serviços dão mais lucro?" },
    { id: "h9", col: "usa_credito_caro", q: "Você usa cheque especial, cartão ou antecipação de recebíveis para fechar o mês?", inv: true },
    { id: "h10", col: "tem_meta_orcamento", q: "A empresa tem meta de faturamento e orçamento para o ano?" }
  ];
  var RESPOSTAS = ["Sim", "Às vezes", "Não"];

  var PREOCUPACOES = [
    "O dinheiro não sobra no fim do mês",
    "Não sei se tenho lucro",
    "Não sei se meu preço está certo",
    "Dívidas e empréstimos",
    "Quero crescer, mas não sei se posso investir",
    "Organizar as finanças"
  ];

  var CHECKLIST_REUNIAO = [
    "Extrato da conta da empresa dos últimos 3 meses",
    "Lista das despesas fixas (aluguel, folha, sistemas)",
    "Empréstimos e financiamentos em aberto, com parcelas e prazos",
    "Se tiver: relatório de vendas do sistema ou da maquininha"
  ];

  var COLUNAS = [
    "data_hora", "id_sessao", "origem", "status",
    "nome", "empresa", "whatsapp", "email", "preocupacao", "consentimento_lgpd",
    "tipo", "segmento", "funcionarios", "tempo_empresa",
    "faturamento", "custo_variavel_pct", "despesas_fixas", "parcelas", "caixa",
    "prazo_recebimento", "estoque", "qtd_nao_sei"
  ].concat(HABITOS.map(function (h) { return h.col; })).concat([
    "nota", "classificacao",
    "nota_controle", "nota_caixa", "nota_margem", "nota_dividas", "nota_planejamento",
    "sobra_mensal", "ponto_equilibrio", "margem_seguranca_pct", "folego_caixa_dias",
    "margem_contribuicao_pct", "peso_dividas_pct", "meses_estoque",
    "alerta_1", "alerta_2", "alerta_3", "todos_alertas"
  ]);

  /* ------------------------------------------------------------ utilidades */
  // Arredondamento igual ao round() do Python (empate vai para o par).
  function pyRound(x) {
    var r = Math.round(x);
    if (Math.abs(x % 1) === 0.5) r = 2 * Math.round(x / 2);
    return r === 0 ? 0 : r; // evita -0
  }
  // Formata com N casas usando o valor binário exato e empate para o par,
  // como f"{x:.Nf}" e round(x, N) do Python (ex.: 2.15 vira "2.1", não "2.2").
  function fixo(x, casas) {
    var neg = x < 0;
    var s = Math.abs(x).toFixed(Math.min(100, casas + 60));
    var partes = s.split(".");
    var frac = partes[1] || "";
    var digitos = partes[0] + frac.slice(0, casas);
    var resto = frac.slice(casas);
    var sobe;
    if (resto[0] > "5") sobe = true;
    else if (resto[0] < "5" || resto === "") sobe = false;
    else if (/[1-9]/.test(resto.slice(1))) sobe = true;
    else sobe = Number(digitos[digitos.length - 1]) % 2 === 1;
    if (sobe) {
      var arr = digitos.split(""), k = arr.length - 1;
      while (k >= 0) {
        if (arr[k] === "9") { arr[k] = "0"; k--; } else { arr[k] = String(Number(arr[k]) + 1); break; }
      }
      if (k < 0) arr.unshift("1");
      digitos = arr.join("");
    }
    var inteiro = digitos.slice(0, digitos.length - casas) || "0";
    var dec = casas ? "." + digitos.slice(digitos.length - casas) : "";
    var out = inteiro + dec;
    return neg && /[1-9]/.test(out) ? "-" + out : out;
  }
  function arred(x, casas) {
    return Number(fixo(x, casas || 0));
  }
  function brl(valor) {
    var sinal = valor < 0 ? "− " : "";
    var inteiro = String(pyRound(Math.abs(valor))).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return sinal + "R$ " + inteiro;
  }
  function pct(x, casas) {
    return fixo(x * 100, casas || 0).replace(".", ",") + "%";
  }
  function vazio(v) { return v === null || v === undefined; }

  var NOTA_NIVEL = { good: 1, warn: 0.5, bad: 0 };
  var ROTULO_NIVEL = { good: "Saudável", warn: "Atenção", bad: "Crítico" };

  function nv(nivel) { return vazio(nivel) ? 0.25 : NOTA_NIVEL[nivel]; }
  function hv(H, id) {
    var h = HABITOS.filter(function (x) { return x.id === id; })[0];
    var resp = H[id];
    var v = resp === "Sim" ? 1 : resp === "Às vezes" ? 0.5 : 0;
    return h.inv ? 1 - v : v;
  }
  function media(H, ids) {
    var s = 0;
    ids.forEach(function (i) { s += hv(H, i); });
    return s / ids.length;
  }

  /* ------------------------------------------------------------ cálculo */
  /**
   * numeros: {fat, var (0-100), fix, parc, caixa, prazo (índice de PRAZOS), est}
   *          null = "não sei"
   * habitos: {h1: "Sim" | "Às vezes" | "Não", ...}
   */
  function calcular(tipo, numeros, habitos) {
    var campos = numerosVisiveis(tipo);
    var naoSei = campos.filter(function (f) { return vazio(numeros[f.id]); }).map(function (f) { return f.id; });

    var F = vazio(numeros.fat) ? null : numeros.fat;
    var v = vazio(numeros["var"]) ? null : numeros["var"] / 100;
    var C = vazio(numeros.fix) ? null : numeros.fix;
    var P = vazio(numeros.parc) ? null : numeros.parc;
    var K = vazio(numeros.caixa) ? null : numeros.caixa;
    var prazo = vazio(numeros.prazo) ? null : numeros.prazo;
    var est = tipo !== "Serviços" && !vazio(numeros.est) ? numeros.est : null;
    var Pz = P || 0;

    var r = {
      F: F, v: v, C: C, P: P, K: K, prazo: prazo, est: est,
      nao_sei: naoSei, qtd_nao_sei: naoSei.length, total_campos: campos.length,
      core: !!(F && F > 0 && v !== null && v < 1 && C !== null),
      mc: null, sobra: null, pe: null, ms: null, fol: null, div: null,
      nivel_sobra: null, nivel_ms: null, nivel_mc: null, nivel_fol: null, nivel_div: null
    };

    if (r.core) {
      r.mc = F * (1 - v);
      r.sobra = r.mc - C - Pz;
      r.pe = (C + Pz) / (1 - v);
      r.ms = (F - r.pe) / F;
      var s = r.sobra / F;
      r.nivel_sobra = s < 0 ? "bad" : s < 0.08 ? "warn" : "good";
      r.nivel_ms = r.ms < 0 ? "bad" : r.ms < 0.15 ? "warn" : "good";
      r.nivel_mc = (1 - v) < 0.25 ? "warn" : "good";
    }
    if (K !== null && C !== null && (C + Pz) > 0) {
      r.fol = K / ((C + Pz) / 30);
      r.nivel_fol = r.fol < 30 ? "bad" : r.fol < 90 ? "warn" : "good";
    }
    if (P !== null && F) {
      r.div = P / F;
      r.nivel_div = r.div > 0.2 ? "bad" : r.div > 0.1 ? "warn" : "good";
    }

    var H = habitos;
    var pil = {
      "Controle": media(H, ["h1", "h2", "h3"]) * 70 + (1 - naoSei.length / campos.length) * 30,
      "Caixa": media(H, ["h4", "h5", "h6"]) * 60 + nv(r.nivel_fol) * 40,
      "Margem e preço": media(H, ["h7", "h8"]) * 60 + nv(r.nivel_ms) * 40,
      "Dívidas": hv(H, "h9") * 50 + nv(r.nivel_div) * 50,
      "Planejamento": media(H, ["h5", "h10"]) * 100
    };
    var soma = 0;
    r.pilares = {};
    Object.keys(pil).forEach(function (k) { r.pilares[k] = pyRound(pil[k]); soma += r.pilares[k]; });
    r.nota = pyRound(soma / 5);

    var n = r.nota;
    if (n < 40) r.classe = ["Crítica", "bad", "Há riscos que podem comprometer a empresa nos próximos meses."];
    else if (n < 60) r.classe = ["Atenção", "warn", "A empresa funciona, mas está vulnerável a qualquer imprevisto."];
    else if (n < 80) r.classe = ["Estável", "good", "A base é boa. Há ajustes a fazer para crescer com segurança."];
    else r.classe = ["Saudável", "good", "Boa saúde financeira. O próximo passo é planejar o crescimento."];

    r.todos_alertas = alertas(r, H);
    r.alertas = r.todos_alertas.slice(0, 3);
    return r;
  }

  function alertas(r, H) {
    var A = [], F = r.F;
    function add(peso, nivel, titulo, texto) { A.push({ peso: peso, nivel: nivel, titulo: titulo, texto: texto }); }

    if (r.core && r.ms < 0)
      add(100, "bad", "A empresa está vendendo menos do que custa",
        "Para pagar as despesas fixas e as parcelas, você precisaria faturar " + brl(r.pe) + " por mês. " +
        "Hoje fatura " + brl(F) + ", o que deixa um buraco de cerca de " + brl(-r.sobra) + " todo mês.");
    if (r.fol !== null && r.fol < 30)
      add(95, "bad", "O caixa paga só " + Math.max(0, pyRound(r.fol)) + " dias de contas fixas",
        "Se as vendas pararem ou atrasarem, o dinheiro em conta acaba em menos de um mês. " +
        "Uma reserva confortável costuma cobrir de 3 a 6 meses de despesas fixas.");
    if (r.qtd_nao_sei >= 2)
      add(90, "warn", "Você não soube " + r.qtd_nao_sei + " dos " + r.total_campos + " números básicos",
        "Sem esses números, decisões de preço, contratação e investimento são tomadas no escuro. " +
        "Organizar essa informação é o primeiro passo de qualquer melhoria.");
    if (r.core && r.ms >= 0 && r.ms < 0.15)
      add(85, "warn", "Uma queda pequena nas vendas já leva ao prejuízo",
        "Se o faturamento cair " + pct(r.ms) + ", a empresa passa a operar no vermelho. " +
        "Um mês fraco ou um cliente grande a menos já basta.");
    if (H.h6 === "Sim" || H.h6 === "Às vezes")
      add(80, "bad", "Já faltou dinheiro para pagar contas em dia",
        "Atrasar contas gera juros e multas e tira seu poder de negociação com fornecedores. " +
        "Normalmente é sinal de que não existe previsão de caixa.");
    if (r.div !== null && r.div > 0.15)
      add(78, r.nivel_div, "As parcelas consomem " + pct(r.div) + " do faturamento",
        "São " + brl(r.P) + " por mês saindo antes de você pagar qualquer outra conta. " +
        "Vale olhar taxas, prazos e a possibilidade de renegociar.");
    if (r.prazo !== null && r.prazo >= 2 && (r.fol === null || r.fol < 90))
      add(75, "warn", "Você vende a prazo e tem pouco caixa para esperar",
        "As contas vencem antes de o dinheiro das vendas entrar. Esse descompasso é uma das causas " +
        "mais comuns de aperto em empresas que vendem bem.");
    if (H.h1 && H.h1 !== "Sim")
      add(72, "warn", "Dinheiro pessoal e da empresa misturados",
        "Quando as contas se misturam, fica impossível saber se a empresa dá lucro ou se é o seu " +
        "dinheiro pessoal que está bancando ela.");
    if (H.h9 === "Sim")
      add(70, "warn", "O mês fecha com crédito caro",
        "Cheque especial, rotativo do cartão e antecipação têm juros altos. Usados todo mês, " +
        "viram uma bola de neve.");
    if (media(H, ["h7", "h8"]) < 0.5)
      add(68, "warn", "Preço definido sem olhar os custos",
        "Sem saber a margem de cada produto ou serviço, você pode estar vendendo muito justamente " +
        "o que dá menos lucro, ou até prejuízo.");
    if (r.core && r.est !== null && r.v > 0) {
      var meses = r.est / (F * r.v);
      if (meses > 2)
        add(65, "warn", ("O estoque equivale a " + fixo(meses, 1) + " meses de vendas").replace(".", ","),
          "É dinheiro parado na prateleira que poderia estar no caixa. Vale entender o que gira " +
          "e o que está encalhado.");
    }
    if (H.h4 && H.h4 !== "Sim")
      add(60, "warn", "Retiradas sem regra",
        "Tirar dinheiro conforme a necessidade bagunça o caixa e esconde o lucro real. " +
        "Um pró-labore fixo resolve as duas coisas.");
    if (H.h5 && H.h5 !== "Sim")
      add(55, "warn", "Sem previsão de caixa",
        "Sem enxergar as próximas semanas, os apertos só aparecem quando já é tarde para reagir.");
    if (H.h10 && H.h10 !== "Sim")
      add(50, "warn", "Sem meta nem orçamento",
        "Sem meta, não há como saber se o mês foi bom ou ruim, nem quanto dá para investir " +
        "com segurança.");

    // ordenação estável por peso, como o sort() do Python
    return A.map(function (a, i) { return [a, i]; })
      .sort(function (x, y) { return (y[0].peso - x[0].peso) || (x[1] - y[1]); })
      .map(function (x) { return x[0]; });
  }

  function simularQueda(r, queda) {
    var F2 = r.F * (1 - queda);
    var sobra2 = F2 * (1 - r.v) - r.C - (r.P || 0);
    var caixa;
    if (sobra2 >= 0) caixa = "Não diminui";
    else if (r.K === null) caixa = "Sem dado de caixa";
    else {
      var dias = pyRound(r.K / (-sobra2) * 30);
      caixa = dias > 720 ? "Zera em mais de 2 anos" : "Zera em " + dias + " dias";
    }
    return { faturamento: F2, sobra: sobra2, caixa: caixa };
  }

  /* ------------------------------------------------------------ linha da planilha */
  // Mesmo conteúdo de diagnostico/planilha.py:montar_linha. "data_hora" é preenchida
  // pelo Apps Script (horário do servidor), e o texto digitado é higienizado lá também.
  function montarLinha(idSessao, origem, contato, perfil, numeros, habitos, r) {
    function num(ch) { return vazio(numeros[ch]) ? "não sei" : numeros[ch]; }
    function a(v, casas) { return vazio(v) ? "" : arred(v, casas || 0); }
    var p = r.pilares;
    var tit = r.alertas.map(function (x) { return x.titulo; }).concat(["", "", ""]);
    var L = {
      data_hora: "",
      id_sessao: idSessao,
      origem: origem,
      status: "Novo",
      nome: contato.nome || "",
      empresa: contato.empresa || "",
      whatsapp: contato.whatsapp || "",
      email: contato.email || "",
      preocupacao: contato.preocupacao || "",
      consentimento_lgpd: "Sim",
      tipo: perfil.tipo,
      segmento: perfil.segmento,
      funcionarios: perfil.funcionarios,
      tempo_empresa: perfil.tempo,
      faturamento: num("fat"),
      custo_variavel_pct: num("var"),
      despesas_fixas: num("fix"),
      parcelas: num("parc"),
      caixa: num("caixa"),
      prazo_recebimento: vazio(numeros.prazo) ? "não sei" : PRAZOS[numeros.prazo],
      estoque: perfil.tipo === "Serviços" ? "" : num("est"),
      qtd_nao_sei: r.qtd_nao_sei,
      nota: r.nota,
      classificacao: r.classe[0],
      nota_controle: p["Controle"],
      nota_caixa: p["Caixa"],
      nota_margem: p["Margem e preço"],
      nota_dividas: p["Dívidas"],
      nota_planejamento: p["Planejamento"],
      sobra_mensal: a(r.sobra),
      ponto_equilibrio: a(r.pe),
      margem_seguranca_pct: vazio(r.ms) ? "" : arred(r.ms * 100, 1),
      folego_caixa_dias: a(r.fol),
      margem_contribuicao_pct: vazio(r.v) ? "" : arred((1 - r.v) * 100, 1),
      peso_dividas_pct: vazio(r.div) ? "" : arred(r.div * 100, 1),
      meses_estoque: (r.core && r.est !== null && r.v) ? arred(r.est / (r.F * r.v), 1) : "",
      alerta_1: tit[0],
      alerta_2: tit[1],
      alerta_3: tit[2],
      todos_alertas: r.todos_alertas.map(function (x) { return x.titulo; }).join(" | ")
    };
    HABITOS.forEach(function (h) { L[h.col] = habitos[h.id] || ""; });
    return L;
  }

  return {
    TIPOS: TIPOS, TIPOS_LEGENDA: TIPOS_LEGENDA, SEGMENTOS: SEGMENTOS, FUNCIONARIOS: FUNCIONARIOS,
    TEMPO_EMPRESA: TEMPO_EMPRESA, PRAZOS: PRAZOS, NUMEROS: NUMEROS, HABITOS: HABITOS,
    RESPOSTAS: RESPOSTAS, PREOCUPACOES: PREOCUPACOES, CHECKLIST_REUNIAO: CHECKLIST_REUNIAO,
    COLUNAS: COLUNAS, ROTULO_NIVEL: ROTULO_NIVEL,
    textoCustoVariavel: textoCustoVariavel, numerosVisiveis: numerosVisiveis,
    calcular: calcular, simularQueda: simularQueda, montarLinha: montarLinha,
    brl: brl, pct: pct, pyRound: pyRound
  };
});
