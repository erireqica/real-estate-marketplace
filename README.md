<div align="center">

# 🏡 Havenly

### Full-stack real estate marketplace

A responsive property platform with public listings, market insights, saved homes, messaging, agent tools, and admin moderation.

**[Live website](https://havenly-property.vercel.app)** · **[GitHub repository](https://github.com/erireqica/real-estate-marketplace)** · **[API health](https://havenly-api.onrender.com/api/health)**

> **Demo note:** the backend is hosted on a free Render instance, so the first request after a period of inactivity can take a little longer while the service wakes up. Check API health for live updates.

</div>

---

## 🌐 Overview

Havenly is a full-stack real estate marketplace built with **React, TypeScript, Flask, and PostgreSQL**.

The public side focuses on property discovery and market context. Registered users can save homes and speak directly with listing agents. Approved agents manage their own listings and conversations through a dedicated workspace, while administrators manage users, properties, and agent applications.

The application is deployed as three separate services:

**Vercel** for the frontend · **Render** for the Flask API · **Neon** for PostgreSQL

<p align="center">
  <img src="docs/screenshots/Home.png" alt="Havenly home page" width="100%">
</p>

---

## ✨ At a glance

| Area | What it includes |
|---|---|
| **Property discovery** | Search, filtering, sorting, galleries, amenities, pricing, location and agent details |
| **User accounts** | JWT authentication, saved homes, profile settings, password changes and conversations |
| **Agent workspace** | Listing management, property statistics, recent listings and client messaging |
| **Admin workspace** | User management, property moderation, agent assignment and application review |
| **Market insights** | Database-derived market statistics, city breakdowns and demonstration price trends |

---

## 🌍 Public experience

Visitors can browse active listings without creating an account. The property collection supports keyword search, city, sale/rent, property type, price range, bedrooms, bathrooms, minimum area and sorting.

Each property has a dedicated detail page with an image gallery, location, price, specifications, amenities and listing-agent information.

The **Market Insights** section uses live listing data from PostgreSQL to calculate figures such as average price, average price per square metre, listing distribution and city-level breakdowns.

<p align="center">
  <img src="docs/screenshots/Properties.png" alt="Havenly property search and listings" width="49%">
  <img src="docs/screenshots/PropertyDetails.png" alt="Havenly property details page" width="49%">
</p>

<p align="center">
  <img src="docs/screenshots/MarketInsights.png" alt="Havenly Market Insights dashboard" width="100%">
</p>

---

## 💬 Accounts and messaging

Authentication uses access and refresh JWTs, with account state restored on the frontend when a session is still valid.

Registered users can save properties, edit their profile, change their password and start a conversation from a property page. Conversations stay linked to the specific property and agent, with reply history and unread-message indicators.

Users can also apply to become an agent. Applications include profile information, optional agency details and a PDF CV. Approval is handled by an administrator rather than by allowing users to assign themselves a higher role.

---

## 🧑‍💼 Agent workspace

Approved agents get a separate dashboard for their own portfolio.

They can create, edit and delete listings, manage listing status, update property details, amenities and images, and view basic performance information such as property views and unread messages.

Property ownership is enforced in the API, so an agent cannot modify another agent's listing by calling the backend directly.

<p align="center">
  <img src="docs/screenshots/AgentDashboard-properties.png" alt="Havenly agent property management" width="49%">
  <img src="docs/screenshots/AgentDashboard-messages.png" alt="Havenly agent messaging workspace" width="49%">
</p>

---

## 🛡️ Admin workspace

Administrators can manage the wider marketplace from a separate dashboard.

They can view platform statistics, manage users, enable or disable accounts, change eligible users between User and Agent roles, create properties for agents, edit or remove any listing, reassign listing ownership and review agent applications.

Approving an application promotes the linked user account to the Agent role.

<p align="center">
  <img src="docs/screenshots/AdminDashboard-applications.png" alt="Havenly Admin dashboard applications" width="100%">
</p>

---

## 🧠 Architecture

```text
┌──────────────────────────────┐
│           Vercel             │
│   React + TypeScript + Vite  │
└──────────────┬───────────────┘
               │ HTTPS / JSON
               ▼
┌──────────────────────────────┐
│           Render             │
│        Flask REST API        │
│     JWT + SQLAlchemy         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│            Neon              │
│         PostgreSQL           │
│     Alembic migrations       │
└──────────────────────────────┘
```

The frontend and backend are deployed independently. Production URLs, secrets and database credentials are provided through environment variables rather than committed to the repository.

---

## 🛠 Tech stack

| Frontend | Backend | Data & deployment |
|---|---|---|
| React | Python | PostgreSQL |
| TypeScript | Flask | Neon |
| Vite | Flask-SQLAlchemy | Alembic |
| React Router | Flask-JWT-Extended | Docker |
| Tailwind CSS | Flask-CORS | Docker Compose |
| Lucide React | Gunicorn | Vercel / Render |

---

## 🗃 Data model

The main relationships are kept intentionally relational:

```text
User
├── Properties
├── Favorites
├── Agent Applications
└── Conversations

Property
├── Property Images
├── Amenities
├── Favorites
└── Conversations

Conversation
└── Conversation Messages
```

The schema includes unique constraints, indexed lookup fields, timestamps, positive price/area checks, foreign keys and ownership relationships.

---

## 🧪 Demo data

The repository includes repeatable fictional seed data so the application is populated immediately after setup.

Current seed content:

| Data | Count |
|---|---:|
| Users | 12 |
| Approved agents | 5 |
| Properties | 28 |
| Property images | 50 |
| Favorites | 22 |
| Conversations | 9 |
| Messages | 35 |
| Agent applications | 3 |

The seed is repeatable and is scoped to fictional `@havenly.test` accounts so normal user data is not intentionally replaced.

### 🔑 Demo accounts

All demo accounts use:

```text
Password123!
```

| Role | Email |
|---|---|
| Administrator | `admin@havenly.test` |
| Agent | `agent@havenly.test` |
| Agent | `drita@havenly.test` |
| User | `user@havenly.test` |
| Pending applicant | `applicant@havenly.test` |

---

## 🔌 API structure

The Flask API is split into focused blueprints:

```text
/api/auth
/api/properties
/api/account
/api/agent
/api/admin
/api/market
```

Sensitive actions are protected in the backend through authenticated-user checks, role checks and listing-ownership checks.

---

## ✅ Testing

The backend currently includes **19 automated tests** covering the main application flows and production database configuration.

The tests cover areas such as authentication, role restrictions, property ownership, admin actions, favorites, conversations, unread messages, password changes, agent applications, seed repeatability and Neon connection handling.

Frontend checks:

```bash
npm run lint
npm run build
```

Backend checks:

```bash
pytest
```

---

## 💻 Run locally

### Requirements

- Node.js 22+
- Python 3.13+
- PostgreSQL 15+

Clone the repository:

```bash
git clone https://github.com/erireqica/real-estate-marketplace.git
cd real-estate-marketplace
```

### Backend

Create the environment file:

```powershell
Copy-Item backend/.env.example backend/.env
```

Example:

```dotenv
APP_ENV=development
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/havenly
SECRET_KEY=replace-with-a-long-random-value
JWT_SECRET_KEY=replace-with-a-different-long-random-value
FRONTEND_URL=http://localhost:5173
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Install dependencies and prepare the database:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt

cd backend
.venv/Scripts/flask --app run.py db upgrade
.venv/Scripts/flask --app run.py seed
.venv/Scripts/flask --app run.py run --debug
```

### Frontend

In another terminal:

```powershell
Copy-Item frontend/.env.example frontend/.env
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

---

## 🐳 Docker

The project also includes a complete Docker Compose setup with PostgreSQL, Flask and the built frontend.

```bash
docker compose up --build
docker compose exec api flask --app run.py seed
```

Then open:

```text
http://localhost:5173
```

---

## 🚀 Deployment notes

Production uses:

- **Vercel** — frontend
- **Render** — Flask API
- **Neon** — PostgreSQL

The production Flask configuration requires `DATABASE_URL`, keeps Neon SSL parameters intact, uses psycopg 3, and enables connection pre-ping / recycling to reduce stale connections after database idle periods.

Alembic migrations run before Gunicorn starts, and Vercel is configured to rewrite SPA routes to `index.html` so direct visits and refreshes work correctly with React Router.

---

## 📁 Project structure

```text
real-estate-marketplace/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── authz.py
│   │   ├── config.py
│   │   ├── errors.py
│   │   ├── extensions.py
│   │   └── seed.py
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vercel.json
│
├── docker-compose.yml
└── README.md
```

---

<div align="center">

**[Open Havenly](https://havenly-property.vercel.app)**

</div>
