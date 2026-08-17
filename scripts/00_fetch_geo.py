"""
Baixa a base geografica do IBGE e calcula centroides de municipio.

Roda UMA VEZ. Depois disso o projeto e 100% offline.

Gera:
  config/municipios_ibge.csv   5.570 municipios com CO_MUNICIPIO (IBGE 7), nome, UF, regiao, lat, lon
  config/geo/uf.geojson        malha das 27 UFs (para coropletico)
  config/geo/municipios/<UF>.geojson   malha municipal por UF (opcional, --malhas-municipais)

O IBGE nao publica latitude/longitude na API de localidades; as coordenadas sao calculadas
aqui a partir da malha (centroide de poligono pela formula do shoelace, anel de maior area).

Uso:
  python scripts/00_fetch_geo.py
  python scripts/00_fetch_geo.py --malhas-municipais     # guarda tambem os poligonos municipais
"""
import argparse
import json
import os
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "config", "municipios_ibge.csv")
GEO_DIR = os.path.join(ROOT, "config", "geo")

API = "https://servicodados.ibge.gov.br/api/v1/localidades"
MALHA = "https://servicodados.ibge.gov.br/api/v3/malhas"
FMT = "formato=application/vnd.geo+json"
UA = {"User-Agent": "dashboard-ensino-superior/1.0"}


def get(url, tentativas=3):
    for i in range(tentativas):
        try:
            r = requests.get(url, timeout=90, headers=UA)
            r.raise_for_status()
            return r
        except Exception as e:
            if i == tentativas - 1:
                raise
            print(f"    retry {i+1}/{tentativas-1}: {type(e).__name__}")
            time.sleep(3 * (i + 1))


def anel_centroide(anel):
    """Centroide de um anel poligonal (shoelace). Retorna (lon, lat, area_abs)."""
    a = cx = cy = 0.0
    n = len(anel)
    for i in range(n - 1):
        x0, y0 = anel[i][0], anel[i][1]
        x1, y1 = anel[i + 1][0], anel[i + 1][1]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if a == 0:
        xs = [p[0] for p in anel]
        ys = [p[1] for p in anel]
        return sum(xs) / len(xs), sum(ys) / len(ys), 0.0
    a *= 0.5
    return cx / (6 * a), cy / (6 * a), abs(a)


def centroide(geom):
    """Centroide do maior anel externo de um Polygon/MultiPolygon."""
    t = geom.get("type")
    coords = geom.get("coordinates", [])
    poligonos = [coords] if t == "Polygon" else (coords if t == "MultiPolygon" else [])
    melhor, maior = None, -1.0
    for p in poligonos:
        if not p:
            continue
        lon, lat, area = anel_centroide(p[0])
        if area > maior:
            melhor, maior = (lon, lat), area
    return melhor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--malhas-municipais", action="store_true",
                    help="salva tambem os poligonos municipais por UF (~6 MB)")
    args = ap.parse_args()

    os.makedirs(GEO_DIR, exist_ok=True)

    print("1/4  Lista de municipios (IBGE localidades)...")
    muns = get(f"{API}/municipios").json()
    meta = {}
    for m in muns:
        micro = m.get("microrregiao") or {}
        meso = micro.get("mesorregiao") or {}
        uf = meso.get("UF") or {}
        reg = uf.get("regiao") or {}
        if not uf:  # fallback p/ municipios sem hierarquia classica
            imed = (m.get("regiao-imediata") or {}).get("regiao-intermediaria") or {}
            uf = imed.get("UF") or {}
            reg = uf.get("regiao") or {}
        meta[m["id"]] = {
            "nome": m["nome"], "uf": uf.get("sigla", ""), "uf_nome": uf.get("nome", ""),
            "co_uf": uf.get("id", ""), "regiao": reg.get("nome", ""),
            "meso": meso.get("nome", ""), "micro": micro.get("nome", ""),
        }
    print(f"     {len(meta):,} municipios")

    print("2/4  Malha das UFs (coropletico)...")
    uf_geo = get(f"{MALHA}/paises/BR?{FMT}&qualidade=intermediaria&intrarregiao=UF").json()
    with open(os.path.join(GEO_DIR, "uf.geojson"), "w", encoding="utf-8") as f:
        json.dump(uf_geo, f, ensure_ascii=False, separators=(",", ":"))
    print(f"     {len(uf_geo.get('features', []))} UFs -> config/geo/uf.geojson")

    print("3/4  Malhas municipais por UF (para calcular centroides)...")
    ufs = get(f"{API}/estados").json()
    ufs.sort(key=lambda u: u["sigla"])
    if args.malhas_municipais:
        os.makedirs(os.path.join(GEO_DIR, "municipios"), exist_ok=True)

    coords, faltando = {}, []
    for i, uf in enumerate(ufs, 1):
        g = get(f"{MALHA}/estados/{uf['id']}?{FMT}&qualidade=intermediaria&intrarregiao=municipio").json()
        feats = g.get("features", [])
        ok = 0
        for ft in feats:
            cod = ft.get("properties", {}).get("codarea")
            if not cod:
                continue
            c = centroide(ft.get("geometry") or {})
            if c:
                coords[int(cod)] = c
                ok += 1
        if args.malhas_municipais:
            with open(os.path.join(GEO_DIR, "municipios", f"{uf['sigla']}.geojson"), "w",
                      encoding="utf-8") as f:
                json.dump(g, f, ensure_ascii=False, separators=(",", ":"))
        print(f"     {i:2d}/27  {uf['sigla']}  {ok:>5} municipios")
        time.sleep(0.3)

    print("4/4  Gravando CSV...")
    linhas = ["CO_MUNICIPIO;NO_MUNICIPIO;SG_UF;NO_UF;CO_UF;NO_REGIAO;NO_MESORREGIAO;NO_MICRORREGIAO;LATITUDE;LONGITUDE"]
    for cod, m in sorted(meta.items()):
        c = coords.get(cod)
        if not c:
            faltando.append((cod, m["nome"], m["uf"]))
        lon, lat = (c if c else ("", ""))
        lat_s = f"{lat:.6f}" if c else ""
        lon_s = f"{lon:.6f}" if c else ""
        linhas.append(f"{cod};{m['nome']};{m['uf']};{m['uf_nome']};{m['co_uf']};{m['regiao']};"
                      f"{m['meso']};{m['micro']};{lat_s};{lon_s}")
    with open(OUT_CSV, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(linhas))

    print(f"\nEscrito: {OUT_CSV}")
    print(f"  {len(meta):,} municipios · {len(coords):,} com coordenada "
          f"({100*len(coords)/len(meta):.1f}%)")
    if faltando:
        print(f"  {len(faltando)} sem coordenada: {faltando[:5]}")
    print(f"Escrito: {os.path.join(GEO_DIR, 'uf.geojson')}")
    if args.malhas_municipais:
        print(f"Escrito: {os.path.join(GEO_DIR, 'municipios')}/<UF>.geojson")


if __name__ == "__main__":
    main()
