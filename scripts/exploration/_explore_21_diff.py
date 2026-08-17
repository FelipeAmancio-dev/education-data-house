"""Verifica o que mudou com o novo Suporte multi-aba e checa as pendencias antigas."""
import sys, os, pandas as pd
sys.path.insert(0, r"C:\education\scripts")
from lib.suporte import ler_suporte, ler_csv_comentado, norm
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)

CFG = r"C:\education\config"
abas = ler_csv_comentado(os.path.join(CFG, "suporte_abas.csv"))
mapa_abas = {norm(r.ABA): str(r.GRUPO).strip() for r in abas.itertuples()}
sup, _ = ler_suporte(r"C:\education\Suporte IES.xlsx", mapa_abas)
mp = pd.read_csv(os.path.join(CFG, "ies_grupo_map.csv"), sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna("")

print("=== 1. PENDENCIAS ANTIGAS: foram resolvidas? ===")
for co, nome in [(1978, "Centro Univ. Fametro (CE)"), (19337, "Fac. Unifametro Maracanau"),
                 (19859, "Fac. Unifametro Cascavel"), (1131, "Centro Univ. Santo Agostinho (UniFSA)"),
                 (3839, "Faculdade IPEMED"), (15450, "Centro Univ. Unica")]:
    r = mp[mp["CO_IES"] == co]
    if len(r):
        g = r["GRUPO"].iloc[0] or "(sem grupo)"
        print(f"  {co:>6}  {nome:<40} -> {g:<20} [{r['ORIGEM_GRUPO'].iloc[0] or '-'}]  "
              f"{r['QT_MAT_TOTAL'].iloc[0]:,.0f} alunos")

print("\n=== 2. ORFAOS: codigos do Suporte ausentes do Censo 2024 ===")
orf = pd.read_csv(os.path.join(CFG, "ies_grupo_map_nao_encontradas.csv"), sep=";", encoding="utf-8-sig")
print(f"total: {len(orf)}")
print(orf.groupby("GRUPO").size().to_string())
print("\ndetalhe:")
print(orf[["CO_IES", "GRUPO", "NO_IES_SUPORTE"]].sort_values(["GRUPO", "CO_IES"]).to_string(index=False))

print("\n=== 3. IES do Suporte que ESTAO no Censo mas com ZERO matriculas ===")
z = mp[(mp["GRUPO"] != "") & (mp["QT_MAT_TOTAL"] == 0) & (mp["ORIGEM_GRUPO"] == "suporte_xlsx")]
print(f"total: {len(z)}")
if len(z):
    print(z[["CO_IES", "NO_IES", "GRUPO", "SG_UF_IES", "QT_CURSOS"]].to_string(index=False))

print("\n=== 4. IES capturadas por regra (nao estao no seu Excel) ===")
d = mp[(mp["GRUPO"] != "") & (mp["ORIGEM_GRUPO"] == "mantenedora_derivada")]
print(d[["CO_IES", "NO_IES", "GRUPO", "NO_MANTENEDORA", "QT_MAT_TOTAL"]]
      .sort_values("QT_MAT_TOTAL", ascending=False).to_string(index=False))

print("\n=== 5. GRUPO_CONSOLIDADO: efeito da fusao FMU -> Anima quando ativada ===")
a = mp[mp["GRUPO"] == "Ânima"]["QT_MAT_TOTAL"].sum()
f = mp[mp["GRUPO"] == "FMU"]["QT_MAT_TOTAL"].sum()
tot = mp["QT_MAT_TOTAL"].sum()
print(f"  Anima standalone : {a:,.0f}  ({100*a/tot:.2f}%)")
print(f"  FMU standalone   : {f:,.0f}  ({100*f/tot:.2f}%)")
print(f"  Anima + FMU      : {a+f:,.0f}  ({100*(a+f)/tot:.2f}%)  -> subiria para o 6o lugar")
print(f"  ranking hoje: Ser Educacional = {mp[mp['GRUPO']=='Ser Educacional']['QT_MAT_TOTAL'].sum():,.0f}")
