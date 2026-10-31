# Autodiagnóstico Financeiro: Gestão Financeira Descomplicada

Topo de funil da consultoria. Em cerca de 5 minutos, o dono da empresa responde perguntas simples e recebe:
- uma nota de saúde financeira de 0 a 100;
- seus números-chave;
- os 3 riscos prioritários;
- um botão para chamar você no WhatsApp e agendar a reunião gratuita.

Cada diagnóstico vira uma linha na sua planilha do Google Sheets.

```
autodiagnostico-gfd/
├── app.py                        ← telas e navegação (Streamlit)
├── diagnostico/
│   ├── perguntas.py              ← TEXTOS: perguntas, opções, checklist (edite aqui)
│   ├── calculos.py               ← REGRAS: indicadores, nota, alertas (edite aqui)
│   ├── planilha.py               ← gravação no Google Sheets (+ CSV local de reserva)
│   ├── graficos.py               ← anel da nota, radar, régua do ponto de equilíbrio
│   └── estilo.py                 ← CSS
├── ferramentas/
│   ├── json_para_secrets.py      ← converte a chave do Google para o secrets.toml
│   └── testar_planilha.py        ← testa a conexão com a planilha
├── tests/test_calculos.py        ← testes dos cálculos
├── .streamlit/config.toml        ← cores do app
├── .streamlit/secrets.toml.example
└── requirements.txt
```

---

## 1. Rodar no seu computador (Windows)

Você precisa do Python 3.11 ou mais novo. Abra o terminal na pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O app abre em `http://localhost:8501`.

- Para ver direto um resultado de exemplo, sem preencher nada: `http://localhost:8501/?demo=1`.
- Sem a planilha configurada, os leads vão para `dados/leads_local.csv`. Dá para testar tudo antes de mexer no Google.

---

## 2. Conectar ao Google Sheets (uma vez só, cerca de 15 minutos)

O app grava na planilha usando uma **conta de serviço**, um "robô" do Google com e-mail próprio. Você compartilha a planilha com ele como faria com qualquer pessoa.

**2.1. Criar a planilha**
1. No seu Google Drive, crie uma planilha chamada, por exemplo, `Leads - Autodiagnóstico`.
2. Copie o **ID** dela, que é o trecho do link entre `/d/` e `/edit`:
   `https://docs.google.com/spreadsheets/d/`**`1AbC...xyz`**`/edit`
3. Confira em Arquivo > Configurações se a localidade está como **Brasil**, para que datas e números fiquem certos.

**2.2. Criar o projeto e a conta de serviço no Google Cloud**
1. Acesse https://console.cloud.google.com com a mesma conta Google e crie um projeto chamado, por exemplo, `autodiagnostico-gfd`.
2. Vá em **APIs e serviços > Biblioteca** e ative a **Google Sheets API** e a **Google Drive API**.
3. Vá em **IAM e administrador > Contas de serviço > Criar conta de serviço**.
   - Nome: `autodiagnostico`. Não precisa dar nenhum papel; clique em Concluir.
4. Abra a conta criada e vá em **Chaves > Adicionar chave > Criar nova chave > JSON**. Um arquivo `.json` será baixado.
   - **Guarde esse arquivo fora da pasta do projeto** e não envie para ninguém. Ele é a senha do robô.
5. Copie o e-mail da conta de serviço (algo como `autodiagnostico@autodiagnostico-gfd.iam.gserviceaccount.com`).

**2.3. Compartilhar a planilha com o robô**
- Na planilha, clique em **Compartilhar**, cole o e-mail da conta de serviço e dê permissão de **Editor**. Pode desmarcar "Notificar".

