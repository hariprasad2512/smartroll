# SmartRoll deployment

This monorepo deploys the Vite frontend to Cloudflare Pages, the FastAPI backend to Render, and uses Supabase for PostgreSQL. Each hosting service is configured on its free tier.

## 1. Create the Supabase database

1. Use the Supabase project in Sydney (`ap-southeast-2`) and select the Free plan.
2. The supplied endpoint is a Supabase Session Pooler URL on port `5432`. Set `DATABASE_URL` to `postgresql+psycopg2://postgres.hilydvamoleyykcnvsnk:URL_ENCODED_PASSWORD@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require`. Replace the password placeholder with your URL-encoded database password. Store this URL in Render's secret environment setting and in `backend/.env` for local use; do not commit a real password.
3. The application creates its SQLAlchemy tables at startup. Do not use SQLite in a deployed service because Render's local filesystem is ephemeral.

Supabase Free projects may be paused after seven days of low activity and do not include automatic backups. Export attendance records regularly if they need to be retained. [Supabase Free project pausing](https://supabase.com/docs/guides/platform/free-project-pausing) · [Supabase pricing](https://supabase.com/pricing)

## 2. Deploy the API to Render

Create a Blueprint from the `hariprasad2512/smartroll` repository. Render uses the top-level `render.yaml`, which builds `backend/Dockerfile`, selects the Free plan, deploys in Singapore, and checks `/health`.

When Render prompts for Blueprint environment variables, set:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Supabase Session Pooler URL with `sslmode=require` |
| `GOOGLE_CLIENT_ID` | The Google OAuth Web client ID |
| `FACULTY_EMAILS` | Comma-separated faculty Google account emails |
| `CORS_ORIGINS` | Exact Pages origin, e.g. `https://smartroll.pages.dev`; add the custom domain too if used |

The API must be publicly reachable by the browser; faculty and student endpoints enforce authorization. Copy the deployed `onrender.com` URL for the frontend's `VITE_API_URL`.

On startup, the API adds the session interval and student Enrollment ID columns to an existing database. Existing sessions keep the previous 30-second QR interval; new sessions default to 60 seconds. Students link an Enrollment ID the next time they sign in. IDs are normalized to uppercase and must be unique.

Render Free services sleep after 15 minutes without inbound traffic and can take about a minute to wake on the next request. [Render Free limits](https://render.com/docs/free)

## 3. Deploy the frontend to Cloudflare Pages

Connect `hariprasad2512/smartroll` to Pages and use these build settings:

| Setting | Value |
| --- | --- |
| Framework preset | Vite |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Node version | `20` |

Set these Pages build environment variables:

| Variable | Value |
| --- | --- |
| `VITE_API_URL` | Deployed Render service URL, no trailing slash |
| `VITE_GOOGLE_CLIENT_ID` | Same Google OAuth Web client ID as the API |

Set both variables in the Pages project's **Build → Environment variables** for the Production environment, then trigger a new deployment. `VITE_API_URL` must be the public URL Render assigned to `smartroll-api` (for example, `https://smartroll-api-<suffix>.onrender.com`), with no `/health` or trailing slash. These are build-time values: changing them does not update an already-built deployment until it is rebuilt. Do not use `http://localhost:8000` here; in a deployed browser that means the visitor's own computer.

`frontend/public/_redirects` provides the SPA fallback for direct links such as `/faculty`, `/student`, and QR check-in routes.

## 4. Configure Google OAuth

In Google Cloud Console → **APIs & Services → Credentials**, edit the OAuth Web client and add the Pages URL (for example, `https://smartroll.pages.dev`) under **Authorized JavaScript origins**. Add the custom domain origin if configured. Google Identity Services credential sign-in uses JavaScript origins; no callback URL is needed for this implementation.

## 5. Verify deployment

1. Open the Render API's `/health` and confirm it returns `{"status":"ok", ...}`.
2. Sign in with a listed faculty email and confirm the app stays on `/faculty` after refresh.
3. Start a session and open the classroom display. Scan its QR code on another device and sign in as a student.
4. Confirm attendance appears on the faculty page and review Render logs for database or CORS errors.

If sign-in reports a network or fetch error, inspect the frontend request to `/api/auth/google` in the browser's Network panel. Confirm its request URL starts with the Render API URL, then confirm `CORS_ORIGINS` on Render contains the exact frontend origin shown in the address bar (scheme and hostname, without a path). After changing either frontend build variable or the backend CORS value, redeploy the corresponding service.
