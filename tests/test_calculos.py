from diagnostico.calculos import brl, calcular, pct, simular_queda

HAB_EXEMPLO = {"h1": "Às vezes", "h2": "Sim", "h3": "Não", "h4": "Não", "h5": "Não",
               "h6": "Às vezes", "h7": "Às vezes", "h8": "Não", "h9": "Às vezes", "h10": "Não"}
NUM_EXEMPLO = {"fat": 80000, "var": 45, "fix": 35000, "parc": 5000, "caixa": 20000, "prazo": 1, "est": None}


def test_formatacao():
    assert brl(72727.27) == "R$ 72.727"
    assert brl(-4000) == "− R$ 4.000"
    assert pct(0.0909) == "9%"
    assert pct(0.05, 1) == "5,0%"


def test_exemplo_oficina():
    r = calcular("Os dois", NUM_EXEMPLO, HAB_EXEMPLO)
    assert r["core"]
    assert round(r["mc"]) == 44000
    assert round(r["sobra"]) == 4000
    assert round(r["pe"]) == 72727
    assert round(r["ms"], 4) == 0.0909
    assert round(r["fol"]) == 15
    assert r["nivel_fol"] == "bad"
    assert r["nivel_ms"] == "warn"
    assert r["qtd_nao_sei"] == 1 and r["total_campos"] == 7
    assert 0 <= r["nota"] <= 100
    assert len(r["alertas"]) == 3
    assert r["alertas"][0]["titulo"].startswith("O caixa paga só 15 dias")


def test_servico_nao_pergunta_estoque():
    r = calcular("Serviços", {**NUM_EXEMPLO, "est": 999999}, HAB_EXEMPLO)
    assert r["total_campos"] == 6
    assert r["est"] is None


def test_tudo_nao_sei():
    nums = {k: None for k in NUM_EXEMPLO}
    hab = {f"h{i}": "Não" for i in range(1, 11)}
    r = calcular("Produtos", nums, hab)
    assert not r["core"]
    assert r["fol"] is None and r["div"] is None
    assert r["classe"][0] == "Crítica"
    assert any("não soube 7" in a["titulo"] for a in r["alertas"])


def test_empresa_saudavel():
    nums = {"fat": 100000, "var": 30, "fix": 30000, "parc": 0, "caixa": 200000, "prazo": 0, "est": 10000}
    hab = {f"h{i}": "Sim" for i in range(1, 11)} | {"h6": "Não", "h9": "Não"}
    r = calcular("Produtos", nums, hab)
    assert r["nota"] >= 80 and r["classe"][0] == "Saudável"
    assert r["alertas"] == []


def test_prejuizo():
    nums = {**NUM_EXEMPLO, "fat": 50000}
    r = calcular("Os dois", nums, HAB_EXEMPLO)
    assert r["ms"] < 0
    assert r["alertas"][0]["titulo"] == "A empresa está vendendo menos do que custa"


def test_simulacao():
    r = calcular("Os dois", NUM_EXEMPLO, HAB_EXEMPLO)
    s = simular_queda(r, 0.10)
    assert round(s["faturamento"]) == 72000
    assert round(s["sobra"]) == -400
    assert s["caixa"] == "Zera em 1500 dias" or s["caixa"] == "Zera em mais de 2 anos"
    assert simular_queda(r, 0)["caixa"] == "Não diminui"