**2.4. Preencher os segredos**
1. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`.
2. Em `[app]`, coloque seu `whatsapp` (só números, com DDI e DDD). Se já tiver preenchido `WHATSAPP_PADRAO` no `app.py`, pode apagar essa seção.
3. Preencha `[planilha]` com o `id` da planilha.
4. Gere o bloco da conta de serviço e substitua o `[gcp_service_account]` de exemplo pela saída do comando:
   ```powershell
   python ferramentas\json_para_secrets.py C:\Users\daniel\Downloads\NOME-DA-CHAVE.json
   ```
5. Teste a conexão:
   ```powershell
   python ferramentas\testar_planilha.py
   ```
   Se aparecer `OK!`, a aba **Leads** foi criada com o cabeçalho. Rode o app, faça um diagnóstico de teste e veja a linha aparecer na planilha.

---

## 3. Publicar no GitHub

> ⚠️ **Nunca** envie `.streamlit/secrets.toml`, o arquivo `.json` da chave ou a pasta `dados/`. O `.gitignore` já bloqueia esses arquivos se você usar o Git ou o GitHub Desktop.

**Opção A: GitHub Desktop (recomendado)**
1. Em File > Add local repository, escolha a pasta do projeto e aceite "create a repository".
2. Confira na lista de alterações que **não** aparecem o `secrets.toml` nem o `.json`.
3. Faça o Commit e depois Publish repository. Pode ser **privado**.

**Opção B: pelo terminal**
```powershell
git init
git add .
git status          # confira que secrets.toml NÃO está na lista
git commit -m "Autodiagnóstico financeiro"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/autodiagnostico-gfd.git
git push -u origin main
```

---

## 4. Colocar no ar (Streamlit Community Cloud, gratuito)

1. Acesse https://share.streamlit.io e entre com o GitHub.
2. Clique em **Create app > Deploy a public app from GitHub** e preencha:
   - Repositório: `autodiagnostico-gfd`
   - Branch: `main`
   - Arquivo principal: `app.py`
   - App URL: escolha algo como `diagnostico-gfd`. O endereço fica `https://diagnostico-gfd.streamlit.app`.
3. Em **Advanced settings**, escolha Python 3.12 e, em **Secrets**, cole **todo** o conteúdo do seu `secrets.toml`.
4. Clique em Deploy. A partir daí, cada `push` no GitHub atualiza o app sozinho.

Para mudar os segredos depois, use o menu do app > **Settings > Secrets**.

> Observação: no plano gratuito, o app "dorme" depois de um período sem acessos. O primeiro visitante depois disso vê uma tela para acordá-lo, e o app volta em alguns segundos.

---

## 5. Botão do WhatsApp

No fim do resultado, o botão **"Agendar pelo WhatsApp"** abre uma conversa com você. A mensagem já vem pronta com o nome da empresa e a nota, por exemplo: *"Olá, Daniel! Fiz o autodiagnóstico da Auto Center (nota 38) e quero agendar a reunião gratuita."*

Para configurar, coloque seu número (só números, com 55 e DDD) em `WHATSAPP_PADRAO`, no início do `app.py`:
```python
WHATSAPP_PADRAO = "5521999999999"
```
O número não é segredo, então pode ir para o GitHub normalmente.

Quando a mensagem chegar, procure o nome na planilha. Você vai ter todas as respostas antes de responder.

---

## 6. Ligar à landing page

**Botão ou link** (mais simples e mais confiável):
```html
<a href="https://diagnostico-gfd.streamlit.app/?origem=site">Fazer meu diagnóstico gratuito</a>
```

**Incorporado na página** (iframe):
```html
<iframe src="https://diagnostico-gfd.streamlit.app/?embed=true&origem=site"
        style="width:100%; height:1100px; border:0;"></iframe>
```

**Saber de onde vem cada lead:** troque o `origem=` em cada canal. A coluna `origem` da planilha registra o valor.

| Canal | Link |
|---|---|
| Site | `...streamlit.app/?origem=site` |
| YouTube (descrição) | `...streamlit.app/?origem=youtube` |
| Instagram (bio) | `...streamlit.app/?origem=instagram` |
| LinkedIn | `...streamlit.app/?origem=linkedin` |
| Google Ads | `...streamlit.app/?origem=google-ads` |

`utm_source` também é aceito, caso a agência use UTMs.

---

## 7. A planilha no dia a dia

