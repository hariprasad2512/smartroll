#  🎓 **SmartRoll — Real-Time Dynamic Attendance Web App**

> Deployment guide: [Cloudflare Pages + Render + Supabase](../DEPLOYMENT.md)

<p align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Deployed%20on-Zerops-00DC82?style=for-the-badge&logo=zerops&logoColor=white" alt="Zerops" />
</p>

> **SmartRoll** replaces paper attendance with Google sign-in and rotating classroom QR check-ins. Short-lived codes and device registration help deter proxy attendance; they cannot guarantee physical presence.

This was submitted as part of The Zerops Challenge 2026.

LIVE LINK --- https://frontend-2c95-3000.prg1.zerops.app
---


## 🔗 Repository Links

* **Frontend Repo:** 🌐 [SmartRoll Frontend Client](https://github.com/hariprasad2512/smartroll-frontend)
* **Backend Repo:** ⚙️ [SmartRoll FastAPI Backend](https://github.com/hariprasad2512/smartroll-backend)

---

## 💡 System Architecture & Problem Solved

| Old Roll Call ❌ | SmartRoll Way ⚡ |
| :--- | :--- |
| Passing paper registers or calling out names manually. | Single-page dynamic QR code projected on class screen. |
| Wastes 5–10 minutes of valuable teaching time. | Attendance completed in under 60 seconds. |
| Proxies via screenshots sent on WhatsApp. | TOTP dynamic tokens rotate every 60 seconds. |
| Invasive GPS or native app downloads required. | 100% web-based; works on any mobile browser. |

---

## 🛠️ Complete Tech Stack

### 📱 Frontend Client
* **Framework:** React + Vite
* **Styling:** Tailwind CSS
* **QR Rendering:** `qrcode.react`
* **Realtime updates:** HTTP synchronization for faculty rosters and projector codes

### ⚙️ Backend API
* **Framework:** Python (FastAPI with `async/await`)
* **Security & Token Generation:** `pyotp` (Time-based One-Time Password / TOTP)
* **ORM:** SQLAlchemy

### 🗄️ Database & Hosting
* **Database:** PostgreSQL
* **Deployment Platform:** [Zerops (ZCP)](https://zerops.io/)

---

## 🗄️ Database Schema Overview (PostgreSQL)

SmartRoll uses SQLAlchemy ORM connected to a PostgreSQL database with the following primary relational structures:

```text
  ┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
  │      Users       │          │     Sessions     │          │  AttendanceLogs  │
  ├──────────────────┤          ├──────────────────┤          ├──────────────────┤
  │ id (PK)          │ 1     *  │ id (PK)          │ 1     *  │  id (PK)         │
  │ name             │───────── ┤ teacher_id (FK)  │───────── ┤ session_id (FK)  │
  │ email            │          │ totp_secret      │          │ student_id (FK)  │
  │ role             │          │ is_active        │          │ timestamp        │
  └──────────────────┘          └──────────────────┘          └──────────────────┘
```

⚬	Users: Stores profiles for Teachers and Students.
⚬	Sessions: Tracks active classroom instances and stores secret keys used for dynamic 30-second TOTP generation.
⚬	AttendanceLogs: Records timestamped check-in entries, preventing duplicate scans per student/session.

####  1. Frontend Config (zerops.yaml in Frontend Repo)
```yaml
zerops:
  - setup: frontend
    build:
      base: nodejs@20
      buildCommands:
        - npm install
        - npm run build
      deployFiles:
        - dist/~
    run:
      base: static
```

#### 2. Backend & PostgreSQL Config (zerops.yaml in Backend Repo)
```yaml
zerops:
  - setup: backend
    build:
      base: python@3.11
      buildCommands:
        - pip install -r requirements.txt
      deployFiles:
        - .
    run:
      base: python@3.11
      start: uvicorn main:app --host 0.0.0.0 --port 8000
      envVariables:
        DATABASE_URL: ${db_connectionString}

```


## 💻 Local Setup & Installation

Prerequisites
Node.js (v18+) & Python (v3.10+)
PostgreSQL installed and running locally

Step 1: Backend Setup

```bash
git clone https://github.com/hariprasad2512/smartroll-backend.git
cd smartroll-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/smartroll" > .env
echo "GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com" >> .env
echo "FACULTY_EMAILS=you@example.com" >> .env
python -m uvicorn main:app --reload --port 8000
```

Create a Google OAuth Web application client ID and authorize the frontend origin (usually `http://localhost:3000`). The same client ID must be set in the frontend's `VITE_GOOGLE_CLIENT_ID` and backend's `GOOGLE_CLIENT_ID`. Only addresses in `FACULTY_EMAILS` can open the faculty dashboard; any other verified Google account self-enrolls as a student.


Step 2: Frontend Setup

```bash
git clone https://github.com/hariprasad2512/smartroll-frontend.git
cd smartroll-frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
echo "VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com" >> .env
npm run dev
```



<p align="center"> Built with ❤️ in the Zerops Challenge 2026 by @WeMakeDevs </p>
