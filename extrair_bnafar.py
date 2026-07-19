"""
extrair_bnafar.py
─────────────────
Loga no BNAFAR (relatório MicroStrategy do Ministério da Saúde), baixa o PDF
do relatório de medicamentos (DCB / Forma farmacêutica / Concentração) e
gera um bnafar_medicamentos.json para servir de FALLBACK no app de
receituário — usado só quando a busca não encontra nada na lista local
(PROTOCOLS) do app.html.

COMO USAR
---------
1. pip install playwright pdfplumber --break-system-packages
   playwright install chromium

2. Defina o usuário/senha do BNAFAR como variáveis de ambiente
   (não deixe senha hardcoded no script):

       set BNAFAR_USER=seu.usuario      (Windows, cmd)
       set BNAFAR_PASS=sua_senha
   ou
       export BNAFAR_USER=seu.usuario   (Linux/Mac/Git Bash)
       export BNAFAR_PASS=sua_senha

3. Rode:
       python extrair_bnafar.py

   Na primeira execução, deixe HEADLESS = False (linha abaixo) pra
   acompanhar o login na tela e confirmar/ajustar os seletores, caso a
   tela de login do BNAFAR não bata exatamente com o que o script espera
   (são apps MicroStrategy antigos, às vezes o HTML muda entre servidores).

4. O script salva:
     - bnafar_relatorio.pdf          (o PDF baixado, cru)
     - bnafar_medicamentos.json      (o que o app.html vai consumir)

   Copie o bnafar_medicamentos.json para a MESMA PASTA do app.html.
   O app tenta um fetch('bnafar_medicamentos.json') relativo — então só
   funciona se o app estiver sendo servido por um servidor (não abrindo
   direto do disco com file://). Se você abre o app.html direto do disco,
   me avise que eu troco a integração pra carregar via <script> embutido
   (const BNAFAR_FALLBACK = [...]) em vez de fetch.

RE-EXECUÇÃO
-----------
Rode esse script periodicamente (ex: 1x por mês) pra manter a lista
atualizada, do mesmo jeito que os outros scripts do
Rodar_Tudo_Consolidado.bat.
"""

import os
import re
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ────────────────────────────────────────────────────────────────

HEADLESS = False  # mude pra True depois de confirmar que o login funciona

LOGIN_URL = "https://ads.saude.gov.br/servlet/mstrWeb?evt=3001&src=mstrWeb.3001"

REPORT_URL = (
    "https://ads.saude.gov.br/servlet/mstrWeb?src=mstrWeb.3140&evt=3140"
    "&documentID=642B02B14CCFA8D7D876F3A50C77313B"
    "&Server=SRVBIPDF03&Port=0&Project=DMBnafar&"
)

PDF_SAIDA = Path("bnafar_relatorio.pdf")
JSON_SAIDA = Path("bnafar_medicamentos.json")

USUARIO = os.environ.get("BNAFAR_USER", "")
SENHA = os.environ.get("BNAFAR_PASS", "")

# Nomes de coluna esperados no PDF (ajuste se o cabeçalho vier diferente)
COL_DCB = "Denominação Comum Brasileira"
COL_FORMA = "Forma farmacêutica"
COL_CONC = "Concentração"


def aguardar_countdown(segundos, motivo=""):
    import time
    for s in range(segundos, 0, -1):
        print(f"\r  aguardando {s}s... {motivo}", end="", flush=True)
        time.sleep(1)
    print()


def fazer_login(page):
    """Tenta logar no MicroStrategy Web (BNAFAR) tentando alguns
    seletores comuns dessa versão do MicroStrategy. Se nenhum bater,
    imprime instrução clara pra inspecionar e ajustar."""
    page.goto(LOGIN_URL, wait_until="load")

    candidatos_user = [
        "input[name='mstrUserid']",
        "#userid",
        "input[name='userid']",
        "input[type='text']",
    ]
    candidatos_pass = [
        "input[name='mstrPasswd']",
        "#password",
        "input[name='password']",
        "input[type='password']",
    ]

    campo_user = None
    for sel in candidatos_user:
        loc = page.locator(sel).first
        if loc.count() > 0:
            campo_user = loc
            break

    campo_pass = None
    for sel in candidatos_pass:
        loc = page.locator(sel).first
        if loc.count() > 0:
            campo_pass = loc
            break

    if not campo_user or not campo_pass:
        print("\n[ERRO] Não encontrei os campos de usuário/senha na tela de login.")
        print("Abra o navegador (HEADLESS=False), veja o HTML real da tela de")
        print("login (botão direito > Inspecionar no campo de usuário) e ajuste")
        print("as listas 'candidatos_user' / 'candidatos_pass' no topo do script.")
        sys.exit(1)

    campo_user.fill(USUARIO)
    campo_pass.fill(SENHA)
    campo_pass.press("Enter")

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeout:
        pass


