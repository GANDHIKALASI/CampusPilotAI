# CampusPilot AI — Vercel Frontend Deployment & Configuration Guide

**Production Frontend URL:** [https://campuspilotai.vercel.app](https://campuspilotai.vercel.app)
**Backend:** FastAPI + Nginx running in Docker on AWS EC2 (`t3.small`, Ubuntu)

---

## 1. Environment Variable Architecture & Double `/api` Guard

The frontend client in [frontend/src/lib/api.ts](file:///home/gandhi/Documents/github/CampusPilotAI/frontend/src/lib/api.ts) constructs all API requests using:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
```
And then makes requests like:
```typescript
fetch(`${API_BASE_URL}/waitlist`, ...)
fetch(`${API_BASE_URL}/conversations`, ...)
fetch(`${API_BASE_URL}/chat`, ...)
```

### Critical API URL Rule:
- When Nginx proxies `location /api/` on EC2, the public API path is `https://<YOUR_EC2_HOSTNAME_OR_IP>/api`.
- Therefore, `NEXT_PUBLIC_API_URL` on Vercel **must include `/api`**:
  ```env
  NEXT_PUBLIC_API_URL=https://<YOUR_EC2_HOSTNAME_OR_IP>/api
  ```
  *(Or `http://<YOUR_EC2_PUBLIC_IP>/api` for testing prior to SSL setup).*
- **Double `/api` Verification:** Individual API calls in `api.ts` call `${API_BASE_URL}/chat`, `${API_BASE_URL}/documents`, etc. They do **not** prepend an extra `/api/` in endpoint paths. Thus, setting `NEXT_PUBLIC_API_URL=https://.../api` produces exactly `https://.../api/chat`. There is **no double-appending of `/api`**.

---

## 2. Required Vercel Environment Variables

Set these three variables in the **Vercel Project Dashboard** (**Settings** → **Environment Variables**):

| Variable Name | Value | Purpose |
|:---|:---|:---|
| `NEXT_PUBLIC_API_URL` | `https://<YOUR_EC2_HOSTNAME>/api` | Directs client browser requests to the EC2 Nginx API gateway |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://your-project-id.supabase.co` | Supabase project REST URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | `your_supabase_anon_publishable_key` | Public client anon key for authentication & SSR session tokens |

> [!CAUTION]
> **Zero Backend Secrets in Vercel:**
> - Never add `SUPABASE_SECRET_KEY` (service role).
> - Never add `GEMINI_API_KEY`.
> - Never add `DATABASE_URL`.
> - Never add `RAZORPAY_KEY_SECRET`.
>
> All database mutations, LLM streaming, and security checks are handled exclusively by the EC2 FastAPI backend.

---

## 3. Supabase Auth Configuration for Vercel

In the [Supabase Dashboard](https://supabase.com/dashboard) under **Authentication** → **URL Configuration**:

1. **Site URL:**
   ```
   https://campuspilotai.vercel.app
   ```
2. **Redirect URLs (Allow list):**
   ```
   https://campuspilotai.vercel.app/**
   http://localhost:3000/**
   ```

---

## 4. Verification from Vercel

Once the backend is started on EC2:
1. Open [https://campuspilotai.vercel.app](https://campuspilotai.vercel.app) in your browser.
2. Open DevTools (F12) → **Console** and **Network**.
3. Verify that requests hit `https://<YOUR_EC2_HOSTNAME>/api/...` and receive `200 OK`.
4. Confirm no CORS errors appear in the browser console.
