"""Dimensiona os cubos agregados candidatos, para decidir a arquitetura de consumo."""
import sys, duckdb
sys.stdout.reconfigure(encoding="utf-8")
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"""CREATE TABLE c AS SELECT CO_IES, TP_DIMENSAO, TP_MODALIDADE_ENSINO AS MOD,
   TP_GRAU_ACADEMICO AS GRAU, TP_REDE, CO_MUNICIPIO, CO_UF,
   trim(CO_CINE_ROTULO, '"') AS CINE, NO_CINE_ROTULO,
   QT_MAT, QT_ING, QT_CONC, QT_CURSO, QT_VG_TOTAL, QT_INSCRITO_TOTAL
   FROM read_csv('{CUR}', {O});""")

cubos = {
 "A. ies x modalidade":                  "SELECT CO_IES, MOD",
 "B. ies x cine x modalidade":           "SELECT CO_IES, CINE, MOD",
 "C. ies x cine x modalidade x grau":    "SELECT CO_IES, CINE, MOD, GRAU",
 "D. ies x municipio x modalidade":      "SELECT CO_IES, CO_MUNICIPIO, MOD",
 "E. cine x municipio x modalidade":     "SELECT CINE, CO_MUNICIPIO, MOD",
 "F. ies x municipio x cine x modal.":   "SELECT CO_IES, CO_MUNICIPIO, CINE, MOD",
 "G. cine x uf x modalidade":            "SELECT CINE, CO_UF, MOD",
 "H. municipio x modalidade":            "SELECT CO_MUNICIPIO, MOD",
 "I. cine x modalidade":                 "SELECT CINE, MOD",
}
print(f"{'CUBO':40s} {'LINHAS/ANO':>12s} {'x10 ANOS':>12s} {'~JSON MB':>10s}")
print("-" * 80)
for nome, sel in cubos.items():
    n = con.sql(f"SELECT count(*) FROM ({sel} FROM c WHERE TP_DIMENSAO IN (1,2,4) "
                f"AND (QT_MAT>0 OR QT_ING>0 OR QT_CONC>0) GROUP BY ALL)").fetchone()[0]
    mb = n * 45 / 1024 / 1024  # ~45 bytes/linha em JSON colunar compacto
    print(f"{nome:40s} {n:12,d} {n*10:12,d} {mb*10:9.1f}")

print("\n--- Cardinalidade das dimensoes ---")
print(con.sql("""SELECT count(DISTINCT CO_IES) ies, count(DISTINCT CINE) cursos_cine,
 count(DISTINCT CO_MUNICIPIO) municipios, count(DISTINCT CO_UF) ufs FROM c""").df().to_string(index=False))

print("\n--- Impacto de filtrar linhas 100% zeradas ---")
print(con.sql("""SELECT count(*) total,
 count(*) FILTER (WHERE QT_MAT>0 OR QT_ING>0 OR QT_CONC>0 OR QT_CURSO>0 OR QT_VG_TOTAL>0) uteis
 FROM c""").df().to_string(index=False))

print("\n--- Concentracao: quantos municipios cobrem 90% das matriculas EAD ---")
print(con.sql("""WITH m AS (SELECT CO_MUNICIPIO, sum(QT_MAT) v FROM c WHERE TP_DIMENSAO=2 GROUP BY 1),
r AS (SELECT *, sum(v) OVER (ORDER BY v DESC) / sum(v) OVER () AS acum,
      row_number() OVER (ORDER BY v DESC) rk FROM m)
SELECT min(rk) FILTER (WHERE acum>=0.90) mun_90pct, min(rk) FILTER (WHERE acum>=0.99) mun_99pct,
       count(*) total_mun FROM r""").df().to_string(index=False))
