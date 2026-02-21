# SFDA Travel Intelligence — Full-Stack Application

Complete Django REST API + React frontend for generating Milken-style travel intelligence PDF reports.

---

## 🏗️ Architecture

```
sfda_app/
├── backend/           Django REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── sfda_project/  (settings, urls, wsgi)
│   └── reports_app/   (models, views, serializers, pdf_generator, ai_generator)
│       └── templates/reports_app/milken_report.html
└── frontend/          React App
    ├── package.json
    └── src/
        ├── App.jsx           (main dashboard)
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── WorldMap.jsx   (D3 interactive map)
        │   ├── NewReportForm.jsx (form + AI generation)
        │   └── AIAssistant.jsx   (chat interface)
        └── services/api.js   (axios API calls)
```

---

## ⚙️ Setup

### 1. Backend (Django)

```bash
cd sfda_app/backend

# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export OPENAI_API_KEY="your-openai-key-here"

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver 0.0.0.0:8000
```

### 2. Frontend (React)

```bash
cd sfda_app/frontend

# Install dependencies
npm install

# Start development server
npm start
# Opens at http://localhost:3000
```

---

## 🚀 How It Works

1. **Create Report** — Fill in event name, location, dates
2. **AI Generation** — Claude API generates ALL sections:
   - Visit objectives
   - Country info & statistics
   - Delegation list (3 members)
   - Multi-day agenda
   - Conference data, slogan, tracks
   - Previous outcomes
   - Session-by-session schedule
   - 8 key speakers with bios
   - 2+ bilateral meetings with talking points
   - Consulate/embassy contacts
   - Weather forecast (per day)
   - Prayer times (per day)
   - Attachments list
3. **Download PDF** — Click "Download PDF" to get Milken-style formatted document
4. **Preview HTML** — View the report in browser

---

## 📡 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET    | /api/reports/ | List all reports |
| POST   | /api/reports/ | Create new report |
| GET    | /api/reports/{id}/ | Get report detail |
| PATCH  | /api/reports/{id}/ | Update report |
| DELETE | /api/reports/{id}/ | Delete report |
| POST   | /api/reports/{id}/generate/ | AI-generate all content |
| GET    | /api/reports/{id}/pdf/ | Download PDF |
| GET    | /api/reports/{id}/preview/ | Preview HTML |
| POST   | /api/assistant/ | AI chat |
| GET    | /api/stats/ | Dashboard stats |

---

## 📄 PDF Structure (Matches Milken PDF)

1. Cover Page — gradient, logos, title, meta
2. Table of Contents
3. Visit Overview — objectives table
4. Country Info — stats grid, flag data
5. Detailed Agenda — multi-day table
6. Delegation List — names, titles, departments
7. **Section Divider** — Conference
8. Conference Data — organizer, slogan, stats
9. Conference Tracks — 10-12 tracks
10. Previous Outcomes — 2023/2024
11. **Section Divider** — Sessions
12. Sessions by Day — time, title, speakers
13. **Section Divider** — Speakers
14. Speakers Table — name, title, org, country
15. Speaker Cards Grid — with bios
16. **Section Divider** — Bilateral Meetings
17. Bilateral Meeting Cards — with talking points
18. **Section Divider** — Consulate
19. Consulate Info — contacts, consul bio
20. Weather + Prayer Times
21. Attachments

---

## 🌐 Frontend Pages

- **Dashboard** — Stats, world map, upcoming destinations, political feed, WHO alerts, recent reports
- **Reports** — Table with PDF download and preview buttons
- **New Report** — Form with AI generation workflow
- **AI Assistant** — Chat interface with full report context

---

## 🔑 Environment Variables

```bash
OPENAI_API_KEY=sk-...
```

---

## 📦 Production Build

```bash
# Build React
cd frontend && npm run build

# Serve Django with static files
cd backend
pip install gunicorn
gunicorn sfda_project.wsgi:application --bind 0.0.0.0:8000
```
