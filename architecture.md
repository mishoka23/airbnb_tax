# Architecture

## Overview

The application is a service-ready modular marketplace for Bulgarian Airbnb and short-term rental hosts who need reliable cleaners.

The v1 architecture should start as a modular Django backend with a Next.js PWA frontend. This keeps the first build practical while preserving clear domain boundaries that can later be extracted into independently deployed microservices.

The app calendar is the source of truth. External calendars, including Google Calendar and iCal feeds from Airbnb or booking platforms, sync into or out of the application.

The current first screen is a public landing page for the service. Authenticated host, cleaner, and admin workspaces should be built as separate app routes after authentication is introduced.

## Architecture Style

Use a modular monolith for v1:

- One deployable backend API.
- One primary PostgreSQL database.
- Redis for cache, locks, and Celery broker/result needs.
- Celery workers for asynchronous sync and notification work.
- One Next.js frontend serving the public landing page and, later, authenticated host, cleaner, and admin experiences.

The code should be organized around business domains, not technical layers alone. Domain modules should communicate through explicit service functions and events rather than reaching into each other's internals.

Future extraction into microservices should be possible without rewriting core business logic.

Current implementation modules:

- `apps.accounts`: users, host profiles, cleaner profiles, agency profiles, agency invitations, agency memberships, cookie consent, verification state, and role permissions.
- `apps.properties`: host properties, external calendar connections, and reservations.
- `apps.marketplace`: cleaning batches, jobs, applications, assignments, and marketplace workflow services.
- `apps.calendars`: conflict checks and placeholder background sync tasks.
- `apps.feedback`: two-way reviews and cleaner reputation updates.
- `apps.notifications`: in-app notification records and provider dispatch placeholders.

Current frontend implementation:

- `frontend/lib/api.ts`: shared HTTP client. All pages use `apiFetch` — it injects `Content-Type` and reads the Django `csrftoken` cookie to set `X-CSRFToken` on state-changing requests. Never call `fetch` directly.
- `frontend/next.config.mjs`: `trailingSlash: true` + two `/api/:path*` rewrite rules that proxy to the Django backend while preserving trailing slashes for `APPEND_SLASH` compatibility.
- `frontend/app/page.tsx`: public landing page. Auth-aware header shows role-correct dashboard link when a session exists (`/admin` for admins, `/host` for hosts, `/app` for cleaners/agencies). Search form uses local state only — not yet connected to backend.
- `frontend/app/login/page.tsx`: session login — redirects to `/` on success.
- `frontend/app/signup/page.tsx`: role-based signup for host / cleaner / agency — redirects to `/app` on success.
- `frontend/app/app/page.tsx`: generic authenticated workspace. Automatically redirects hosts to `/host` and admins to `/admin`. For cleaners and agencies shows account status.
- `frontend/app/admin/page.tsx`: admin account approval panel. Lists all accounts, filters by pending / approved / all. Approve and reject actions call `POST /api/accounts/users/{id}/approve/` and `/reject/`. Accessible to `admin` role only.
- `frontend/app/host/page.tsx`: host dashboard with two sections toggled in the topbar:
  - **Properties** — lists host properties as cards with job counts. "Add property" modal POSTs to `POST /api/properties/properties/`.
  - **Jobs & Calendar** — custom month calendar grid with coloured status dots per day. "Post a job" modal POSTs to `POST /api/marketplace/jobs/` (saved as Draft). Publish button calls `POST /api/marketplace/jobs/{id}/publish/` to transition Draft → Open.
- `frontend/app/components/CookieConsentBanner.tsx`: consent-first GDPR cookie banner.
- `frontend/app/globals.css`: single CSS file for all routes using plain CSS variables and named component classes. No CSS library.

Not yet built:
- `/cleaner` — cleaner dashboard (profile, browse open jobs, apply for jobs).
- `/agency` — agency dashboard (manage members, view jobs).
- Applications review panel inside the host dashboard.
- Cleaner verification flow in the admin panel.
- Real search connected to the backend cleaner/agency API.

## Product Domains

### Identity and Access

Responsibilities:

- User authentication.
- Property owner, cleaner, agency, and admin roles.
- Django session-cookie authentication with CSRF protection for the v1 web app.
- Account approval states: pending, approved, rejected, and suspended.
- Profile data.
- Cleaner verification status.
- Agency profiles, agency invitations, and agency-cleaner memberships.
- Cookie consent records for essential, analytics, and marketing choices.
- Permissions and role-based API access.

Rules:

- Pending users can log in and complete onboarding, but cannot post jobs, apply for jobs, accept assignments, or assign agency work.
- Property owners are stored with the existing `host` role value and presented in the UI as "Property owner".
- Cleaners who work for an agency remain separate users with their own cleaner profile and calendar.
- Agencies invite cleaners into their group; cleaners accept invitations from their own account.
- Email/SMS code verification is planned but not delivered by providers in v1.

### Hosts and Properties

Responsibilities:

- Host-owned properties.
- Property address and access metadata.
- Cleaning instructions.
- Default cleaning duration and pricing hints.
- Linked external calendars for each property.

### Cleaners

Responsibilities:

- Cleaner profile.
- Service areas.
- Availability.
- Verification state.
- Public rating summary.
- Work preferences.

### Agencies

Responsibilities:

- Agency profile and service areas.
- Cleaner invitations and agency membership management.
- Agency-level job applications.
- Assigning accepted agency work to active member cleaner calendars.

Rules:

- Agencies must be approved before applying for jobs or assigning work.
- Agencies can assign work only to active cleaner members.
- Member cleaners must still have approved accounts and verified cleaner profiles before receiving agency work.

### Marketplace Jobs

