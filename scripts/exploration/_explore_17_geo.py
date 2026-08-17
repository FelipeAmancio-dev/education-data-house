"""Teste de viabilidade de geolocalizacao: centroides IBGE e fontes de campus/polo."""
import sys, json, requests
sys.stdout.reconfigure(encoding="utf-8")

def testa(nome, url, timeout=25):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        print(f"  [{r.status_code}] {nome}  ({len(r.content):,} bytes)  {r.headers.get('Content-Type','')[:40]}")
        return r
    except Exception as e:
        print(f"  [ERRO] {nome}: {type(e).__name__} {str(e)[:90]}")
        return None

print("=== 1. IBGE: centroides de municipio (rota garantida) ===")
r = testa("IBGE localidades/municipios", "https://servicodados.ibge.gov.br/api/v1/localidades/municipios")
if r and r.ok:
    d = r.json()
    print(f"  -> {len(d):,} municipios. Exemplo: {d[0]['nome']} / {d[0]['microrregiao']['mesorregiao']['UF']['sigla']}")
    print(f"  -> campos disponiveis: {list(d[0].keys())}  (NAO traz lat/lon)")

r = testa("IBGE malha UF (GeoJSON)",
          "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=UF")
if r and r.ok:
    try:
        g = r.json()
        print(f"  -> GeoJSON com {len(g.get('features', []))} features (UFs)")
    except Exception as e:
        print(f"  -> resposta nao-JSON: {e}")

r = testa("IBGE malha municipio de 1 UF (ES)",
          "https://servicodados.ibge.gov.br/api/v3/malhas/estados/32?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=municipio")
if r and r.ok:
    try:
        g = r.json()
        print(f"  -> GeoJSON com {len(g.get('features', []))} municipios do ES")
    except Exception as e:
        print(f"  -> {e}")

print("\n=== 2. Fontes de centroide com lat/lon prontos ===")
testa("IBGE FTP/gov - localidades v1 (com coordenadas?)",
      "https://servicodados.ibge.gov.br/api/v1/localidades/municipios/3205309")
r = testa("Nominatim (geocoder aberto, 1 req/s)",
          "https://nominatim.openstreetmap.org/search?q=Vitoria+ES+Brasil&format=json&limit=1")
if r and r.ok:
    try:
        d = r.json()
        if d:
            print(f"  -> geocodificou: lat={d[0]['lat']} lon={d[0]['lon']}")
    except Exception as e:
        print(f"  -> {e}")

print("\n=== 3. e-MEC: cadastro de IES, locais de oferta e polos EAD ===")
testa("e-MEC home", "https://emec.mec.gov.br/")
testa("Portal dados abertos MEC", "https://dadosabertos.mec.gov.br/")
