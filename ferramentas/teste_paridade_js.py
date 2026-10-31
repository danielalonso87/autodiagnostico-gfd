"""
Confere se o diagnóstico em JavaScript (kit-landing/gfd-calculos.js) dá exatamente
o mesmo resultado que o Python (diagnostico/calculos.py).

Uso (na pasta do projeto, precisa do Node.js instalado):
    python ferramentas/teste_paridade_js.py          # 3000 casos aleatórios
    python ferramentas/teste_paridade_js.py 20000    # mais casos

Rode sempre que mudar uma fórmula, faixa ou texto de alerta em um dos dois lados.
"""

import json
import random
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from diagnostico.calculos import calcular, simular_queda  # noqa: E402
from diagnostico.perguntas import HABITOS, PRAZOS, RESPOSTAS, TIPOS  # noqa: E402

try:  # montar_linha importa streamlit; se não houver, compara só os cálculos
    from diagnostico.planilha import montar_linha  # noqa: E402
except Exception:  # pragma: no cover
    montar_linha = None

NODE = r"""
const C = require(process.argv[1]);
const casos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = casos.map(c => {
  const r = C.calcular(c.tipo, c.numeros, c.habitos);
  const sims = r.core ? [0, 0.1, 0.25, 0.5].map(q => C.simularQueda(r, q)) : null;
  const linha = C.montarLinha('id', 'teste', c.contato, c.perfil, c.numeros, c.habitos, r);
  return {r, sims, linha};
});
process.stdout.write(JSON.stringify(out));
"""

CHAVES_R = ["core", "qtd_nao_sei", "total_campos", "mc", "sobra", "pe", "ms", "fol", "div",
            "nivel_sobra", "nivel_ms", "nivel_mc", "nivel_fol", "nivel_div", "pilares", "nota"]
IGNORAR_LINHA = {"data_hora", "nome", "empresa", "whatsapp", "email"}  # tratados no servidor


def valor(rng, lo, hi, p_nao_sei=0.15, redondo=1000):
    if rng.random() < p_nao_sei:
        return None
    if rng.random() < 0.08:
        return 0
    return round(rng.uniform(lo, hi) / redondo) * redondo


def gerar(n, semente=42):
    rng = random.Random(semente)
    casos = []
    for _ in range(n):
        tipo = rng.choice(TIPOS)
        numeros = {
            "fat": valor(rng, 5_000, 500_000),
            "var": None if rng.random() < 0.15 else rng.choice(range(0, 96, 5)),
            "fix": valor(rng, 1_000, 300_000),
            "parc": valor(rng, 0, 60_000, redondo=500),
            "caixa": valor(rng, 0, 400_000),
            "prazo": None if rng.random() < 0.1 else rng.randrange(len(PRAZOS)),
            "est": valor(rng, 0, 600_000) if tipo != "Serviços" else None,
        }
        habitos = {h["id"]: rng.choice(RESPOSTAS) for h in HABITOS}
        casos.append({
            "tipo": tipo, "numeros": numeros, "habitos": habitos,
            "perfil": {"tipo": tipo, "segmento": "S", "funcionarios": "2 a 5", "tempo": "1 a 3 anos"},
            "contato": {"nome": "A", "empresa": "E", "whatsapp": "21999999999", "email": "", "preocupacao": None},
        })
    return casos


def igual(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return a is not None and b is not None and abs(a - b) <= 1e-6 * max(1, abs(a))
    return a == b


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    casos = gerar(n)
    js_path = str(RAIZ / "kit-landing" / "gfd-calculos.js")
    proc = subprocess.run(["node", "-e", NODE, js_path], input=json.dumps(casos),
                          capture_output=True, text=True, encoding="utf-8")
    if proc.returncode:
        sys.exit("Erro ao rodar o Node:\n" + proc.stderr)
    js = json.loads(proc.stdout)

    falhas = 0
    for i, (c, j) in enumerate(zip(casos, js)):
        r = calcular(c["tipo"], c["numeros"], c["habitos"])
        dif = [k for k in CHAVES_R if not igual(r[k], j["r"][k])]
        if list(r["classe"]) != j["r"]["classe"]:
            dif.append("classe")
        for k in ("alertas", "todos_alertas"):
            if [(a["titulo"], a["texto"], a["nivel"]) for a in r[k]] != \
               [(a["titulo"], a["texto"], a["nivel"]) for a in j["r"][k]]:
                dif.append(k)
        if r["core"]:
            sims = [simular_queda(r, q) for q in (0, 0.1, 0.25, 0.5)]
            for s, t in zip(sims, j["sims"]):
                if s["caixa"] != t["caixa"] or not igual(s["sobra"], t["sobra"]):
                    dif.append("simulacao")
                    break
        if montar_linha:
            lp = montar_linha("id", "teste", c["contato"], c["perfil"], c["numeros"], c["habitos"], r)
            from diagnostico.planilha import COLUNAS
            if COLUNAS != list(j["linha"].keys()) and set(COLUNAS) != set(j["linha"].keys()):
                dif.append("colunas")
            else:
                for col, v in zip(COLUNAS, lp):
                    if col not in IGNORAR_LINHA and not igual(v, j["linha"][col]):
                        dif.append(f"linha.{col}")
        if dif:
            falhas += 1
            if falhas <= 5:
                print(f"Caso {i} diferente em: {', '.join(dif)}\n  {json.dumps(c, ensure_ascii=False)}")
    if falhas:
        sys.exit(f"\n{falhas} de {n} casos com diferença entre Python e JavaScript.")
    extra = "" if montar_linha else " (sem conferir a linha da planilha: streamlit não instalado)"
    print(f"OK! {n} casos aleatórios: Python e JavaScript dão o mesmo resultado{extra}.")


if __name__ == "__main__":
    main()
