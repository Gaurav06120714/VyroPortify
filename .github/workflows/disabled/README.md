# Disabled workflows

These deploy workflows are templates for when you wire up Railway (backend)
and Vercel (frontend) hosting. They're kept here, renamed to `.tmpl`, so:

1. GitHub Actions does **not** discover them (the `workflows/` directory only
   loads `.yml` / `.yaml` files at its top level).
2. Their failed runs no longer clutter the CI history.

To activate one:

1. Move it back into `.github/workflows/`.
2. Rename `.tmpl` → `.yml`.
3. Add the required secrets (`RAILWAY_TOKEN`, `VERCEL_TOKEN`,
   `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`) under
   **Settings → Secrets and variables → Actions**.
4. Trigger manually from the **Actions** tab → "Deploy Backend" → "Run workflow".
