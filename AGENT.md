# Agent Instructions

## Mission

Help build and maintain a Bulgarian-market marketplace that connects short-term rental hosts with verified cleaners.

The product direction for v1 is:

- Responsive web/PWA.
- Public landing page first, with marketplace operations behind authenticated app screens later.
- Session-cookie authentication with manual admin approval for v1.
- Django REST Framework backend.
- React/Next.js frontend.
- PostgreSQL, Redis, and Celery.
- Bulgarian and English UI.
- EUR currency.
- Verified cleaners.
- Agency accounts that invite separate cleaner users into agency groups.
- Consent-first cookie handling for optional analytics and marketing cookies.
- Single cleaning and monthly batch posting.
- Google Calendar sync and iCal import/export.
- Two-way reviews.
- No in-app payments in v1.

## Working Rules

- Treat `BUSINESS.md` as the source of truth for business strategy, target users, marketplace assumptions, monetization hypotheses, and open business questions.
- Preserve the service-ready modular architecture described in `architecture.md`.
- Keep the unauthenticated `/` frontend experience as a public marketing/lead-generation landing page, not an internal dashboard.
- Keep changes scoped to the user request.
- Do not introduce unrelated refactors.
- Do not add payment processing, payouts, wallets, invoices, or platform fees unless the user explicitly asks for that change.
- Prefer explicit business services for workflows instead of burying state transitions in API views.
- Keep calendar behavior centered on the internal app calendar as the source of truth.
- Keep Bulgarian-market assumptions visible: BG/EN, EUR, `Europe/Sofia`, verified cleaners, no in-app payments, two-way reviews.

## Documentation Rules

Update docs in the same change when altering:

- Business strategy, target users, monetization assumptions, launch strategy, or success metrics.
- Architecture boundaries.
- Business workflows.
- Data model concepts.
- API routes or behavior.
- Local development commands.
- Test commands.
- External integrations.
- Deployment assumptions.

Use:

- `README.md` for project overview and quick-start entry points.
- `BUSINESS.md` for business strategy, target market, user segments, monetization hypotheses, success metrics, risks, and open business questions.
- `DEV.md` for developer setup and project operating instructions.
- `architecture.md` for technical architecture and domain boundaries.
- `AGENT.md` for agent-specific working rules.

When documents overlap, use this priority:

- `BUSINESS.md` decides what the business is trying to achieve and which assumptions are locked.
- `architecture.md` decides how the system is structured technically.
- `DEV.md` decides how developers run and maintain the project.
- `AGENT.md` decides how agents should work inside the repository.

## Code Quality Rules

When code exists:

- Add or update tests for business logic, API behavior, migrations, permissions, and background tasks.
- Keep migrations intentional and reviewable.
- Avoid cross-domain imports that bypass service boundaries.
- Prefer typed, explicit interfaces for shared workflow inputs.
- Make background jobs idempotent where possible.
- Handle external calendar and notification failures explicitly.
- Keep secrets out of source control.
- Do not run `npm run build` while `npm run dev` is running against the same `frontend/.next` directory; stop dev or clear `.next` first to avoid stale Next.js runtime errors.

## Marketplace Rules To Preserve

- Cleaners must be verified before applying for marketplace jobs.
- Users must be approved before full marketplace rights are enabled.
- Agencies must assign accepted agency jobs only to active member cleaners.
- Hosts can post one cleaning or a monthly batch.
- Cleaners apply; hosts accept or reject.
- Price can be proposed or agreed in the app, but payment is handled outside the platform in v1.
- A cleaning job can have only one accepted cleaner assignment.
- Reviews are two-way and only allowed after job completion.
- Admins must be able to inspect marketplace history for disputes and moderation.

## Current Implementation State

### Backend — complete for v1 domain logic

- Modular Django/DRF monolith under `backend/`.
- All domain apps wired: `accounts`, `properties`, `marketplace`, `calendars`, `feedback`, `notifications`.
- Session-cookie auth with CSRF enforcement (`ensure_csrf_cookie` on all auth views, `X-CSRFToken` required on state-changing requests).
- Account approval states and admin approve/reject/suspend actions fully working.
- Agency profiles, invitations, memberships, and member assignment fully working.
- Property CRUD, cleaning job CRUD, batch CRUD, application workflow, assignment, completion, two-way reviews all implemented in service layer.
- Notification records exist; email/SMS/provider dispatch is a placeholder.
- Calendar conflict API exists; Google Calendar sync and iCal parsing are placeholders.