Responsibilities:

- Single cleaning job creation.
- Monthly batch creation.
- Job search and filtering.
- Job lifecycle state transitions.
- Assignment rules.
- Agency assignment delegation to an active member cleaner.
- Cancellation and dispute flags.

Recommended job lifecycle:

```text
draft -> open -> assigned -> completed
              -> cancelled
assigned -> disputed
```

Applications exist between `open` and `assigned`. A job should have at most one accepted cleaner assignment.

### Applications

Responsibilities:

- Cleaner applications to jobs or monthly batches.
- Proposed price or note when needed.
- Host acceptance or rejection.
- Application history for audit and admin review.

Payments are not processed in v1. The app may store proposed and agreed EUR amounts for visibility, but money moves outside the platform.

### Calendar

Responsibilities:

- Internal job and availability calendar.
- Reservation import from iCal feeds.
- Google Calendar sync.
- iCal export for hosts and cleaners.
- Conflict detection.
- Reminder scheduling.

Rules:

- Internal calendar is the source of truth for cleaning jobs.
- Use `Europe/Sofia` for default timezone handling.
- Store timestamps in UTC.
- Surface conflicts instead of silently overwriting external events.
- Keep sync failures visible to the affected user and admins.

### Feedback and Reputation

Responsibilities:

- Two-way reviews after completed jobs.
- Host-to-cleaner ratings.
- Cleaner-to-host/property ratings.
- Private issue reporting.
- Admin review and moderation.

Reviews should only be created for completed jobs by parties involved in that job.

### Notifications

Responsibilities:

- In-app notifications.
- Email notifications.
- SMS notifications for urgent workflow events.

Important notification triggers:

- Cleaner application submitted.
- Host accepts or rejects an application.
- Assignment created or cancelled.
- Calendar sync failure.
- Upcoming cleaning reminder.
- Review prompt after completion.

### Admin

Responsibilities:

- Cleaner verification.
- Review moderation.
- Dispute inspection.
- Job and application visibility.
- User support and account status management.

## Core Data Concepts

The first schema should be based around these concepts:

- User account.
- Account approval state.
- Host profile.
- Cleaner profile.
- Cleaner verification.
- Agency profile.
- Agency invitation.
- Agency membership.
- Cookie consent.
- Property.
- External calendar connection.
- Reservation.
- Cleaning job.
- Monthly cleaning batch.
- Cleaner application.
- Assignment.
- Review.
- Notification.
- Audit log.

Use explicit audit logging for important marketplace decisions, including verification changes, application acceptance, assignment cancellation, dispute status changes, and review moderation.

## API Shape

Use REST APIs through Django REST Framework.

Current API route groups:

- `/api/health/`
- `/api/accounts/signup/`
- `/api/accounts/login/`
- `/api/accounts/logout/`
- `/api/accounts/me/`
- `/api/accounts/cookie-consent/`
- `/api/accounts/users/`
- `/api/accounts/hosts/`
- `/api/accounts/cleaners/`
- `/api/accounts/agencies/`
- `/api/accounts/agency-invitations/`
- `/api/accounts/agency-memberships/`
- `/api/properties/properties/`
- `/api/properties/calendar-connections/`
- `/api/properties/reservations/`
- `/api/marketplace/batches/`
- `/api/marketplace/jobs/`
- `/api/marketplace/applications/`
- `/api/marketplace/assignments/`
- `/api/feedback/reviews/`
- `/api/notifications/notifications/`
- `/api/calendars/conflicts/`
- `/admin/`

The exact routes can evolve, but APIs should preserve domain boundaries and avoid leaking internal model structure unnecessarily.

Important account and agency actions:

- `POST /api/accounts/users/{id}/approve/`
- `POST /api/accounts/users/{id}/reject/`
- `POST /api/accounts/users/{id}/suspend/`
- `POST /api/accounts/agencies/{id}/invite-cleaner/`
- `POST /api/accounts/agency-invitations/{id}/accept/`
- `POST /api/marketplace/assignments/{id}/assign-member/`

## Background Work

Use Celery for work that should not block HTTP requests:

- iCal polling and parsing.
- Google Calendar synchronization.
- Calendar conflict checks.
- Notification dispatch.
- SMS sending.
- Review prompt scheduling.
- Cleanup or retry of failed integration jobs.

Background tasks should be idempotent where possible and safe to retry.

Current background task state:

- Celery app wiring exists in `backend/config/celery.py`.
- Notification dispatch, iCal sync, and Google Calendar sync tasks are placeholders until providers and OAuth/feed behavior are selected.

## Future Microservice Boundaries

If scaling requires service extraction, split along these boundaries:

- Identity service.
- Marketplace service.
- Calendar and integrations service.
- Notification service.
- Feedback and reputation service.
- Admin and moderation service.

Before extraction, communicate across modules with explicit domain events such as:

- `job.created`
- `application.submitted`
- `assignment.accepted`
- `assignment.cancelled`
- `job.completed`
- `review.submitted`
- `calendar.sync_failed`

## Infrastructure Direction

Target EU managed cloud infrastructure:

- Containerized backend and worker deployments.
- Managed PostgreSQL with automated backups.
- Managed Redis.
- Managed object storage.
- Centralized logs.
- Error tracking.
- Basic metrics and uptime monitoring.

The system should be GDPR-conscious from the start. Store only necessary personal data, avoid secrets in source control, and document retention/deletion decisions when they are implemented.

Cookie controls:

- Essential auth and security cookies are always available.
- Analytics and marketing cookies require explicit consent.
- Store consent choices with policy version, consent version, timestamp, and user or anonymous visitor identifier.
- Do not activate optional customer-insight tracking before consent is recorded.
