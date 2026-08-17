"""
Sobe o dashboard num servidor local e abre o navegador.

E preciso servidor porque `fetch()` de arquivos locais e bloqueado ao abrir o HTML
por file:// . De brinde, ganhamos gzip e cache — e o mesmo diretorio fica pronto
para publicacao em qualquer host estatico.

Uso:
  python run_dashboard.py                 # porta 8000, abre o navegador
  python run_dashboard.py --porta 8080
  python run_dashboard.py --sem-navegador
"""
import argparse
import functools
import gzip
import http.server
import io
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(ROOT, "dashboard")

COMPRIMIVEIS = (".json", ".js", ".css", ".html", ".geojson", ".svg")


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serve o dashboard com gzip nos arquivos de texto e sem cache agressivo."""

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    # ---------------------------------------------------------------- API local
    # Só existe quando o dashboard roda pelo servidor local. O bloco de Price Action
    # sonda `status` e só mostra o botão de atualizar se houver resposta — no arquivo
    # único e no artifact publicado o endpoint não existe e o botão nem aparece.
    def _json(self, codigo, obj):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _rota_api(self):
        return self.path.split("?")[0].rstrip("/")

    def do_POST(self):
        if self._rota_api() != "/api/precos/atualizar":
            self.send_error(404)
            return
        script = os.path.join(ROOT, "scripts", "06_fetch_precos.py")
        try:
            r = subprocess.run([sys.executable, script, "--quieto"],
                               capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self._json(504, {"ok": False, "erro": "coleta demorou mais de 180s"})
            return
        if r.returncode != 0:
            self._json(502, {"ok": False, "erro": (r.stderr or r.stdout or "falha").strip()[-400:]})
            return
        self._json(200, {"ok": True})

    def do_GET(self):
        if self._rota_api() == "/api/precos/status":
            arq = os.path.join(WEB, "data", "precos.json")
            self._json(200, {"ok": True, "existe": os.path.exists(arq)})
            return
        caminho = self.translate_path(self.path)
        if (os.path.isfile(caminho) and caminho.lower().endswith(COMPRIMIVEIS)
                and "gzip" in self.headers.get("Accept-Encoding", "")):
            with open(caminho, "rb") as f:
                bruto = f.read()
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz:
                gz.write(bruto)
            dados = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(caminho))
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        if "404" in str(args) or "500" in str(args):
            sys.stderr.write(f"  [{self.address_string()}] {fmt % args}\n")


def atualiza_precos_em_loop(intervalo):
    """Recoleta os precos em segundo plano enquanto o servidor estiver de pe.

    O dashboard reconsulta `data/precos.json` no mesmo ritmo e so redesenha quando o
    carimbo muda. Falha de rede nao derruba nada: mantem o snapshot anterior.
    """
    script = os.path.join(ROOT, "scripts", "06_fetch_precos.py")
    while True:
        time.sleep(intervalo)
        try:
            r = subprocess.run([sys.executable, script, "--quieto"],
                               capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                sys.stderr.write("  [precos] falha na coleta\n")
        except Exception as e:                        # noqa: BLE001
            sys.stderr.write(f"  [precos] {type(e).__name__}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--porta", type=int, default=8000)
    ap.add_argument("--sem-navegador", action="store_true")
    ap.add_argument("--sem-precos", action="store_true",
                    help="não recoleta preços em segundo plano")
    ap.add_argument("--intervalo", type=int, default=300,
                    help="segundos entre coletas de preço (padrão 300 = 5 min)")
    args = ap.parse_args()

    dados = os.path.join(WEB, "data", "meta.json")
    if not os.path.exists(dados):
        print("Os dados do dashboard não foram gerados ainda.\n")
        print("Rode, nesta ordem:")
        print("  python scripts/01_ingest.py")
        print("  python scripts/02_build_cubes.py")
        print("  python scripts/04_export_web.py")
        sys.exit(1)

    socketserver.TCPServer.allow_reuse_address = True
    h = functools.partial(Handler, directory=WEB)
    porta = args.porta
    for tentativa in range(12):
        try:
            servidor = socketserver.TCPServer(("127.0.0.1", porta), h)
            break
        except OSError:
            porta += 1
    else:
        print(f"Nenhuma porta livre entre {args.porta} e {porta}.")
        sys.exit(1)

    if not args.sem_precos:
        threading.Thread(target=atualiza_precos_em_loop, args=(args.intervalo,),
                         daemon=True).start()
        print(f"Preços: recoleta a cada {args.intervalo//60} min em segundo plano.")

    url = f"http://127.0.0.1:{porta}/index.html"
    print(f"Dashboard em  {url}")
    print("Ctrl+C para encerrar.\n")
    if not args.sem_navegador:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
        servidor.shutdown()


if __name__ == "__main__":
    main()
