/**
 * Autodiagnóstico Financeiro — Gestão Financeira Descomplicada
 * Recebe os diagnósticos da landing page e grava na aba "Leads" desta planilha.
 *
 * COMO INSTALAR (feito pelo Daniel, uma vez):
 *  1. Abra a planilha de leads no Google Sheets.
 *  2. Menu Extensões > Apps Script. Apague o que estiver lá e cole este arquivo inteiro.
 *  3. Salve (ícone de disquete). Rode a função "testar" uma vez (botão Executar) e autorize.
 *  4. Implantar > Nova implantação > tipo "App da Web":
 *       - Executar como: Eu
 *       - Quem pode acessar: Qualquer pessoa
 *     Copie a URL que termina em /exec e mande para a agência.
 *  5. Se alterar este código depois: Implantar > Gerenciar implantações > lápis >
 *     Versão: "Nova versão" > Implantar. Assim a URL continua a mesma.
 *
 * A mesma aba "Leads" pode receber dados do app Streamlit e da landing: as colunas são iguais.
 */

var ABA = "Leads";
var FUSO = "America/Sao_Paulo";

// Mesma ordem de diagnostico/planilha.py e kit-landing/gfd-calculos.js
var COLUNAS = [
  "data_hora", "id_sessao", "origem", "status",
  "nome", "empresa", "whatsapp", "email", "preocupacao", "consentimento_lgpd",
  "tipo", "segmento", "funcionarios", "tempo_empresa",
  "faturamento", "custo_variavel_pct", "despesas_fixas", "parcelas", "caixa",
  "prazo_recebimento", "estoque", "qtd_nao_sei",
  "conta_separada", "registra_entradas_saidas", "sabe_lucro_mes", "prolabore_fixo", "previsao_caixa",
  "faltou_dinheiro_contas", "preco_por_custo", "sabe_margem_produto", "usa_credito_caro", "tem_meta_orcamento",
  "nota", "classificacao",
  "nota_controle", "nota_caixa", "nota_margem", "nota_dividas", "nota_planejamento",
  "sobra_mensal", "ponto_equilibrio", "margem_seguranca_pct", "folego_caixa_dias",
  "margem_contribuicao_pct", "peso_dividas_pct", "meses_estoque",
  "alerta_1", "alerta_2", "alerta_3", "todos_alertas"
];

function doPost(e) {
  try {
    var dados = JSON.parse(e.postData.contents || "{}");
    if (dados.site) return resposta({ ok: true });            // armadilha anti-robô preenchida: ignora
    var L = dados.linha || {};
    if (!L.nome || String(L.whatsapp || "").replace(/\D/g, "").length < 10) {
      return resposta({ ok: false, erro: "nome e WhatsApp são obrigatórios" });
    }

    var lock = LockService.getScriptLock();
    lock.waitLock(10000);
    try {
      var aba = prepararAba();
      var linha = COLUNAS.map(function (col) {
        if (col === "data_hora") return Utilities.formatDate(new Date(), FUSO, "dd/MM/yyyy HH:mm:ss");
        if (col === "status") return "Novo";
        if (col === "whatsapp") return "'" + limitar(L.whatsapp);
        var v = L[col];
        if (v === undefined || v === null) return "";
        if (typeof v === "number") return isFinite(v) ? v : "";
        return texto(v);
      });
      aba.appendRow(linha);
    } finally {
      lock.releaseLock();
    }
    return resposta({ ok: true });
  } catch (err) {
    console.error(err);
    return resposta({ ok: false, erro: String(err) });
  }
}

// Abrir a URL /exec no navegador mostra se está no ar.
function doGet() {
  return resposta({ ok: true, servico: "autodiagnostico-gfd" });
}

function prepararAba() {
  var planilha = SpreadsheetApp.getActiveSpreadsheet();
  var aba = planilha.getSheetByName(ABA) || planilha.insertSheet(ABA);
  var atual = aba.getLastColumn() ? aba.getRange(1, 1, 1, aba.getLastColumn()).getValues()[0] : [];
  if (atual.join("|") !== COLUNAS.join("|")) {
    if (aba.getMaxColumns() < COLUNAS.length) aba.insertColumnsAfter(aba.getMaxColumns(), COLUNAS.length - aba.getMaxColumns());
    aba.getRange(1, 1, 1, COLUNAS.length).setValues([COLUNAS]).setFontWeight("bold");
    aba.setFrozenRows(1);
  }
  return aba;
}

// Texto digitado pelo visitante: corta tamanho e impede que vire fórmula na planilha.
function texto(v) {
  var s = limitar(v);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}
function limitar(v) {
  return String(v == null ? "" : v).trim().slice(0, 1000);
}

function resposta(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Rode uma vez pelo editor para autorizar e conferir a aba (não grava lead).
function testar() {
  var aba = prepararAba();
  Logger.log("OK! Aba '" + aba.getName() + "' pronta com " + COLUNAS.length + " colunas.");
}
