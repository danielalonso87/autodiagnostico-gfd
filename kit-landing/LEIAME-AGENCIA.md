# Kit do Autodiagnóstico para a landing page

Este kit coloca o **Autodiagnóstico Financeiro** da Gestão Financeira Descomplicada dentro da landing page, sem iframe e sem depender do Streamlit. Os leads continuam indo para a mesma planilha do Google Sheets do Daniel.

Para ver funcionando antes de mexer em qualquer coisa, abra o `exemplo.html` no navegador.

## Arquivos

| Arquivo | O que é | Pode editar? |
|---|---|---|
| `gfd-diagnostico.css` | Visual do widget. Tudo fica dentro de `.gfd`, sem vazar para a landing | **Sim**, principalmente as variáveis do topo |
| `gfd-diagnostico.js` | Telas, navegação, envio do lead e eventos de conversão | Com cuidado (veja as regras) |
| `gfd-calculos.js` | Fórmulas, faixas, nota, alertas e textos das perguntas | **Não**, sem falar com o Daniel |
| `exemplo.html` | Página de exemplo com o widget instalado | Referência |
| `apps-script/Codigo.gs` | Recebe os leads e grava na planilha. **Fica com o Daniel** | Não |

Não há dependências externas: é JavaScript puro, sem jQuery nem frameworks.

---

## Instalação em 3 passos

**1. Hospede os arquivos** `gfd-diagnostico.css`, `gfd-calculos.js` e `gfd-diagnostico.js` junto da landing, no mesmo servidor, CDN ou na biblioteca de mídia/tema do construtor de páginas.

**2. Coloque o contêiner** onde o diagnóstico deve aparecer:
```html
<div id="gfd-diagnostico"></div>
```

**3. Carregue e inicie**, de preferência no fim do `<body>`:
```html
<link rel="stylesheet" href="/caminho/gfd-diagnostico.css">
<script src="/caminho/gfd-calculos.js"></script>
<script src="/caminho/gfd-diagnostico.js"></script>
<script>
  GFDDiagnostico.iniciar("#gfd-diagnostico", {
    endpoint: "URL_DO_APPS_SCRIPT",   // o Daniel envia (termina em /exec)
    whatsapp: "5521986721336",
    origemPadrao: "site"
  });
</script>
```

> **WordPress, Elementor e similares:** use um bloco de "HTML personalizado" para o `div` e os `<script>`. O CSS pode ir no mesmo bloco, com a tag `<link>`, ou no CSS adicional do tema.

### Opções de `iniciar`

| Opção | Padrão | Para quê |
|---|---|---|
| `endpoint` | `""` | URL do Apps Script que grava o lead. **Sem ela, nada é gravado**: aparece um aviso no console |
| `whatsapp` | `""` | Número do botão final (55 + DDD + número) |
| `nomeConsultor` | `"Daniel"` | Nome na mensagem pronta do WhatsApp |
| `origemPadrao` | `"site"` | Valor da coluna `origem` quando a URL não tem `?origem=` nem `?utm_source=` |
| `rolarAoTrocar` | `true` | Rola até o topo do widget a cada etapa |
| `aoEvento` | — | `function(nome, dados)`, chamada em cada evento (abaixo) |
| `aoConcluir` | — | `function(resultado, linha)`, chamada quando o lead vê o resultado |

---

## Visual

Para seguir a identidade da landing, troque as variáveis CSS. Não é preciso editar o resto do CSS:

```css
#gfd-diagnostico {
  --gfd-destaque: #0b5cad;          /* cor principal: botões, barra de progresso, CTA */
  --gfd-destaque-suave: #e3eefa;
  --gfd-fonte: "Montserrat", sans-serif;
  --gfd-fonte-titulo: "Montserrat", sans-serif;
  --gfd-superficie: #ffffff;        /* fundo dos cartões */
  --gfd-raio: 16px;                 /* arredondamento */
  --gfd-largura: 900px;
}
```

Por padrão, a fonte é herdada da landing (`inherit`). As cores de **bom, atenção e ruim** (verde, laranja, vermelho) têm significado no diagnóstico, então mantenha a lógica se for trocá-las.

---

## Conversões (Google Ads / GA4 / GTM)

O widget envia eventos para o `window.dataLayer`, ou seja, funciona direto com o Google Tag Manager:

| Evento | Quando | Dados |
|---|---|---|
| `gfd_inicio` | Clicou em "Começar diagnóstico" | `gfd_origem` |
| `gfd_etapa` | Concluiu uma etapa | `gfd_etapa` (`perfil`, `numeros`, `habitos`, `contato`) |
| **`gfd_concluido`** | **Enviou o contato e viu o resultado (lead gerado)** | `gfd_nota`, `gfd_classificacao`, `gfd_segmento` |
| `gfd_whatsapp` | Clicou em "Agendar pelo WhatsApp" | `gfd_nota` |

- **Conversão principal sugerida:** `gfd_concluido`.
- **Conversão secundária:** `gfd_whatsapp`.
- Com `gfd_etapa`, dá para montar o funil e ver onde as pessoas desistem.

Sem GTM, dá para disparar a tag direto:
```js
GFDDiagnostico.iniciar("#gfd-diagnostico", {
  endpoint: "...", whatsapp: "...",
  aoConcluir: function () { gtag("event", "conversion", { send_to: "AW-XXXXXXX/YYYYYYY" }); }
});
```

### Origem do lead
A coluna `origem` da planilha vem de `?origem=` ou `?utm_source=` na URL da landing. Exemplo de URL final do anúncio: `https://site.com.br/diagnostico?utm_source=google-ads&utm_campaign=...`.

---

## Regras importantes

1. **Não altere `gfd-calculos.js`** (fórmulas, faixas, pesos, textos dos alertas e das perguntas). Ele é uma cópia fiel do sistema do Daniel em Python, e existe um teste automático que confere que os dois dão o mesmo resultado. Se precisar mudar algum texto ou pergunta, fale com o Daniel para ele mudar nos dois lados.
2. **Pode mudar à vontade em `gfd-diagnostico.js`** os textos de interface: títulos das telas, textos de botão, CTA. Os nomes das colunas e o formato do envio devem ficar iguais.
3. **Não remova** o checkbox de autorização (LGPD) nem o campo invisível `gfd-mel`, que é uma armadilha anti-robô.
4. O lead é gravado **no clique em "Ver meu diagnóstico"**, antes de mostrar o resultado.

---

## Como testar

1. Com o `endpoint` configurado, faça um diagnóstico completo na landing, usando um nome como "TESTE AGÊNCIA".
2. Peça ao Daniel para confirmar que a linha apareceu na aba **Leads**.
3. No GTM, use o modo de visualização (Preview) para confirmar o `gfd_concluido`.
4. Teste no celular. O widget é responsivo até cerca de 360px de largura.

Dúvidas sobre o diagnóstico: Daniel Alonso.
