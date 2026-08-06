# Havenly — Real Estate Marketplace

Havenly is a polished full-stack property marketplace built as a production-minded portfolio project. Visitors can explore homes without registering, compare local market statistics, and connect with listing agents. Approved agents manage their own portfolio and inquiries while administrators moderate the marketplace and agent network.

## Product highlights

- Premium responsive home, property collection, and gallery-led detail experiences
- Keyword search plus city, purpose, property type, price, bedroom, bathroom, area, and sorting support
- Secure JWT registration/login and role-based API authorization
- Saved properties and property-specific inquiries for registered users
- Moderated agent application flow—users cannot self-assign the agent role
- Agent workspace for portfolio CRUD, view statistics, and read/unread inquiries
- Administrator workspace for platform statistics, users, listings, and application decisions
- Database-derived market snapshots, city comparisons, and replaceable demonstration trend data
- Convincing seed dataset spanning agents, users, cities, property types, amenities, applications, and messages

## Stack and architecture

| Layer | Technology | Structure |
|---|---|---|
| Web | React, TypeScript, Vite, Tailwind CSS, React Router | Pages, reusable components, layouts, context, typed API service |
| API | Python, Flask, Flask-JWT-Extended | Application factory, blueprints, authorization helpers, models, seed command |
| Data | PostgreSQL, SQLAlchemy, Alembic | Normalized relational schema with constraints, indexes, timestamps, and migrations |

The frontend and API deploy independently. Configuration comes from environment variables; secrets and deployment URLs are not embedded in source code.

## Local development

Prerequisites: Node.js 22+, Python 3.13+, and PostgreSQL 15+.

### API

```powershell
Copy-Item backend/.env.example backend/.env
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
cd backend
.venv/Scripts/flask --app run.py db upgrade
.venv/Scripts/flask --app run.py seed
.venv/Scripts/flask --app run.py run --debug
```

Set `DATABASE_URL` in `backend/.env` to a PostgreSQL SQLAlchemy URL such as:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/havenly
SECRET_KEY=generate-a-long-random-secret
JWT_SECRET_KEY=generate-a-different-long-random-secret
FRONTEND_URL=http://localhost:5173
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend

```powershell
Copy-Item frontend/.env.example frontend/.env
cd frontend
npm install
npm run dev
```

`VITE_API_URL` defaults to `http://localhost:5000/api`.

### Docker Compose

```powershell
docker compose up --build
docker compose exec api flask --app run.py seed
```

Open `http://localhost:5173`.

## Demonstration accounts

All seeded accounts use `Password123!`.

| Role | Email |
|---|---|
| Administrator | `admin@havenly.test` |
| Agent | `agent@havenly.test` |
| User | `user@havenly.test` |
| Pending applicant | `applicant@havenly.test` |

These credentials are demonstration data only and must not be used in production.

## API organization

- `/api/auth` — registration, login, current identity
- `/api/properties` — public discovery and property details
- `/api/account` — profile, favorites, inquiries, agent application
- `/api/agent` — agent-owned listings, metrics, and inquiry inbox
- `/api/admin` — platform moderation and application decisions
- `/api/market` — aggregate market snapshots and trend series

Ownership and role checks are enforced in the API. Hiding a frontend route is never treated as authorization.

## Quality checks

```powershell
backend/.venv/Scripts/python -m pytest backend/tests -q
cd frontend
npm run build
```

The backend tests cover authentication, role denial, agent listing creation, cross-agent ownership protection, and administrator promotion workflow. The frontend production command performs strict TypeScript compilation before bundling.

## Deployment notes

- Run `flask --app run.py db upgrade` as a release step.
- Use managed PostgreSQL and set `DATABASE_URL` at runtime.
- Build the frontend with the deployed `VITE_API_URL`; Vite values are embedded during compilation.
- Set unique, high-entropy `SECRET_KEY` and `JWT_SECRET_KEY` values.
- Serve the API behind HTTPS and restrict `FRONTEND_URL` to the deployed web origin.
- External image storage can replace URL-based demonstration images without changing the property/image relationship.

## Portfolio presentation

Recommended screenshots: Home hero, filtered property collection, property gallery, Market Insights, Agent My Properties, Agent Messages, and Administrator Agent Applications. Add final hosted URLs and screenshots after deployment; deployment itself is intentionally outside the initial product build.

Market trend history is explicitly marked as demonstration data and is structured behind a dedicated endpoint so a real historical provider can replace it later. Market observations are informational and are not financial advice.
