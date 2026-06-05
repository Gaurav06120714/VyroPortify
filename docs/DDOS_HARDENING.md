# DDoS Hardening — Operational Playbook

Last updated: 2026-06-06 (v3.3.1)

## What's already in code

| Layer | Where | Notes |
|---|---|---|
| Per-IP rate limits | `slowapi` in `app/core/limiter.py` + route decorators | Backed by Redis. AI build: 6/hr, /oauth/token: 20/min. |
| Per-account daily quota | `app/services/quota.py` | Plan-aware (free 5, pro 50, ent 500 builds/day). |
| Webhook receiver throttle | `app/workers/tasks/deliver_webhook.py` | 60 deliveries / endpoint / minute. |
| Request size limit | `enforce_request_size_limit` middleware | `MAX_REQUEST_BODY_BYTES` from settings. |
| Scanner-path drop | `ddos_hardening` middleware | `/wp-admin`, `/.env`, `/.git/`, etc. → 404 instantly. |
| User-Agent gate on writes | `ddos_hardening` middleware | Empty/`<3` chars → 400 on POST/PUT/PATCH/DELETE. |
| Edge cache headers | `ddos_hardening` middleware | `public, max-age=300, s-maxage=900` on `/portfolio/p/*`. |
| Security headers | `add_security_headers` middleware | CSP, HSTS, X-Frame-Options, etc. |

## What still needs **you** to set up (not code)

### 1. Cloudflare in front of the production domain — *do this first*

1. Sign up at https://dash.cloudflare.com (free).
2. Add your domain → pick the **Free plan**.
3. Update your DNS at the registrar (Namecheap/GoDaddy/etc.) to use Cloudflare's nameservers.
4. In Cloudflare → **DNS** tab, add an `A` (or `CNAME`) record for `api.yourdomain.com` pointing to the backend host. Make sure the orange cloud is **ON** (proxied).
5. In Cloudflare → **Security → WAF**:
   - Turn on **"Bot Fight Mode"**.
   - Turn on the managed ruleset (default in Free).
6. In Cloudflare → **Security → DDoS**: leave defaults — L3/L4 protection is automatic on every plan.
7. **"Under Attack" mode**: a single toggle on the dashboard. Flip it on if you see a flood; it forces a JS challenge on every request for 24h.

After this is done, point `PROXY_DEPTH=1` in your backend `.env` so `slowapi` correctly extracts the real client IP from `CF-Connecting-IP`.

### 2. Cloudflare Turnstile (CAPTCHA) on signup + AI builder

1. Cloudflare dashboard → **Turnstile** → "Add site".
2. Note the **Site key** (public) and **Secret key** (private).
3. Frontend: render the Turnstile widget on `/signup` and `/builder` (npm: `@marsidev/react-turnstile`).
4. Backend: on those routes, accept a `cf-turnstile-response` form/header value and POST it to:
   ```
   POST https://challenges.cloudflare.com/turnstile/v0/siteverify
       secret=<TURNSTILE_SECRET> response=<token>
   ```
   Reject the request if `success != true`.
5. Add `TURNSTILE_SECRET` to `backend/.env`.

### 3. Production proxy config (nginx in front of uvicorn)

If you self-host instead of using Render/Fly, the proxy should add these:

```nginx
client_max_body_size 10M;
client_body_timeout 10s;
client_header_timeout 10s;
send_timeout 10s;

limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_conn_zone $binary_remote_addr zone=perip:10m;

location / {
    limit_req zone=api burst=60 nodelay;
    limit_conn perip 20;
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 4. Autoscaling cap (Render / Fly / Railway)

Set a **hard max instance count** in your platform's autoscale settings. A
runaway flood that auto-scales to 50 instances will burn through credit before
your alerting fires. A 5-instance cap is sane for early production.

### 5. Alerting

Hook Sentry to email/Slack on:

- 5xx rate > 1% over 5 minutes
- 429 rate spike > 10× baseline
- Sudden drop in DB connection pool free count

## Incident playbook (when an attack hits)

1. Cloudflare dashboard → flip **"Under Attack" mode** on the affected hostname.
2. Tail `/tmp/vyro-backend.log` and `tail -f` Cloudflare's Security Events to see the source ASNs / paths.
3. If the attack is hitting a specific path, add a **Firewall Rule** in
   Cloudflare to challenge or block it (e.g. `(http.request.uri.path eq
   "/api/v1/resume/build" and ip.geoip.country in {"CN" "RU"})`).
4. If your origin is being hit directly (DNS leak), add `Origin Rules` to
   require `cf-connecting-ip` headers, or rotate the origin to a new IP.
5. After the storm passes, review which quotas/limits were tripped and tune.

## Verification

```bash
# Scanner path → 404 from middleware, not the framework router
curl -sI http://localhost:8001/.env | head -1   # → HTTP/1.1 404

# Missing UA on POST → 400
curl -X POST -H "User-Agent:" http://localhost:8001/api/v1/auth/me   # → 400

# Edge cache header on public viewer
curl -sI http://localhost:8001/api/v1/portfolio/p/<slug> | grep -i cache-control
```
