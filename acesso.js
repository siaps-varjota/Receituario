/* ============================================================
   acesso.js — controle de acesso por categoria profissional
   Portal de Saúde · Varjota/CE
   ============================================================
   COMO USAR
   - portal.html   : <script src="acesso.js"></script> + Acesso.aplicarPortal();
   - cada app      : no <head>, antes de tudo:
                     <script src="acesso.js"></script>
                     <script>Acesso.guardarPagina();</script>
   ============================================================ */
(function () {
  var SESSION_KEY = "receituario_auth";
  var PORTAL  = "portal.html";
  var LOGIN   = "index.html";

  /* ── CONFIGURAÇÃO ─────────────────────────────────────────
     Chave   = categoria (como está na planilha; acento, maiúscula
               e "(A)" são ignorados: "MÉDICO(A)" = "medico").
     Valor   = arquivos que essa categoria NÃO pode abrir.
     Categoria que não aparece aqui tem acesso a tudo
     (ex.: Coordenação, ENFERMEIRO(A)).
  ─────────────────────────────────────────────────────────── */
  var BLOQUEIOS = {
    "MÉDICO(A)": ["app.html", "tuberculose.html"]
    // exemplos para o futuro:
    // "TÉCNICO(A) DE ENFERMAGEM": ["app.html", "gestante.html"],
    // "ODONTÓLOGO(A)":            ["app.html", "hanseniase.html"],
  };

  /* ── internos ── */
  function norm(s) {
    return String(s || "")
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")   // tira acentos
      .replace(/\(.*?\)/g, "")                             // tira "(A)"
      .replace(/[^A-Za-z ]/g, "")
      .replace(/\s+/g, " ").trim().toUpperCase();
  }

  var REGRAS = {};
  Object.keys(BLOQUEIOS).forEach(function (cat) {
    REGRAS[norm(cat)] = BLOQUEIOS[cat].map(function (f) { return f.toLowerCase(); });
  });

  function sessao() {
    try {
      var d = JSON.parse(sessionStorage.getItem(SESSION_KEY));
      if (d && d.exp && Date.now() < d.exp) return d;
    } catch (e) {}
    return null;
  }

  function nomeArquivo(href) {
    return String(href || "").split("#")[0].split("?")[0].split("/").pop().toLowerCase();
  }

  function bloqueado(href) {
    var s = sessao();
    if (!s) return false;                       // sem sessão: quem cuida é o guard de login
    var lista = REGRAS[norm(s.categoria)];
    return !!lista && lista.indexOf(nomeArquivo(href)) !== -1;
  }

  /* ── API pública ── */
  window.Acesso = {
    pode: function (href) { return !bloqueado(href); },

    // portal.html: remove os cards que a categoria não pode ver
    aplicarPortal: function () {
      var grid = document.querySelector(".grid");
      document.querySelectorAll("a.card[href]").forEach(function (a) {
        if (bloqueado(a.getAttribute("href"))) a.remove();
      });
      if (grid && !grid.querySelector("a.card")) {
        grid.innerHTML = '<p style="grid-column:1/-1;color:#6b7a99;text-align:center;padding:40px 0">' +
                         'Nenhum aplicativo liberado para a sua categoria profissional.</p>';
      }
    },

    // páginas dos apps: exige login e barra quem não tem permissão
    guardarPagina: function () {
      if (!sessao()) { location.replace(LOGIN); return; }
      if (bloqueado(location.pathname)) {
        alert("Este aplicativo não está disponível para a sua categoria profissional.");
        location.replace(PORTAL);
      }
    }
  };
})();
