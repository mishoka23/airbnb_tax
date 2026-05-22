# Development Guide

## Project Purpose

This project is a Bulgarian-market marketplace for connecting Airbnb and short-term rental hosts with verified cleaners.

The MVP should let hosts post one cleaning or a month of cleaning jobs, let verified cleaners apply, let both sides agree on price outside the platform, share calendar availability, and collect two-way feedback after completed work.

## MVP Scope

The first production version should include:

- Property owner (`host`), cleaner, agency, and admin user roles.
- Session-cookie signup/login/logout/current-user APIs.
- Manual admin approval before marketplace rights are enabled.
- Agency invitations and agency-cleaner memberships.
- Consent-first cookie recording for optional analytics and marketing cookies.
- Host property management.
- Single cleaning job posting.
- Monthly cleaning batch creation from reservations or manual dates.
- Cleaner verification before marketplace access.
- Cleaner applications to individual jobs or monthly batches.
- Assignment workflow after host approval.
- Agreed price tracking in EUR without in-app payments.
- Internal calendar as the source of truth.
- Google Calendar sync plus iCal import/export.
- Email, in-app, and SMS notifications for important workflow events.
- Two-way reviews after completed jobs.
- Admin moderation for cleaners, reviews, disputes, and marketplace activity.

Out of scope for v1 unless explicitly requested:

- In-app payments, payouts, invoices, platform fees, or wallet balances.
- Native mobile apps.
- Property management system integrations such as Guesty or Hostaway.
- Advanced operations such as supplies inventory, photo inspections, or damage claim workflows.

## Expected Stack

Use this baseline stack unless the architecture document is intentionally updated:

- Backend: Python, Django, Django REST Framework.
- Frontend: React with Next.js as a responsive web/PWA.
- Database: PostgreSQL.
- Cache and broker: Redis.
- Background jobs: Celery.
- Object storage: EU-hosted S3-compatible storage for future uploaded assets.
- Hosting: EU managed cloud infrastructure.
- Timezone: `Europe/Sofia`.
- Currency: EUR.
- Languages: Bulgarian and English.

## Repository State

This repository contains the first application scaffold:

- `backend/`: Django project, Django REST Framework APIs, domain apps, service-layer workflows, initial migrations, and tests.
- `frontend/`: Next.js responsive web/PWA with a public landing page. Authenticated dashboards are not built yet.
- `docker-compose.yml`: PostgreSQL, Redis, backend, Celery worker, and frontend local stack.
- `.env.example`: local environment defaults.

## Local Development Conventions

Current layout:

```text
backend/
  config/
  apps/
frontend/
  app/
  lib/
docker-compose.yml
.env.example
```

Keep the backend modular even before services are split. Each backend domain should own its models, serializers, services, permissions, tests, and migrations.

Prefer explicit service-layer functions for business workflows such as accepting applications, assigning cleaners, completing jobs, and submitting reviews. Avoid putting marketplace state transitions directly inside views.

## Environment Setup

Copy the example environment file before using Docker Compose:

```powershell
Copy-Item .env.example .env
```

The Docker environment uses PostgreSQL and Redis. When running the backend directly without `DATABASE_URL`, Django falls back to local SQLite for lightweight development checks.

The root `requirements.txt` is a project-level overview. It includes `backend/requirements.txt` for Python installation and documents the non-Python technology requirements in comments.

## Docker Development

Run the full local stack:

```powershell
docker compose up --build
```

Useful service URLs:

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:8000/api/health/`
- Django admin: `http://localhost:8000/admin/`

Run backend commands through Docker:

```powershell
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py createsuperuser
docker compose run --rm backend python manage.py test
```

## Backend Local Commands

