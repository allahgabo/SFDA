# 🚀 SFDA Travel Intelligence — Render Deployment Guide

## Architecture on Render
```
One service:  sfda-app  (Django serves React + API)
One database: sfda-db   (PostgreSQL, free tier)
```
Django serves the React build at `/` and the API at `/api/`.
No separate frontend service needed.

---

## Step-by-Step Deployment

### 1. Push to GitHub

```bash
# In your project folder (sfda_app/)
git init
git add .
git commit -m "Initial commit — SFDA Travel Intelligence"

# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/sfda-app.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Render

1. Go to **https://render.com** → Sign in / Sign up
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account
4. Select your **sfda-app** repository
5. Render detects `render.yaml` automatically → Click **"Apply"**
6. Two resources are created:
   - `sfda-db` — PostgreSQL database
   - `sfda-app` — Web service

### 3. Set Your API Keys

After the service is created (before or after first deploy):

1. Go to **sfda-app** → **Environment** tab
2. Add these variables:
   ```
   ANTHROPIC_API_KEY   =  sk-ant-api03-...your key...
   OPENAI_API_KEY      =  sk-proj-...your key...
   ```
3. Click **"Save Changes"** → Render redeploys automatically

### 4. First Deploy (~5-8 minutes)

Watch the build logs. You should see:
```
✅ React build complete
✅ React build copied to backend/frontend_build
✅ Python packages installed
✅ Static files collected, migrations applied
✅ Created admin user: admin@sfda.gov.sa / SFDAadmin2025!
✅ Build complete!
```

### 5. Access Your App

Your app URL: `https://sfda-app.onrender.com`

**Default login:**
```
Email:    admin@sfda.gov.sa
Password: SFDAadmin2025!
```
⚠️ Change this password immediately after first login!

---

## Optional: Custom Password

Add to Render environment variables before first deploy:
```
DEFAULT_ADMIN_EMAIL     =  your@email.com
DEFAULT_ADMIN_PASSWORD  =  YourSecurePassword123!
```

---

## Troubleshooting

### Build fails: "libpango not found"
The `build.sh` installs WeasyPrint system dependencies automatically.
If it fails, check build logs for the apt-get step.

### App loads but API returns 404
Make sure `build.sh` ran successfully and `frontend_build/` exists.

### "Database connection failed"
Render links the database automatically via `DATABASE_URL`.
If you deployed manually (not via Blueprint), add `DATABASE_URL` from:
Render Dashboard → sfda-db → Info → "Internal Database URL"

### Free tier "spins down" after 15 minutes
Free Render services sleep when inactive. First request after sleep takes ~30 seconds.
Upgrade to **Starter ($7/mo)** for always-on behavior.

---

## Local Development (unchanged)

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python manage.py runserver

# Terminal 2 — Frontend
cd frontend
npm install
npm start
```

---

## File Structure
```
sfda_app/
├── render.yaml          ← Render deployment config
├── build.sh             ← Build script (runs on Render)
├── .gitignore
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── sfda_project/
│   │   ├── settings.py  ← env-aware (DEBUG, SECRET_KEY, DATABASE_URL)
│   │   ├── urls.py      ← serves React catch-all
│   │   └── wsgi.py
│   └── reports_app/
└── frontend/
    ├── package.json
    └── src/
```