def baixar_relatorio_pdf(context, page):
    """Navega até o relatório. Como a URL aponta pro servidor de PDF
    (Server=SRVBIPDF03), o mais comum é isso disparar um download direto.
    Se não disparar, cai no plano B: procurar um botão de exportar."""
    try:
        with page.expect_download(timeout=30000) as download_info:
            page.goto(REPORT_URL, wait_until="commit")
        download = download_info.value
        download.save_as(str(PDF_SAIDA))
        print(f"PDF baixado direto: {PDF_SAIDA}")
        return
    except PWTimeout:
        print("Não veio um download automático — tentando plano B (botão de exportar)...")

    # Plano B: a página abriu normalmente (relatório na tela), procura um
    # botão/link de exportar para PDF no toolbar do MicroStrategy.
    page.goto(REPORT_URL)
    aguardar_countdown(5, "carregando relatório")

    candidatos_export = [
        "text=Exportar",
        "text=Export",
        "[title*='Export']",
        "[title*='PDF']",
        "a:has-text('PDF')",
    ]
    for sel in candidatos_export:
        loc = page.locator(sel).first
        if loc.count() > 0:
            try:
                with page.expect_download(timeout=20000) as download_info:
                    loc.click()
                download = download_info.value
                download.save_as(str(PDF_SAIDA))
                print(f"PDF baixado via botão de exportar: {PDF_SAIDA}")
                return
            except PWTimeout:
                continue

    print("\n[ERRO] Não consegui baixar o PDF automaticamente.")
    print("Abra com HEADLESS=False, veja como o relatório aparece na tela e")
    print("me avise o que você vê (a tabela direto, ou precisa clicar em algo")
    print("pra exportar) que eu ajusto o script.")
    sys.exit(1)


def normalizar_cabecalho(cel):
    return re.sub(r"\s+", " ", (cel or "").strip().lower())


def extrair_tabela_pdf(caminho_pdf):
    import pdfplumber

    itens = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                if not tabela or len(tabela) < 2:
                    continue
                cabecalho = [normalizar_cabecalho(c) for c in tabela[0]]

                def achar_col(nome_procurado):
                    alvo = normalizar_cabecalho(nome_procurado)
                    for i, c in enumerate(cabecalho):
                        if alvo in c or c in alvo:
                            return i
                    return None

                idx_dcb = achar_col(COL_DCB)
                idx_forma = achar_col(COL_FORMA)
                idx_conc = achar_col(COL_CONC)

                if idx_dcb is None:
                    continue  # tabela que não é a de medicamentos (ex: cabeçalho/rodapé)

                for linha in tabela[1:]:
                    nome = (linha[idx_dcb] or "").strip() if idx_dcb is not None and idx_dcb < len(linha) else ""
                    if not nome:
                        continue
                    forma = (linha[idx_forma] or "").strip() if idx_forma is not None and idx_forma < len(linha) else ""
                    conc = (linha[idx_conc] or "").strip() if idx_conc is not None and idx_conc < len(linha) else ""
                    itens.append({
                        "group": "BNAFAR (RENAME)",
                        "nome": nome,
                        "conc": conc,
                        "forma": forma,
                        "via": "",
                        "uso": "",
                        "protocolo": "Relação Nacional de Medicamentos Essenciais (RENAME/BNAFAR)",
                    })
    return itens


def main():
    if not USUARIO or not SENHA:
        print("[ERRO] Defina as variáveis de ambiente BNAFAR_USER e BNAFAR_PASS antes de rodar.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("Fazendo login no BNAFAR...")
        fazer_login(page)

        print("Baixando relatório...")
        baixar_relatorio_pdf(context, page)

        browser.close()

    print("Extraindo tabela do PDF...")
    itens = extrair_tabela_pdf(PDF_SAIDA)

    if not itens:
        print("[AVISO] Não encontrei nenhuma linha de medicamento no PDF.")
        print("Abra o bnafar_relatorio.pdf manualmente pra conferir o formato")
        print("da tabela — pode ser que os nomes das colunas (COL_DCB, COL_FORMA,")
        print("COL_CONC) no topo do script precisem de ajuste.")

    # Remove duplicados (mesmo nome+conc+forma)
    vistos = set()
    itens_unicos = []
    for it in itens:
        chave = (it["nome"].lower(), it["conc"].lower(), it["forma"].lower())
        if chave not in vistos:
            vistos.add(chave)
            itens_unicos.append(it)

    JSON_SAIDA.write_text(
        json.dumps(itens_unicos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n{len(itens_unicos)} medicamentos salvos em {JSON_SAIDA}")
    print("Copie esse arquivo pra mesma pasta do app.html.")


if __name__ == "__main__":
    main()
