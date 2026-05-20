# Architecture

## Overview

The application is a service-ready modular marketplace for Bulgarian Airbnb and short-term rental hosts who need reliable cleaners.

The v1 architecture should start as a modular Django backend with a Next.js PWA frontend. This keeps the first build practical while preserving clear domain boundaries that can later be extracted into independently deployed microservices.

The app calendar is the source of truth. External calendars, including Google Calendar and iCal feeds from Airbnb or booking platforms, sync into or out of the application.

## Architecture Style

Use a modular monolith for v1:

- One deployable backend API.
- One primary PostgreSQL database.
- Redis for cache, locks, and Celery broker/result needs.
- Celery workers for asynchronous sync and notification work.
- One Next.js frontend serving hosts, cleaners, and admins with role-specific experiences.

The code should be organized around business domains, not technical layers alone. Domain modules should communicate through explicit service functions and events rather than reaching into each other's internals.

Future extraction into microservices should be possible without rewriting core business logic.

## Product Domains

### Identity and Access

Responsibilities:

- User authentication.
- Host, cleaner, and admin roles.
- Profile data.
- Cleaner verification status.
- Permissions and role-based API access.

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

### Marketplace Jobs

Responsibilities:

- Single cleaning job creation.
- Monthly batch creation.
- Job search and filtering.
- Job lifecycle state transitions.
- Assignment rules.
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
- Host profile.
- Cleaner profile.
- Cleaner verification.
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

Expected resource groups:

- `/auth/`
- `/users/`
- `/hosts/`
- `/cleaners/`
- `/properties/`
- `/calendar/`
- `/reservations/`
- `/jobs/`
- `/applications/`
- `/assignments/`
- `/reviews/`
- `/notifications/`
- `/admin/`

The exact routes can evolve, but APIs should preserve domain boundaries and avoid leaking internal model structure unnecessarily.

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

