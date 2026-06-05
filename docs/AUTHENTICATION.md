# Authentication

## 🔐 Authentication — Password, Email OTP & Phone OTP

VyroPortify supports **three sign-in methods**, all powered by Clerk:

| Method | How it works |
|---|---|
| **Email + Password** | Classic credential login |
| **Email OTP** | One-time 6-digit code sent to the user's email |
| **Phone OTP (SMS)** | One-time 6-digit code sent via SMS |
| **Social (Google, GitHub)** | OAuth single-click sign-in |

The `<SignIn />` and `<SignUp />` components on `/login` and `/register` automatically render whichever factors are enabled in the Clerk dashboard — **no code change is required**.

### Enable OTP (one-time setup)

1. Open the **Clerk Dashboard** → your project → **User & Authentication → Email, Phone, Username**.
2. Toggle on:
   - ✅ **Email address** → *Verification: Email verification code*
   - ✅ **Phone number** → *Verification: SMS verification code*
3. Under **User & Authentication → Authentication strategies**, enable:
   - ✅ **Email verification code**
   - ✅ **SMS verification code**
   - (keep) **Password**, **Google**, **GitHub**
4. Save. The login/register pages immediately offer OTP options.

> 💡 Phone OTP requires a Clerk plan with SMS credits. Free tier ships ~100 SMS/mo.

### Backend impact

- Backend treats every authenticated request the same way — it verifies the Clerk JWT via JWKS (`app/security.py`). OTP vs password vs social is transparent to the API.
- New users created via OTP are auto-provisioned on first authenticated call (existing behavior).