From `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Run tests and checks:

```powershell
python manage.py check
python manage.py test
python -m compileall .
```

Run a Celery worker after Redis is available and dependencies are installed:

```powershell
celery -A config worker --loglevel=info
```

## Frontend Local Commands

From `frontend/`:

```powershell
npm.cmd install
npm.cmd run dev -- --hostname 127.0.0.1
```

Run frontend checks:

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

PowerShell may block `npm.ps1` with an execution policy error. Use `npm.cmd` commands on Windows to avoid changing execution policy.

Do not run `npm.cmd run build` while `npm.cmd run dev` is running. Both write to `frontend/.next`, and running them together can produce missing generated files such as `.next/server/app/page.js`. If the frontend shows a stale Next.js runtime error, stop the dev server, remove `.next`, and restart:

```powershell
cd C:\Users\35987\Desktop\airbnb_tax\frontend
Remove-Item -Recurse -Force .next
npm.cmd run dev -- --hostname 127.0.0.1
```

## Current Frontend Behavior

### Routing overview

| Route | Purpose |
|---|---|
| `/` | Public landing page — auth-aware header |
| `/login` | Session login |
| `/signup` | Role-based signup |
| `/app` | Generic workspace — auto-redirects hosts and admins |
| `/admin` | Admin account approval panel |
| `/host` | Host property and job management with calendar |
| `/cleaner` | **Not built** — cleaner dashboard |
| `/agency` | **Not built** — agency dashboard |

### Key frontend files

**`frontend/lib/api.ts`** — all HTTP calls go through `apiFetch`. Handles CSRF automatically.
Do not call `fetch` directly in any page — always use `apiFetch`.

**`frontend/next.config.mjs`** — has `trailingSlash: true` and two rewrite rules for `/api/:path*`. Do not simplify to one rewrite rule — Django's `APPEND_SLASH` requires both forms.

**`frontend/app/globals.css`** — single CSS file for the entire app. All new pages should add their styles here following existing naming conventions (`.host-*`, `.admin-*`, etc.).

### Landing page (`/`)

- Audience toggle for hosts and cleaners.
- Search-style lead form with city, month, and property/capacity inputs.
- Local demo results only — not yet connected to backend cleaner search.
- Auth-aware header: when logged in, shows the correct dashboard link for the current role.

### Admin panel (`/admin`)

- Lists all user accounts with client-side filtering by status (pending / approved / all).
- Approve or reject pending accounts with instant local state update.
- Accessible to `admin` role only — redirects others.

### Host dashboard (`/host`)

- Two sections toggled in the topbar: **Properties** and **Jobs & Calendar**.
- Properties section: add property via modal form (`POST /api/properties/properties/`).
- Jobs section: month calendar grid with coloured status dots per day.
  - Click an empty day → job form pre-filled with that date.
  - Click a day with jobs → filters the list panel to that day.
  - Post a job via modal form (`POST /api/marketplace/jobs/`) — saved as Draft.
  - Publish button: `POST /api/marketplace/jobs/{id}/publish/` → transitions to Open.
- Pending hosts see a gold warning banner but can still view the UI.

### CSS conventions

All pages use plain CSS in `frontend/app/globals.css`. No external CSS libraries.

CSS variable reference:
```
--brand: #ff385c    primary CTA colour
--teal: #008489     trust, cleaner, success
--gold: #b7791f     warnings, ratings, assigned
--ink: #111111      strong headings
--muted: #6a6a6a    secondary text
--line: #dddddd     borders
--surface: #ffffff  card backgrounds
--radius: 8px
```

Naming conventions:
- Public landing: no prefix, or `.hero-*`, `.section`, `.trust-*`, `.join-*`
- Auth pages: `.auth-*`
- Generic workspace: `.app-*`
- Admin panel: `.admin-*`
- Host dashboard: `.host-*`
- Modals: `.host-modal-backdrop` → `.host-modal` → `.host-modal-header` + `.host-form`

When building a new role dashboard (cleaner, agency), follow the host pattern:
1. Create `frontend/app/{role}/page.tsx` with auth gate, role check, and data fetch.
2. Add `.{role}-*` CSS classes to the bottom of `globals.css` following the same structure as `.host-*`.
3. Update the redirect in `frontend/app/app/page.tsx` to redirect that role.
4. Update the header link in `frontend/app/page.tsx` for that role.

## Current Backend Behavior

The backend has initial domain models, migrations, admin registrations, serializers, viewsets, and service functions.

Implemented service-level behavior:

- Signup, login, logout, and current-user APIs using Django sessions.
- Pending, approved, rejected, and suspended account status.
- Admin approval, rejection, and suspension actions.
- Agency profile, invitation, membership, and member assignment APIs.
- Cookie consent records for essential, analytics, and marketing choices.
- Publish draft cleaning jobs.
- Allow approved, verified cleaners and approved agencies to apply to open jobs.
- Allow hosts/admins to accept one application.
- Allow assigned agencies to delegate accepted work to active member cleaners.
- Reject competing applications after assignment.
- Mark assigned jobs completed.
- Allow two-way reviews only after completion.
- Update cleaner rating summaries after reviews.

Provider integrations are not complete yet:

- Google Calendar sync is a placeholder.
- iCal parsing is a placeholder.
- Email/SMS dispatch is a placeholder.
- Object storage is planned for future file/photo/document uploads.

## Git Setup Note

This workspace has reported a Git safe-directory ownership warning. If Git commands fail locally with `detected dubious ownership`, the developer or agent may need to run:

```powershell
git config --global --add safe.directory C:/Users/35987/Desktop/airbnb_tax
```

Only run that command after confirming it is appropriate for the current machine and user account.

## Testing Expectations

When code exists, test coverage should focus on:

- Job lifecycle transitions.
- Cleaner verification and permissions.
- Application and assignment rules.
- Calendar conflict detection.
- Google Calendar and iCal sync behavior.
- Notification triggers.
- Review eligibility and two-way review constraints.
- Admin moderation actions.

Every change to business logic, data models, API permissions, migrations, or background tasks should include tests or a clear explanation for why tests were not added.

## Documentation Expectations

Update documentation in the same change when modifying:

- Business strategy, target users, marketplace assumptions, monetization hypotheses, launch strategy, or success metrics.
- Architecture boundaries.
- User workflows.
- Data model concepts.
- API behavior.
- Local development commands.
- Deployment assumptions.
- External integrations.

Documentation roles:

- `BUSINESS.md` defines the business strategy, target market, value proposition, marketplace model, monetization hypotheses, success metrics, risks, and open business questions.
- `architecture.md` defines technical architecture, domain boundaries, data concepts, integrations, and future service extraction.
- `DEV.md` defines developer setup, project conventions, expected stack, and maintenance expectations.
- `AGENT.md` defines how AI and developer agents should work in the repository.
