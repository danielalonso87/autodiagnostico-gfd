/*!
 * Autodiagnóstico Financeiro — Gestão Financeira Descomplicada
 * Widget para embutir na landing page. Requer gfd-calculos.js carregado antes.
 *
 * Uso:
 *   <div id="gfd-diagnostico"></div>
 *   <script>
 *     GFDDiagnostico.iniciar("#gfd-diagnostico", {
 *       endpoint: "https://script.google.com/macros/s/XXXX/exec",  // URL do Apps Script
 *       whatsapp: "5521999999999"
 *     });
 *   </script>
 *
 * Eventos para Google Tag Manager / Google Ads (window.dataLayer):
 *   gfd_inicio            — clicou em "Começar diagnóstico"
 *   gfd_etapa             — avançou de etapa (gfd_etapa: perfil|numeros|habitos|contato)
 *   gfd_concluido         — enviou o contato e viu o resultado (CONVERSÃO PRINCIPAL)
 *   gfd_whatsapp          — clicou no botão do WhatsApp (conversão secundária)
 */
(function (global) {
  "use strict";
  var C = global.GFDCalc;
  if (!C) { console.error("[GFD] Carregue gfd-calculos.js antes de gfd-diagnostico.js"); return; }

  var ETAPAS = ["perfil", "numeros", "habitos", "contato"];
  var TITULOS = { perfil: "Sua empresa", numeros: "Números", habitos: "Rotina", contato: "Contato" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function idAleatorio() {
    var a = "abcdefghijklmnopqrstuvwxyz0123456789", s = "";
    for (var i = 0; i < 10; i++) s += a[Math.floor(Math.random() * a.length)];
    return s;
  }
  function origemDaUrl(padrao) {
    try {
      var p = new URLSearchParams(global.location.search);
      return p.get("origem") || p.get("utm_source") || padrao;
    } catch (e) { return padrao; }
  }

  function iniciar(alvo, opcoes) {
    var raiz = typeof alvo === "string" ? document.querySelector(alvo) : alvo;
    if (!raiz) { console.error("[GFD] Elemento não encontrado:", alvo); return; }
    var cfg = Object.assign({
      endpoint: "",                 // URL /exec do Google Apps Script
      whatsapp: "",                 // 55 + DDD + número, só dígitos
      nomeConsultor: "Daniel",
      origemPadrao: "site",
      rolarAoTrocar: true,          // rola até o topo do widget ao trocar de etapa
      aoEvento: null,               // function(nome, dados) — opcional
      aoConcluir: null              // function(resultado, linha) — opcional
    }, opcoes || {});

    raiz.classList.add("gfd");
    var S = novoEstado();

    function novoEstado() {
      var nums = {};
      C.NUMEROS.forEach(function (f) { nums[f.id] = { v: null, ns: false }; });
      return { tela: "intro", perfil: { tipo: null, segmento: "", funcionarios: null, tempo: null },
               nums: nums, hab: {}, contato: {}, idSessao: idAleatorio(), origem: origemDaUrl(cfg.origemPadrao),
               resultado: null, linha: null, queda: 10, faltas: [] };
    }

    function evento(nome, dados) {
      var d = Object.assign({ event: nome, gfd_origem: S.origem }, dados || {});
      try { (global.dataLayer = global.dataLayer || []).push(d); } catch (e) { /* sem GTM */ }
      if (typeof cfg.aoEvento === "function") { try { cfg.aoEvento(nome, d); } catch (e) { console.error(e); } }
    }

    function ir(tela) {
      S.tela = tela; S.faltas = [];
      render();
      if (cfg.rolarAoTrocar) {
        var topo = raiz.getBoundingClientRect().top + global.pageYOffset - 20;
        if (global.pageYOffset > topo) global.scrollTo({ top: topo, behavior: "smooth" });
      }
    }

    /* ---------------------------------------------------------- telas */
    function render() {
      var html = "";
      if (S.tela === "intro") html = telaIntro();
      else if (S.tela === "resultado") html = telaResultado();
      else html = progresso() + ({ perfil: telaPerfil, numeros: telaNumeros, habitos: telaHabitos, contato: telaContato })[S.tela]() + navegacao();
      raiz.innerHTML = '<div class="gfd-tela">' + html + "</div>";
      ligar();
    }

    function telaIntro() {
      return '<div class="gfd-intro"><div>' +
        '<span class="gfd-sobre">Gratuito · cerca de 5 minutos</span>' +
        "<h2>Quantos dias sua empresa aguenta sem vender?</h2>" +
        '<p class="gfd-lead">Responda algumas perguntas com valores aproximados. No final você vê a <strong>nota de saúde financeira</strong> da empresa, os números que mais importam para o seu negócio e os <strong>3 pontos que pedem atenção agora</strong>.</p>' +
        '<p class="gfd-nota-info">Não precisa de planilha nem extrato. Se não souber algum número, marque <strong>Não sei</strong>. Isso também faz parte do diagnóstico.</p>' +
        '<div class="gfd-acoes"><button type="button" class="gfd-btn" data-acao="comecar">Começar diagnóstico</button></div>' +
        '</div><div class="gfd-recebe"><span class="gfd-sobre">O que você recebe</span>' +
        "<p><strong>1. Nota de 0 a 100</strong>Saúde financeira em 5 áreas: controle, caixa, margem, dívidas e planejamento.</p>" +
        "<p><strong>2. Seus números-chave</strong>Ponto de equilíbrio, fôlego de caixa, margem de segurança e quanto sobra por mês.</p>" +
        "<p><strong>3. Os 3 riscos prioritários</strong>O que resolver primeiro, explicado sem financês.</p>" +
        "</div></div>";
    }

    function progresso() {
      var i = ETAPAS.indexOf(S.tela);
      return '<div class="gfd-prog"><span>Passo ' + (i + 1) + " de 4 · " + TITULOS[S.tela] + '</span><div><i style="width:' + ((i + 1) / 4 * 100) + '%"></i></div></div>';
    }

    function navegacao() {
      var erro = "";
      if (S.faltas.length) {
        erro = '<div class="gfd-erro" role="alert">Falta responder:<ul>' +
          S.faltas.map(function (f) { return "<li>" + esc(f) + "</li>"; }).join("") + "</ul>" +
          (S.tela === "numeros" ? "Se não souber algum número, marque <strong>Não sei</strong>." : "") + "</div>";
      }
      return erro + '<div class="gfd-nav"><button type="button" class="gfd-btn gfd-btn-sec" data-acao="voltar">Voltar</button>' +
        '<button type="button" class="gfd-btn" data-acao="avancar">' + (S.tela === "contato" ? "Ver meu diagnóstico" : "Continuar") + "</button></div>";
    }

    function falta(chave) { return S.faltas._chaves && S.faltas._chaves.indexOf(chave) >= 0 ? " gfd-falta" : ""; }

    function chips(grupo, opcoes, atual) {
      return '<div class="gfd-chips">' + opcoes.map(function (o) {
        return '<button type="button" class="gfd-chip" data-grupo="' + grupo + '" data-v="' + esc(o) + '" aria-pressed="' + (atual === o) + '">' + esc(o) + "</button>";
      }).join("") + "</div>";
    }

    function telaPerfil() {
      var p = S.perfil;
      return "<h3>Conte um pouco sobre a empresa</h3>" +
        '<div class="gfd-campo' + falta("tipo") + '"><span class="gfd-q">O que a empresa vende?</span><div class="gfd-cards3">' +
        C.TIPOS.map(function (t, i) {
          return '<button type="button" class="gfd-pick" data-grupo="tipo" data-v="' + esc(t) + '" aria-pressed="' + (p.tipo === t) + '"><strong>' + esc(t) + "</strong><span>" + esc(C.TIPOS_LEGENDA[i]) + "</span></button>";
        }).join("") + "</div></div>" +
        '<div class="gfd-campo' + falta("segmento") + '"><label class="gfd-q" for="gfd-segmento">Qual o segmento?</label><select id="gfd-segmento" data-campo="segmento"><option value="">Escolha uma opção</option>' +
        C.SEGMENTOS.map(function (s) { return "<option" + (p.segmento === s ? " selected" : "") + ">" + esc(s) + "</option>"; }).join("") + "</select></div>" +
        '<div class="gfd-campo' + falta("funcionarios") + '"><span class="gfd-q">Quantas pessoas trabalham na empresa?</span>' + chips("funcionarios", C.FUNCIONARIOS, p.funcionarios) + "</div>" +
        '<div class="gfd-campo' + falta("tempo") + '"><span class="gfd-q">Há quanto tempo a empresa existe?</span>' + chips("tempo", C.TEMPO_EMPRESA, p.tempo) + "</div>";
    }

    function telaNumeros() {
      var h = "<h3>Os números do mês, de cabeça</h3><p class=\"gfd-suave\">Valores aproximados de um mês normal. Arredondar está ótimo.</p>";
      C.numerosVisiveis(S.perfil.tipo).forEach(function (f) {
        var st = S.nums[f.id];
        var botaoNs = '<button type="button" class="gfd-naosei" data-naosei="' + f.id + '" aria-pressed="' + st.ns + '">Não sei</button>';
        if (f.kind === "money") {
          h += '<div class="gfd-campo' + falta(f.id) + '" data-num="' + f.id + '"><label class="gfd-q" for="gfd-n-' + f.id + '">' + esc(f.q) + '</label><p class="gfd-ajuda">' + esc(f.help) + "</p>" +
            '<div class="gfd-valor"><div class="gfd-caixa-valor"><span>R$</span><input type="text" inputmode="numeric" autocomplete="off" placeholder="0" id="gfd-n-' + f.id + '" data-dinheiro="' + f.id + '" value="' + (st.v === null ? "" : st.v.toLocaleString("pt-BR")) + '"></div>' + botaoNs + "</div></div>";
        } else if (f.kind === "pct") {
          var t = C.textoCustoVariavel(S.perfil.tipo);
          h += '<div class="gfd-campo' + falta(f.id) + '" data-num="var"><label class="gfd-q" for="gfd-n-var">' + esc(t.q) + '</label><p class="gfd-ajuda">' + esc(t.help) + '</p><p class="gfd-exemplo">' + esc(t.ex) + "</p>" +
            '<div class="gfd-valor"><div class="gfd-caixa-valor" style="max-width:160px"><input type="text" inputmode="numeric" autocomplete="off" placeholder="0" id="gfd-n-var" data-pct="var" value="' + (st.v === null ? "" : st.v) + '"><span style="padding:0 12px 0 0">%</span></div>' + botaoNs + "</div>" +
            '<div class="gfd-chips">' + [20, 30, 40, 50, 60, 70].map(function (p) {
              return '<button type="button" class="gfd-chip" data-atalho="' + p + '" aria-pressed="' + (st.v === p) + '">' + p + "%</button>";
            }).join("") + "</div></div>";
        } else {
          h += '<div class="gfd-campo' + falta(f.id) + '" data-num="prazo"><span class="gfd-q">' + esc(f.q) + '</span><p class="gfd-ajuda">' + esc(f.help) + "</p>" +
            '<div class="gfd-chips">' + C.PRAZOS.map(function (o, i) {
              return '<button type="button" class="gfd-chip" data-prazo="' + i + '" aria-pressed="' + (st.v === i) + '">' + esc(o) + "</button>";
            }).join("") + botaoNs + "</div></div>";
        }
      });
      return h;
    }

    function telaHabitos() {
      return "<h3>Como é a rotina financeira hoje</h3><p class=\"gfd-suave\">Responda pensando nos últimos 6 meses. Não existe resposta certa.</p>" +
        C.HABITOS.map(function (hb) {
          return '<div class="gfd-campo gfd-hab' + falta(hb.id) + '"><span class="gfd-q">' + esc(hb.q) + '</span><div class="gfd-seg" role="group" aria-label="' + esc(hb.q) + '">' +
            C.RESPOSTAS.map(function (r) {
              return '<button type="button" data-hab="' + hb.id + '" data-v="' + esc(r) + '" aria-pressed="' + (S.hab[hb.id] === r) + '">' + esc(r) + "</button>";
            }).join("") + "</div></div>";
        }).join("");
    }

    function telaContato() {
      var c = S.contato;
      return "<h3>Para onde enviamos seu diagnóstico?</h3><p class=\"gfd-suave\">Seu resultado aparece logo depois.</p>" +
        '<div class="gfd-campo' + (S.faltas.length ? " gfd-falta" : "") + '"><div class="gfd-grid2">' +
        '<div><label for="gfd-nome">Seu nome *</label><input type="text" id="gfd-nome" data-contato="nome" autocomplete="name" value="' + esc(c.nome) + '"></div>' +
        '<div><label for="gfd-empresa">Nome da empresa</label><input type="text" id="gfd-empresa" data-contato="empresa" autocomplete="organization" value="' + esc(c.empresa) + '"></div>' +
        '<div><label for="gfd-whats">WhatsApp com DDD *</label><input type="tel" id="gfd-whats" data-contato="whatsapp" inputmode="tel" autocomplete="tel" placeholder="(21) 99999-9999" value="' + esc(c.whatsapp) + '"></div>' +
        '<div><label for="gfd-email">E-mail</label><input type="email" id="gfd-email" data-contato="email" autocomplete="email" value="' + esc(c.email) + '"></div>' +
        "</div>" +
        '<div style="display:flex;flex-direction:column;gap:6px"><label class="gfd-rot" for="gfd-preoc">O que mais te preocupa hoje na empresa?</label><select id="gfd-preoc" data-contato="preocupacao"><option value="">Escolha (opcional)</option>' +
        C.PREOCUPACOES.map(function (p) { return "<option" + (c.preocupacao === p ? " selected" : "") + ">" + esc(p) + "</option>"; }).join("") + "</select></div>" +
        '<input type="text" class="gfd-mel" tabindex="-1" autocomplete="off" aria-hidden="true" data-contato="site" value="">' +
        '<label class="gfd-check"><input type="checkbox" data-contato="lgpd"' + (c.lgpd ? " checked" : "") + '><span>Autorizo o contato da Gestão Financeira Descomplicada pelo WhatsApp e e-mail informados e o uso destas respostas apenas para preparar meu diagnóstico, conforme a LGPD.</span></label></div>';
    }

    /* ---------------------------------------------------------- resultado */
    function anel(nota, nivel) {
      var R = 52, Cc = 2 * Math.PI * R, off = Cc * (1 - nota / 100);
      var cor = { good: "var(--gfd-bom)", warn: "var(--gfd-atencao)", bad: "var(--gfd-ruim)" }[nivel];
      return '<svg width="132" height="132" viewBox="0 0 132 132" role="img" aria-label="Nota ' + nota + ' de 100">' +
        '<circle cx="66" cy="66" r="' + R + '" fill="none" stroke="var(--gfd-superficie-2)" stroke-width="12"/>' +
        '<circle cx="66" cy="66" r="' + R + '" fill="none" stroke="' + cor + '" stroke-width="12" stroke-linecap="round" stroke-dasharray="' + Cc + '" stroke-dashoffset="' + off + '" transform="rotate(-90 66 66)"/>' +
        '<text x="66" y="72" text-anchor="middle" font-size="34" font-weight="700" fill="var(--gfd-texto)">' + nota + "</text>" +
        '<text x="66" y="92" text-anchor="middle" font-size="11" fill="var(--gfd-suave)">de 100</text></svg>';
    }

    function radar(pil) {
      var k = Object.keys(pil), cx = 180, cy = 150, R = 96, N = k.length, g = "";
      function pt(i, f) { var a = -Math.PI / 2 + i * 2 * Math.PI / N; return [cx + Math.cos(a) * R * f, cy + Math.sin(a) * R * f]; }
      [0.25, 0.5, 0.75, 1].forEach(function (f) {
        g += '<polygon points="' + k.map(function (_, i) { return pt(i, f).join(","); }).join(" ") + '" fill="none" stroke="var(--gfd-linha)"/>';
      });
      k.forEach(function (_, i) { var p = pt(i, 1); g += '<line x1="' + cx + '" y1="' + cy + '" x2="' + p[0] + '" y2="' + p[1] + '" stroke="var(--gfd-linha)"/>'; });
      g += '<polygon points="' + k.map(function (n, i) { return pt(i, Math.max(0.04, pil[n] / 100)).join(","); }).join(" ") + '" fill="var(--gfd-destaque)" fill-opacity=".22" stroke="var(--gfd-destaque)" stroke-width="2"/>';
      k.forEach(function (n, i) {
        var p = pt(i, 1.2), anc = Math.abs(p[0] - cx) < 10 ? "middle" : p[0] > cx ? "start" : "end";
        g += '<text x="' + p[0] + '" y="' + p[1] + '" text-anchor="' + anc + '" font-size="12" fill="var(--gfd-suave)">' + esc(n) + "</text>" +
             '<text x="' + p[0] + '" y="' + (p[1] + 15) + '" text-anchor="' + anc + '" font-size="13" font-weight="700" fill="var(--gfd-texto)">' + pil[n] + "</text>";
      });
      return '<svg class="gfd-radar" viewBox="-40 0 440 300" role="img" aria-label="Nota por área">' + g + "</svg>";
    }

    function kpi(rot, val, sub, nivel, faltou) {
      if (val === null) {
        return '<div class="gfd-kpi"><div class="gfd-kpi-rot">' + rot + '<span class="gfd-pilula gfd-p-none">Sem dado</span></div><div class="gfd-kpi-val">—</div><div class="gfd-kpi-sub">Faltou: ' + faltou + ".</div></div>";
      }
      var pill = nivel ? '<span class="gfd-pilula gfd-p-' + nivel + '">' + C.ROTULO_NIVEL[nivel] + "</span>" : "";
      return '<div class="gfd-kpi' + (nivel ? " gfd-" + nivel : "") + '"><div class="gfd-kpi-rot">' + rot + pill + '</div><div class="gfd-kpi-val">' + val + '</div><div class="gfd-kpi-sub">' + sub + "</div></div>";
    }

    function faltouNomes(ids) {
      var nomes = { fat: "faturamento", "var": "custos da venda", fix: "despesas fixas", parc: "parcelas", caixa: "saldo em caixa" };
      var n = ids.filter(function (i) { return numeros()[i] === null; }).map(function (i) { return nomes[i]; });
      return n.join(", ") || "dados";
    }

    function telaResultado() {
      var r = S.resultado, c = S.contato;
      var nome = (c.empresa || "").trim() || (c.nome || "").trim() || "sua empresa";
      var cls = r.classe, core = r.core, fc = faltouNomes(["fat", "var", "fix"]);
      var hoje = new Date().toLocaleDateString("pt-BR");
      var h = '<div class="gfd-res-topo"><div><span class="gfd-sobre">Diagnóstico · ' + hoje + "</span><h3>Saúde financeira de " + esc(nome) + '</h3></div><button type="button" class="gfd-btn gfd-btn-sec" data-acao="refazer">Refazer</button></div>' +
        '<div class="gfd-dupla"><div class="gfd-painel"><div class="gfd-nota">' + anel(r.nota, cls[1]) + '<div><span class="gfd-pilula gfd-p-' + cls[1] + '">' + cls[0] + '</span><p style="font-weight:600">' + cls[2] + '</p><p class="gfd-suave" style="font-size:.85rem">' +
        (r.qtd_nao_sei ? 'Você marcou "não sei" em ' + r.qtd_nao_sei + " de " + r.total_campos + " números." : "Você respondeu todos os números.") + "</p></div></div></div>" +
        '<div class="gfd-painel"><h4>Nota por área</h4>' + radar(r.pilares) + "</div></div>" +
        "<h4>Seus números-chave</h4><div class=\"gfd-kpis\">" +
        kpi("Sobra mensal estimada", core ? C.brl(r.sobra) : null, core ? C.pct(r.sobra / r.F, 1) + " do faturamento, depois de custos, despesas fixas e parcelas." : "", r.nivel_sobra, fc) +
        kpi("Ponto de equilíbrio", core ? C.brl(r.pe) : null, "Faturamento mínimo por mês para não ter prejuízo.", r.nivel_ms, fc) +
        kpi("Margem de segurança", core ? C.pct(r.ms) : null, core && r.ms < 0 ? "Faturamento abaixo do ponto de equilíbrio." : "Quanto as vendas podem cair antes do prejuízo.", r.nivel_ms, fc) +
        kpi("Fôlego de caixa", r.fol !== null ? Math.max(0, C.pyRound(r.fol)) + " dias" : null, "Por quanto tempo o caixa paga as contas fixas e parcelas sem nenhuma venda.", r.nivel_fol, faltouNomes(["caixa", "fix"])) +
        kpi("Margem de contribuição", core ? C.pct(1 - r.v) : null, core ? "De cada R$ 100 vendidos, sobram R$ " + C.pyRound((1 - r.v) * 100) + " para pagar as despesas fixas." : "", r.nivel_mc, fc) +
        kpi("Peso das dívidas", r.div !== null ? C.pct(r.div) : null, r.div !== null ? C.brl(r.P) + " em parcelas por mês sobre o faturamento." : "", r.nivel_div, faltouNomes(["parc", "fat"])) +
        "</div>";

      if (core) {
        var max = Math.max(r.F, r.pe) * 1.18, ok = r.F >= r.pe, folga = r.F - r.pe;
        h += '<div class="gfd-painel"><h4>Onde você está em relação ao ponto de equilíbrio</h4>' +
          '<div class="gfd-regua"><div class="gfd-trilho"><div class="gfd-preench" style="width:' + (r.F / max * 100) + "%;background:var(--gfd-" + (ok ? "bom" : "ruim") + ')"></div></div>' +
          '<div class="gfd-pe" style="left:' + (r.pe / max * 100) + '%"><span style="transform:translateX(' + (r.pe / max > 0.7 ? "-100%" : r.pe / max < 0.3 ? "0" : "-50%") + ')">Equilíbrio ' + C.brl(r.pe) + "</span></div>" +
          '<div class="gfd-legenda"><span>Seu faturamento: <b>' + C.brl(r.F) + "</b></span><span>" + (folga >= 0 ? "Folga de " + C.brl(folga) : "Faltam " + C.brl(-folga)) + " por mês</span></div></div>" +
          '<div class="gfd-sim"><label for="gfd-queda" style="font-weight:600">E se as vendas caírem <span data-sim="p">' + S.queda + "%</span>?</label>" +
          '<input type="range" id="gfd-queda" min="0" max="50" step="5" value="' + S.queda + '">' +
          '<div class="gfd-sim-out"><div><span>Faturamento</span><b data-sim="f"></b></div><div><span>Sobra no mês</span><b data-sim="s"></b></div><div><span>Caixa</span><b data-sim="c"></b></div></div>' +
          '<p class="gfd-suave" style="font-size:.8rem">Simulação mantendo despesas fixas e parcelas iguais e os custos da venda proporcionais ao faturamento.</p></div></div>';
      }

      h += "<h4>O que resolver primeiro</h4>";
      if (r.alertas.length) {
        h += '<ol class="gfd-alertas">' + r.alertas.map(function (a, i) {
          return '<li><span class="gfd-n gfd-p-' + a.nivel + '">' + (i + 1) + "</span><div><b>" + esc(a.titulo) + "</b><p>" + esc(a.texto) + "</p></div></li>";
        }).join("") + "</ol>";
      } else {
        h += '<ol class="gfd-alertas"><li><span class="gfd-n gfd-p-good">✓</span><div><b>Nenhum risco grave encontrado</b><p>A base está organizada. Na reunião dá para olhar crescimento e investimentos.</p></div></li></ol>';
      }

      var botao = "";
      if (cfg.whatsapp) {
        var msg = "Olá, " + cfg.nomeConsultor + "! Fiz o autodiagnóstico da " + nome + " (nota " + r.nota + ") e quero agendar a reunião gratuita.";
        botao = '<a class="gfd-btn" data-acao="whatsapp" target="_blank" rel="noopener" href="https://wa.me/' + String(cfg.whatsapp).replace(/\D/g, "") + "?text=" + encodeURIComponent(msg) + '">Agendar pelo WhatsApp</a>';
      }
      h += '<div class="gfd-cta"><div><h3>Quer validar esses números com os dados reais?</h3><p>Na reunião gratuita de 45 minutos, conferimos este diagnóstico com o extrato e os números da sua empresa e você sai com um plano de ação para os próximos 90 dias.</p></div>' + botao + "</div>" +
        "<details><summary>O que separar para a reunião</summary><ul>" + C.CHECKLIST_REUNIAO.map(function (i) { return "<li>" + esc(i) + "</li>"; }).join("") + "</ul></details>";
      return h;
    }

    function atualizarSimulacao() {
      var r = S.resultado; if (!r || !r.core) return;
      var s = C.simularQueda(r, S.queda / 100), cor = s.sobra < 0 ? "var(--gfd-ruim)" : "var(--gfd-bom)";
      var q = function (k) { return raiz.querySelector('[data-sim="' + k + '"]'); };
      q("p").textContent = S.queda + "%";
      q("f").textContent = C.brl(s.faturamento);
      q("s").textContent = C.brl(s.sobra); q("s").style.color = cor;
      q("c").textContent = s.caixa; q("c").style.color = cor;
    }

    /* ---------------------------------------------------------- dados */
    function numeros() {
      var out = {};
      C.numerosVisiveis(S.perfil.tipo).forEach(function (f) {
        var st = S.nums[f.id];
        out[f.id] = st.ns || st.v === null ? null : st.v;
      });
      if (S.perfil.tipo === "Serviços") out.est = null;
      return out;
    }

    function validar() {
      var f = [], chaves = [];
      function add(chave, texto) { chaves.push(chave); f.push(texto); }
      if (S.tela === "perfil") {
        if (!S.perfil.tipo) add("tipo", "o que a empresa vende");
        if (!S.perfil.segmento) add("segmento", "segmento");
        if (!S.perfil.funcionarios) add("funcionarios", "número de pessoas");
        if (!S.perfil.tempo) add("tempo", "tempo de empresa");
      } else if (S.tela === "numeros") {
        C.numerosVisiveis(S.perfil.tipo).forEach(function (n) {
          var st = S.nums[n.id];
          if (st.v === null && !st.ns) add(n.id, n.q || C.textoCustoVariavel(S.perfil.tipo).q);
        });
      } else if (S.tela === "habitos") {
        C.HABITOS.forEach(function (hb) { if (!S.hab[hb.id]) add(hb.id, hb.q); });
      } else if (S.tela === "contato") {
        var c = S.contato;
        if (!(c.nome || "").trim()) add("nome", "seu nome");
        if ((c.whatsapp || "").replace(/\D/g, "").length < 10) add("whatsapp", "WhatsApp com DDD");
        if ((c.email || "").trim() && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(c.email.trim())) add("email", "um e-mail válido (ou deixe em branco)");
        if (!c.lgpd) add("lgpd", "a autorização de contato");
      }
      f._chaves = chaves;
      return f;
    }

    function concluir() {
      var nums = numeros();
      var r = C.calcular(S.perfil.tipo, nums, S.hab);
      var c = S.contato;
      var linha = C.montarLinha(S.idSessao, S.origem,
        { nome: (c.nome || "").trim(), empresa: (c.empresa || "").trim(), whatsapp: (c.whatsapp || "").trim(),
          email: (c.email || "").trim(), preocupacao: c.preocupacao || "" },
        { tipo: S.perfil.tipo, segmento: S.perfil.segmento, funcionarios: S.perfil.funcionarios, tempo: S.perfil.tempo },
        nums, S.hab, r);
      S.resultado = r; S.linha = linha;
      enviar(linha, c.site || "");
      evento("gfd_concluido", { gfd_nota: r.nota, gfd_classificacao: r.classe[0], gfd_segmento: S.perfil.segmento });
      if (typeof cfg.aoConcluir === "function") { try { cfg.aoConcluir(r, linha); } catch (e) { console.error(e); } }
      ir("resultado");
    }

    function enviar(linha, armadilha) {
      if (!cfg.endpoint) { console.warn("[GFD] endpoint não configurado: o lead não foi gravado.", linha); return; }
      try {
        // text/plain + no-cors: o Apps Script recebe sem bloqueio de CORS (não lemos a resposta).
        fetch(cfg.endpoint, {
          method: "POST", mode: "no-cors", keepalive: true,
          headers: { "Content-Type": "text/plain;charset=utf-8" },
          body: JSON.stringify({ linha: linha, site: armadilha })
        }).catch(function (e) { console.error("[GFD] Falha ao gravar o lead:", e); });
      } catch (e) { console.error("[GFD] Falha ao gravar o lead:", e); }
    }

    /* ---------------------------------------------------------- eventos da interface */
    function ligar() {
      raiz.querySelectorAll("[data-acao]").forEach(function (b) {
        b.addEventListener("click", function () {
          var a = b.getAttribute("data-acao");
          if (a === "comecar") { evento("gfd_inicio"); ir("perfil"); }
          else if (a === "voltar") { var i = ETAPAS.indexOf(S.tela); ir(i > 0 ? ETAPAS[i - 1] : "intro"); }
          else if (a === "avancar") {
            var f = validar();
            if (f.length) { S.faltas = f; render(); var el = raiz.querySelector(".gfd-falta"); if (el) el.scrollIntoView({ behavior: "smooth", block: "center" }); return; }
            evento("gfd_etapa", { gfd_etapa: S.tela });
            var j = ETAPAS.indexOf(S.tela);
            if (j < ETAPAS.length - 1) ir(ETAPAS[j + 1]); else concluir();
          }
          else if (a === "refazer") { S = novoEstado(); ir("intro"); }
          else if (a === "whatsapp") { evento("gfd_whatsapp", { gfd_nota: S.resultado && S.resultado.nota }); }
        });
      });

      raiz.querySelectorAll("[data-grupo]").forEach(function (b) {
        b.addEventListener("click", function () {
          var g = b.getAttribute("data-grupo");
          S.perfil[g] = b.getAttribute("data-v");
          raiz.querySelectorAll('[data-grupo="' + g + '"]').forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
          b.closest(".gfd-campo").classList.remove("gfd-falta");
        });
      });
      var seg = raiz.querySelector('[data-campo="segmento"]');
      if (seg) seg.addEventListener("change", function () { S.perfil.segmento = seg.value; seg.closest(".gfd-campo").classList.remove("gfd-falta"); });

      raiz.querySelectorAll("[data-dinheiro]").forEach(function (inp) {
        inp.addEventListener("input", function () {
          var id = inp.getAttribute("data-dinheiro"), st = S.nums[id], d = inp.value.replace(/\D/g, "").slice(0, 12);
          st.v = d === "" ? null : parseInt(d, 10);
          inp.value = d === "" ? "" : st.v.toLocaleString("pt-BR");
          if (st.v !== null) { st.ns = false; marcarNs(id); }
          inp.closest(".gfd-campo").classList.remove("gfd-falta");
        });
      });
      raiz.querySelectorAll("[data-pct]").forEach(function (inp) {
        inp.addEventListener("input", function () {
          var st = S.nums["var"], d = inp.value.replace(/\D/g, "").slice(0, 2);
          st.v = d === "" ? null : Math.min(95, parseInt(d, 10));
          inp.value = d === "" ? "" : String(st.v);
          if (st.v !== null) { st.ns = false; marcarNs("var"); }
          marcarAtalhos();
          inp.closest(".gfd-campo").classList.remove("gfd-falta");
        });
      });
      raiz.querySelectorAll("[data-atalho]").forEach(function (b) {
        b.addEventListener("click", function () {
          var st = S.nums["var"]; st.v = Number(b.getAttribute("data-atalho")); st.ns = false;
          raiz.querySelector("[data-pct]").value = String(st.v);
          marcarNs("var"); marcarAtalhos();
          b.closest(".gfd-campo").classList.remove("gfd-falta");
        });
      });
      raiz.querySelectorAll("[data-prazo]").forEach(function (b) {
        b.addEventListener("click", function () {
          var st = S.nums.prazo; st.v = Number(b.getAttribute("data-prazo")); st.ns = false;
          raiz.querySelectorAll("[data-prazo]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
          marcarNs("prazo");
          b.closest(".gfd-campo").classList.remove("gfd-falta");
        });
      });
      raiz.querySelectorAll("[data-naosei]").forEach(function (b) {
        b.addEventListener("click", function () {
          var id = b.getAttribute("data-naosei"), st = S.nums[id];
          st.ns = !st.ns;
          if (st.ns) {
            st.v = null;
            var inp = raiz.querySelector('[data-dinheiro="' + id + '"], [data-pct="' + id + '"]'); if (inp) inp.value = "";
            if (id === "prazo") raiz.querySelectorAll("[data-prazo]").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
            if (id === "var") marcarAtalhos();
          }
          marcarNs(id);
          b.closest(".gfd-campo").classList.remove("gfd-falta");
        });
      });

      raiz.querySelectorAll("[data-hab]").forEach(function (b) {
        b.addEventListener("click", function () {
          var id = b.getAttribute("data-hab");
          S.hab[id] = b.getAttribute("data-v");
          raiz.querySelectorAll('[data-hab="' + id + '"]').forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
          b.closest(".gfd-campo").classList.remove("gfd-falta");
        });
      });

      raiz.querySelectorAll("[data-contato]").forEach(function (inp) {
        var k = inp.getAttribute("data-contato");
        var ev = inp.tagName === "SELECT" || inp.type === "checkbox" ? "change" : "input";
        inp.addEventListener(ev, function () { S.contato[k] = inp.type === "checkbox" ? inp.checked : inp.value; });
      });

      var rng = raiz.querySelector("#gfd-queda");
      if (rng) { rng.addEventListener("input", function () { S.queda = Number(rng.value); atualizarSimulacao(); }); atualizarSimulacao(); }
    }

    function marcarNs(id) {
      var b = raiz.querySelector('[data-naosei="' + id + '"]');
      if (b) b.setAttribute("aria-pressed", String(S.nums[id].ns));
    }
    function marcarAtalhos() {
      raiz.querySelectorAll("[data-atalho]").forEach(function (x) {
        x.setAttribute("aria-pressed", String(Number(x.getAttribute("data-atalho")) === S.nums["var"].v));
      });
    }

    render();
    return {
      reiniciar: function () { S = novoEstado(); ir("intro"); },
      estado: function () { return S; }
    };
  }

  global.GFDDiagnostico = { iniciar: iniciar, versao: "1.0.0" };
})(typeof window !== "undefined" ? window : this);
