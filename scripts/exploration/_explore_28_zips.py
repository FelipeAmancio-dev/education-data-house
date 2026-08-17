"""Inspeciona a estrutura interna de todos os zips historicos SEM extrair."""
import sys, zipfile, os, re
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\education\data_raw"

for ano in range(2015, 2025):
    z = os.path.join(ROOT, str(ano), f"microdados_censo_da_educacao_superior_{ano}.zip")
    if not os.path.exists(z):
        print(f"{ano}: ZIP NAO ENCONTRADO")
        continue
    print("=" * 110)
    print(f"### {ano}   zip={os.path.getsize(z)/1024/1024:,.1f} MB")
    print("=" * 110)
    with zipfile.ZipFile(z) as zf:
        infos = zf.infolist()
        # so arquivos de dados (csv) e o resto resumido
        csvs = [i for i in infos if i.filename.upper().endswith(".CSV")]
        outros = [i for i in infos if not i.filename.upper().endswith(".CSV") and not i.is_dir()]
        for i in sorted(csvs, key=lambda x: -x.file_size):
            ratio = (i.compress_size / i.file_size * 100) if i.file_size else 0
            print(f"  CSV  {i.file_size/1024/1024:9,.1f} MB desc | {i.compress_size/1024/1024:8,.1f} MB comp "
                  f"({ratio:4.1f}%)  {i.filename}")
        for i in sorted(outros, key=lambda x: -x.file_size)[:6]:
            print(f"  ---  {i.file_size/1024/1024:9,.1f} MB       | {i.filename}")
        if len(outros) > 6:
            print(f"  ... mais {len(outros)-6} arquivos nao-CSV")
        tot = sum(i.file_size for i in csvs)
        print(f"  >>> TOTAL CSV DESCOMPACTADO: {tot/1024/1024:,.1f} MB")
    print()
