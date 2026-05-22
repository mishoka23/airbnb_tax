# Host Cleaner Marketplace

Marketplace for Bulgarian short-term rental hosts, verified cleaners, and cleaning agencies.

The MVP focuses on job posting, monthly cleaning batches, cleaner applications, assignment, shared calendar coordination, notifications, and two-way feedback. Payments are intentionally out of scope for v1.

## Documentation

- `BUSINESS.md`: business strategy, target market, monetization hypotheses, risks, and open questions.
- `architecture.md`: technical architecture and domain boundaries.
- `DEV.md`: development setup and operating guide.
- `AGENT.md`: instructions for AI and developer agents.

## Stack

- Backend: Django, Django REST Framework, PostgreSQL, Redis, Celery.
- Frontend: Next.js responsive web/PWA.
- Local infrastructure: Docker Compose with PostgreSQL, Redis, backend, worker, and frontend services.

## Quick Start

Copy environment defaults:

```powershell
Copy-Item .env.example .env
```

Run the full local stack:

```powershell
docker compose up --build
```

Default URLs:

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:8000/api/health/`
- Django admin: `http://localhost:8000/admin/`

## Current Implementation Status

### Backend (complete for v1 domain logic)

- Django project and domain apps (`accounts`, `properties`, `marketplace`, `calendars`, `feedback`, `notifications`).
- Session-cookie signup, login, logout, and current-user APIs with CSRF enforcement.
- Account approval states (pending / approved / rejected / suspended) and admin approve/reject/suspend actions.
- Agency profiles, invitations, memberships, and delegated cleaner assignments.
- Cookie consent records for optional analytics and marketing cookies.
- Property management: CRUD, external calendar connections, reservations.
- Marketplace service functions: publish jobs, submit applications, accept applications, complete jobs, two-way reviews.
- Notification records and placeholder Celery tasks.
- Calendar conflict API and placeholder sync tasks.

### Frontend (Next.js App Router)

| Route | Status | Description |
|---|---|---|
| `/` | ✅ Done | Public landing page — auth-aware header with role-based dashboard link |
| `/login` | ✅ Done | Session login |
| `/signup` | ✅ Done | Role-based signup (host / cleaner / agency) |
| `/app` | ✅ Done | Generic workspace — auto-redirects hosts → `/host`, admins → `/admin` |
| `/admin` | ✅ Done | Admin approval dashboard — list / filter / approve / reject accounts |
| `/host` | ✅ Done | Host dashboard — property CRUD, job posting, month calendar view, publish jobs |
| `/cleaner` | ⬜ Not built | Cleaner dashboard — profile, browse open jobs, apply |
| `/agency` | ⬜ Not built | Agency dashboard — manage members, view assigned jobs |

### Shared infrastructure

- `frontend/lib/api.ts` — `apiFetch` wrapper with automatic CSRF token injection and `Content-Type`.
- `frontend/next.config.mjs` — `trailingSlash: true` + dual rewrite rules for Django `APPEND_SLASH` compatibility.
- `frontend/app/globals.css` — CSS design tokens and shared component classes (see DEV.md for details).