### Frontend — what exists

**`frontend/lib/api.ts`** — all API calls must go through `apiFetch`. It:
- Adds `Content-Type: application/json` when a body is present.
- Reads `csrftoken` cookie and adds `X-CSRFToken` header on POST/PUT/PATCH/DELETE.
- Returns raw `Response` — callers check `.ok` and call `.json()`.

**`frontend/next.config.mjs`** — critical config:
- `trailingSlash: true` — required so Next.js does not strip slashes before Django sees them.
- Two rewrite rules matching `/api/:path*/` and `/api/:path*` — required to preserve trailing slashes through to Django's `APPEND_SLASH`.

**`frontend/app/page.tsx`** — public landing page:
- Auth-aware header: shows role-correct dashboard link (`/admin` for admins, `/host` for hosts, `/app` for others) when logged in; shows "Log in" when not.
- Search form uses local state only — not connected to real backend yet.

**`frontend/app/login/page.tsx`** — session login, redirects to `/` after success.

**`frontend/app/signup/page.tsx`** — role-based signup (host / cleaner / agency), redirects to `/app` after success.

**`frontend/app/app/page.tsx`** — generic workspace:
- Auto-redirects: hosts → `/host`, admins → `/admin`.
- For cleaners/agencies: shows account status (pending / approved / rejected / suspended).

**`frontend/app/admin/page.tsx`** — admin approval panel:
- Gate: redirects to `/login` if unauthenticated, shows "Admin only" if not admin role.
- Fetches `GET /api/accounts/users/` (all accounts, filtered client-side).
- Three filters: pending / approved / all.
- Approve: `POST /api/accounts/users/{id}/approve/` — updates local state immediately.
- Reject: `POST /api/accounts/users/{id}/reject/` — updates local state immediately.

**`frontend/app/host/page.tsx`** — host dashboard:
- Gate: redirects to `/login` if unauthenticated, shows "Hosts only" if not host role.
- Pending hosts see a gold banner but can still view the UI.
- **Properties section**: lists properties as cards with job counts and default settings. "Add property" opens a modal that POSTs to `POST /api/properties/properties/`.
- **Jobs & Calendar section**:
  - Month calendar (custom 7-column CSS grid, Mon–Sun), prev/next navigation.
  - Coloured dots per day: grey (draft), teal (open), gold (assigned), green (done), red (cancelled), orange (disputed).
  - Clicking an empty day pre-fills the job form with that date.
  - Clicking a day with jobs filters the list panel to that day.
  - Job list panel shows: title, property, time range, status badge, price, Publish button for drafts.
  - "Post a job" modal POSTs to `POST /api/marketplace/jobs/` — saved as Draft.
  - Publish button calls `POST /api/marketplace/jobs/{id}/publish/` — transitions Draft → Open.

### What is NOT built yet (next priorities)

1. **`/cleaner` dashboard** — cleaner profile view, browse open jobs, apply for a job (`POST /api/marketplace/applications/`).
2. **Applications panel in host dashboard** — host sees applications per job, calls `POST /api/marketplace/applications/{id}/accept/`.
3. **`/agency` dashboard** — agency manages members, views assigned jobs.
4. **Cleaner verification** — admin marks cleaner as verified before they can apply.
5. **Real search on landing page** — connect to `GET /api/accounts/cleaners/` with location filter.
6. **Calendar integrations** — iCal import, Google Calendar sync (backend placeholders exist).

## Before Making Changes

Check the current repository state and read the relevant docs first. For product, marketplace, launch, monetization, or success-metric changes, read `BUSINESS.md` before proposing or editing technical implementation.

If Git reports a safe-directory ownership warning, do not work around it destructively. The developer may need:

```powershell
git config --global --add safe.directory C:/Users/35987/Desktop/airbnb_tax
```

Only run commands that match the current project state. This repository may contain documentation before it contains application scaffolding.

## Handoff Expectations

Every substantial change should end with:

- What changed.
- What tests or checks were run.
- Any commands that failed and why.
- Any follow-up work that is genuinely needed.
