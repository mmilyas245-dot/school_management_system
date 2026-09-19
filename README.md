# ZALMI Institute - Clerk Management System (Streamlit)

A free, web-based replacement for the Excel/VBA clerk system: same fields
(Personal / Academic / Financial details), full CRUD (Add, Search, Update,
Delete, View all), a free cloud database, and every change auto-mirrored to
a Google Sheet.

**Stack (all free):**
- **Streamlit Community Cloud** — hosts the web app
- **Supabase** (or Neon) — free Postgres database, the source of truth
- **Google Sheets** — a live mirror of the data, updated on every save

---

## 1. Create the free database (Supabase)

1. Go to https://supabase.com → Sign up (free) → **New project**.
2. Pick any name/region, set a database password (save it somewhere safe).
3. Once the project is ready, go to **Project Settings → Database**.
4. Under **Connection string**, choose the **URI** tab, and copy it. It looks like:
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxx.supabase.co:5432/postgres`
5. Replace `[YOUR-PASSWORD]` with the password you set. This full string is your `DB_URL`.

   *(Neon.tech works the same way if you prefer it — free tier, same "copy connection string" step.)*

You do **not** need to create the table yourself — the app creates the
`students` table automatically the first time it runs.

---

## 2. Create the Google Sheet + service account (for the live mirror)

1. Go to https://console.cloud.google.com/ → create a new project (any name).
2. In **APIs & Services → Library**, enable:
   - **Google Sheets API**
   - **Google Drive API**
3. Go to **APIs & Services → Credentials → Create Credentials → Service account**.
   Give it any name, click through, no extra roles needed.
4. Open the new service account → **Keys** tab → **Add Key → Create new key → JSON**.
   This downloads a `.json` file — keep it private.
5. Open the JSON file. You'll paste its contents into Streamlit's secrets in Step 4.
6. Create a new Google Sheet (sheets.new). Copy the **Sheet ID** from its URL:
   `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`
7. Click **Share** on the sheet, and share it with the service account's
   email (looks like `xxxx@xxxx.iam.gserviceaccount.com`, found in the JSON
   as `client_email`) — give it **Editor** access.

---

## 3. Put the code on GitHub

1. Create a new GitHub repository (can be private).
2. Upload all the files in this folder (`app.py`, `requirements.txt`, `README.md`).
   **Do not upload `.streamlit/secrets_example.toml` with real secrets filled in** —
   it's just a template.

---

## 4. Deploy for free on Streamlit Community Cloud

1. Go to https://share.streamlit.io/ → sign in with GitHub → **New app**.
2. Pick your repo, branch `main`, main file path `app.py` → **Deploy**.
3. While it's building (or after), go to your app's **Settings → Secrets**
   and paste in something like this (fill in your real values from Steps 1–2):

```toml
APP_USERNAME = "admin"
APP_PASSWORD = "choose-a-real-password"

DB_URL = "postgresql://postgres:YOURPASSWORD@db.xxxxxxxx.supabase.co:5432/postgres"

GOOGLE_SHEET_ID = "your-sheet-id-from-the-url"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

   (Copy every field straight from the JSON key file you downloaded — just
   wrap the whole thing under the `[gcp_service_account]` header as shown.)

4. Save. The app will reboot and be live at a public `*.streamlit.app` URL —
   share that link with your clerks.

---

## 5. Using the app

- **➕ New Entry** — same fields as the old Excel form (Personal, Academic,
  Financial). Offer Fees and Due Fees are calculated automatically.
- **🔍 Search / Update / Delete** — search by name, admission no, father's
  name, or mobile number; pick a record; edit and Update, or Delete it.
- **📋 All Records** — full table, totals, and a CSV download (open the CSV
  in Excel/Sheets to print, or use your browser's Ctrl+P on that page).
- Every Add / Update / Delete instantly rewrites the connected Google Sheet,
  so it always matches the database exactly.

## Customizing dropdown options

Open `app.py` and edit the lists near the top:
`COURSES`, `CLASS_LEVELS`, `CLASS_TIMINGS`, `MATERIAL_OPTIONS`, `STATUS_OPTIONS`
to match your institute's actual courses/teachers/timings.

## Notes

- Photo upload was intentionally left out of this first version (can be
  added later using Supabase Storage, another free service).
- Login is a single shared clerk username/password (from secrets) — good
  enough for a small front-desk team. Ask if you'd like per-user accounts.