Cada diagnóstico concluído grava uma linha com:
- contato e consentimento LGPD;
- perfil da empresa;
- números informados ("não sei" quando a pessoa não soube);
- respostas da rotina;
- nota e notas por área;
- indicadores e os 3 alertas.

Dicas:
- A coluna **status** nasce como `Novo`. Use-a como um mini-CRM: `Novo > Contatado > Reunião marcada > Cliente / Perdido`. Para facilitar, crie uma lista suspensa em Dados > Validação de dados.
- Se a pessoa voltar e refizer o diagnóstico, entra uma linha nova com o mesmo `id_sessao`.
- Antes da reunião, abra a linha do lead. Você já chega sabendo os números, os alertas e a maior preocupação dele.
- Se a gravação no Sheets falhar (internet, permissão), o cliente vê o resultado normalmente e o app tenta salvar em `dados/leads_local.csv`. No Streamlit Cloud esse arquivo não é permanente, então o Sheets precisa estar funcionando.

---

## 8. Personalizar

| Quero mudar... | Arquivo |
|---|---|
| Texto de perguntas, opções, checklist da reunião | `diagnostico/perguntas.py` |
| Faixas de semáforo, pesos da nota, textos dos alertas | `diagnostico/calculos.py` |
| Textos das telas, botões, CTA | `app.py` |
| Cores | `.streamlit/config.toml` e `diagnostico/estilo.py` |

Depois de mexer nos cálculos, rode os testes:
```powershell
pip install pytest
python -m pytest
```

### Como a nota é calculada
A nota é a média de 5 áreas, de 0 a 100 cada:

| Área | Composição |
|---|---|
| **Controle** | 70% hábitos (conta separada, registro, sabe o lucro) + 30% quantos números a pessoa soube responder |
| **Caixa** | 60% hábitos (pró-labore fixo, previsão, não faltou dinheiro) + 40% fôlego de caixa |
| **Margem e preço** | 60% hábitos (preço por custo, sabe a margem) + 40% margem de segurança |
| **Dívidas** | 50% uso de crédito caro + 50% parcelas ÷ faturamento |
| **Planejamento** | previsão de caixa + meta e orçamento |

Faixas: abaixo de 40, Crítica; de 40 a 59, Atenção; de 60 a 79, Estável; 80 ou mais, Saudável.

Indicador sem dado conta como 25%, porque não saber já é um problema.

---

## 9. Kit para a landing page (agência)

A pasta `kit-landing/` tem o mesmo diagnóstico em HTML/JavaScript, para a agência embutir direto na landing page, sem iframe. Os leads vão para a **mesma aba Leads**, com as mesmas colunas.

O guia da agência é o `kit-landing/LEIAME-AGENCIA.md`. A sua parte é só esta:

**9.1. Instalar o receptor de leads (Google Apps Script)**
1. Abra a sua planilha de leads e vá em **Extensões > Apps Script**.
2. Apague o código que estiver lá e cole todo o conteúdo de `kit-landing/apps-script/Codigo.gs`. Salve.
3. No topo, escolha a função **testar** e clique em **Executar**. O Google vai pedir autorização: clique em "Avançado > Acessar (não seguro)". É normal, porque o script é seu.
4. Vá em **Implantar > Nova implantação**, clique na engrenagem e escolha **App da Web**:
   - **Executar como:** Eu
   - **Quem pode acessar:** Qualquer pessoa
5. Clique em **Implantar** e copie a **URL do app da Web**, que termina em `/exec`. Mande essa URL para a agência.

Para conferir, abra a URL no navegador. Deve aparecer `{"ok":true,...}`.

**9.2. Mandar para a agência**
- O link do repositório no GitHub, ou a pasta `kit-landing` zipada;
- a URL `/exec` do passo anterior.

**9.3. Se mudar uma pergunta, faixa ou alerta**
Mude nos dois lados: `diagnostico/*.py` e `kit-landing/gfd-calculos.js`. Depois rode o teste (precisa do Node.js instalado):
```powershell
python ferramentas\teste_paridade_js.py
```
Ele compara 3.000 diagnósticos aleatórios e avisa se o Python e o JavaScript divergirem.
