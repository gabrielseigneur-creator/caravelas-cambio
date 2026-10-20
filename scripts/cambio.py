#!/usr/bin/env python3
"""Busca PTAX (BCB, USD/BRL) e taxa de referência do BCE (EUR/USD) do último dia útil
e grava dados/cambio-AAAA-MM-DD.json e dados/latest.json. Sem credenciais: APIs públicas.

Uso: python scripts/cambio.py            (busca online)
     python scripts/cambio.py --fixture tests/  (testa com respostas salvas)
"""
import csv, io, json, sys, urllib.request
from datetime import date, timedelta, datetime, timezone

BCB = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
       "CotacaoDolarPeriodo(dataInicial=@i,dataFinalCotacao=@f)?@i='{i}'&@f='{f}'&$format=json&$orderby=dataHoraCotacao%20desc&$top=1")
ECB = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=1&format=csvdata"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "caravelas-cambio/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def ptax(texto):
    v = json.loads(texto)["value"]
    if not v:
        raise ValueError("BCB sem cotação no período")
    x = v[0]
    return {"par": "USD/BRL", "fonte": "BCB PTAX (venda)", "taxa": x["cotacaoVenda"],
            "compra": x["cotacaoCompra"], "data": x["dataHoraCotacao"][:10]}


def bce(texto):
    rows = list(csv.DictReader(io.StringIO(texto)))
    if not rows:
        raise ValueError("BCE sem observação")
    r = rows[-1]
    return {"par": "EUR/USD", "fonte": "BCE taxa de referência", "taxa": float(r["OBS_VALUE"]),
            "data": r["TIME_PERIOD"]}


def main():
    hoje = date.today()
    fixture = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--fixture" else None
    out = {"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "taxas": [], "erros": []}
    fontes = [("bcb", ptax, BCB.format(i=(hoje - timedelta(days=7)).strftime("%m-%d-%Y"), f=hoje.strftime("%m-%d-%Y"))),
              ("ecb", bce, ECB)]
    for nome, parse, url in fontes:
        try:
            texto = open(f"{fixture}/{nome}.txt").read() if fixture else get(url)
            out["taxas"].append(parse(texto))
        except Exception as e:  # registra e segue: falha de uma fonte não derruba a outra
            out["erros"].append(f"{nome}: {type(e).__name__}: {e}")
    t = {x["par"]: x for x in out["taxas"]}
    if "USD/BRL" in t and "EUR/USD" in t:
        out["derivadas"] = [{"par": "EUR/BRL", "taxa": round(t["USD/BRL"]["taxa"] * t["EUR/USD"]["taxa"], 6),
                             "nota": "PTAX venda × BCE; datas podem diferir"}]
    out["status"] = "ok" if not out["erros"] else ("degradado" if out["taxas"] else "falhou")
    if fixture:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if out["status"] == "ok" else 1
    nome = f"dados/cambio-{hoje.isoformat()}.json"
    for p in (nome, "dados/latest.json"):
        json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    print(out["status"], out["erros"])
    return 0 if out["status"] != "falhou" else 1


if __name__ == "__main__":
    sys.exit(main())
