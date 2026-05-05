# Receituário e-SUS — SESAVAR

Plataforma de geração de receituários simples e de controle especial (antibióticos) para enfermeiros(as) da Secretaria de Saúde de Varjota.

## 🔐 Acesso

A plataforma é protegida por senha. As credenciais padrão estão em `index.html`, no objeto `USERS`:

```javascript
const USERS = {
  "enfermeiro":  "sesavar2025",
  "admin":       "admin@2025",
  "sesavar":     "receita2025"
};
```

**Para alterar as senhas:** edite o arquivo `index.html` e modifique os pares `"usuário": "senha"`.

## 🚀 Como implantar no GitHub Pages

### 1. Crie o repositório

1. Acesse [github.com](https://github.com) e entre na sua conta.
2. Clique em **"New repository"**.
3. Dê um nome (ex: `receituario-sesavar`).
4. Marque como **Privado** (recomendado) ou Público.
5. Clique em **"Create repository"**.

### 2. Faça o upload dos arquivos

Opção A — pela interface web:
1. Na página do repositório clique em **"uploading an existing file"**.
2. Arraste todos os arquivos desta pasta e clique em **"Commit changes"**.

Opção B — via Git (linha de comando):
```bash
git init
git add .
git commit -m "Primeira versão do receituário"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/receituario-sesavar.git
git push -u origin main
```

### 3. Ative o GitHub Pages

1. No repositório vá em **Settings → Pages**.
2. Em **Source** selecione **"GitHub Actions"**.
3. O workflow `.github/workflows/deploy.yml` já está configurado e publicará automaticamente a cada push.
4. Após o primeiro deploy aparecerá o link público (ex: `https://seu-usuario.github.io/receituario-sesavar/`).

## 📁 Estrutura de arquivos

```
├── index.html          ← Tela de login (altere as senhas aqui)
├── app.html            ← Receituário completo (protegido por sessão)
├── .github/
│   └── workflows/
│       └── deploy.yml  ← Pipeline de deploy automático
└── README.md
```

## ⚠️ Segurança

A autenticação é feita no lado do cliente (JavaScript + `sessionStorage`). Isso é adequado para uso interno/intranet com acesso controlado. Para ambientes críticos recomenda-se um backend com autenticação real.

A sessão expira automaticamente em **8 horas**.

---

Desenvolvido por **Alidemberg Araújo** · Coordenador do e-SUS Municipal · SESAVAR
