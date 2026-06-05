# Authentication Setup

Last updated: 2026-06-06 (v3.4.0)

VyroPortify delegates the entire credentials UX — registration, login,
password reset, email OTP, phone OTP, social sign-in — to **Clerk**. Clerk
covers every requirement out of the box; we just need to flip the right
switches in their dashboard and connect a webhook.

Supported methods (after the steps below are complete):

| Method | Where |
|---|---|
| Email + password | Clerk hosted UI |
| Email OTP (6-digit code) | Clerk hosted UI |
| Phone OTP (SMS, 6-digit code) | Clerk hosted UI (when SMS provider attached) |
| Google one-click | Clerk hosted UI |
| GitHub one-click | Clerk hosted UI |
| Forgot password (OTP-verified) | Clerk hosted UI |

## 1. Enable identifiers + verification

1. Open your Clerk dashboard → **User & Authentication → Email, Phone, Username**.
2. Under **Contact information**:
   - ✅ **Email address** → required, used for sign-in, verify at sign-up
   - ✅ **Phone number** → required, used for sign-in, verify at sign-up
3. Under **Authentication strategies**:
   - ✅ **Password**
   - ✅ **Email verification code** (this is "Email OTP")
   - ✅ **SMS verification code** (this is "Phone OTP" — needs an SMS provider; see §5)

## 2. Enable social providers

1. **User & Authentication → Social Connections**.
2. Add **Google** → "Use custom credentials" if you want your own OAuth
   client (recommended for production); otherwise the Clerk dev creds work
   for local testing.
3. Add **GitHub** → same flow.
4. Under each provider's settings, scope to `profile email`.

## 3. Collect full name during signup

1. **User & Authentication → Personal information**.
2. ✅ **First name** → required
3. ✅ **Last name** → required

This is how Clerk satisfies the "Full Name" field from the spec — they're
captured at signup and exposed in the webhook payload as `first_name` and
`last_name`, which our handler joins into `users.name`.

## 4. Configure the user-mirror webhook

1. **Webhooks → Add Endpoint**.
2. Endpoint URL: `https://<your-api-host>/api/v1/auth/clerk-webhook`
3. Subscribe to events:
   - `user.created`
   - `user.updated`
   - `user.deleted`
4. Copy the **Signing Secret** (`whsec_…`).
5. In `backend/.env` set:
   ```
   CLERK_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
   ```
6. Restart the backend. Send a test event from the dashboard → you should
   see `event=user.created status=ok` in `/tmp/vyro-backend.log`.

What this gives you:

- Every signup writes a row to `users` with `name`, `email`, `phone_number`,
  `created_at` — automatically populating the data the export endpoints need.
- A personal workspace + owner-role membership is created so the user can
  use billing, RBAC, and analytics immediately.
- Email & phone changes propagate; account deletes cascade-delete portfolios
  and resumes via the existing `ondelete=CASCADE` FKs.

## 5. (Optional) Phone OTP needs an SMS provider

Clerk hosts the UI but you bring the SMS sender. Options:

- **Clerk default** (Free tier) — limited dev volume; fine for staging.
- **Twilio** — Clerk dashboard → SMS Provider → Twilio → paste Account SID + Auth Token.
- **Vonage / MessageBird** — similar Clerk integration.

Skip if you only need email OTP for now; Clerk will hide the phone-OTP
button when no provider is connected.

## 6. Rate limiting

Clerk applies its own brute-force protection on OTP requests (5 attempts /
hour / phone-or-email by default). On top, our backend rate-limits:

- `/api/v1/oauth/token` → 20/min (already in place from v3.3.1)
- Sign-in retries are bucketed in Redis by IP + hashed email via `RateLimitDep`

## 7. Where the auth UI lives

The Next.js frontend renders Clerk's `<SignIn />` and `<SignUp />` components
on `/login` and `/signup`. They automatically render the methods you
enabled — toggling SMS OTP in the Clerk dashboard makes the button appear
in the UI without any frontend code change.

If you want a custom-styled UI instead of Clerk's hosted screens, swap
`<SignIn />` for `<SignIn.Root />` and compose your own form using Clerk's
headless API. Validation messages and error states come from Clerk's
`isLoaded` / `signIn.status` machine.

## 8. Verification checklist

```bash
# 1. Webhook lands and stores the user
curl -s http://localhost:8001/api/v1/admin/users.csv \
     -H "Authorization: Bearer <your_clerk_jwt>" | head -3

# 2. XLSX downloads
curl -s -o /tmp/users.xlsx http://localhost:8001/api/v1/admin/users.xlsx \
     -H "Authorization: Bearer <your_clerk_jwt>"
file /tmp/users.xlsx   # → "Microsoft Excel 2007+"

# 3. Duplicate signup is prevented
#    Clerk surfaces "That email address is taken" / "That phone is taken"
#    directly in the hosted UI. The DB layer also rejects via the
#    UNIQUE indexes on users.email and users.phone_number.
```

## Why we don't build a custom email/password router

The spec asks for password + email-OTP + phone-OTP + Google + GitHub.
Building those from scratch means owning:

- bcrypt + password reset flows + breach checks
- transactional OTP email + SMS routing + retry semantics
- OAuth2 PKCE flows for two providers
- session cookies + CSRF + CORS
- account-takeover heuristics

Clerk does all of that, is SOC 2 Type II, and the integration is one
webhook + the `<SignIn />` component. The work in this release is
deliberately scoped to wiring + export, not reinventing identity.
