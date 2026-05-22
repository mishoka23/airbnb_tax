from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import (
    AgencyInvitation,
    AgencyMembership,
    AgencyProfile,
    CleanerProfile,
    CookieConsent,
    HostProfile,
    User,
)
from apps.marketplace.models import Assignment, CleaningJob
from apps.marketplace.services import accept_application, publish_job, submit_application
from apps.properties.models import Property


class AccountAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_signup_creates_pending_user_and_profile_session(self):
        response = self.client.post(
            reverse("account-signup"),
            {
                "name": "Host Owner",
                "email": "owner@example.com",
                "phone_number": "+359888000111",
                "city": "Sofia",
                "preferred_language": User.Language.ENGLISH,
                "role": User.Role.HOST,
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="owner@example.com")
        self.assertEqual(user.account_status, User.AccountStatus.PENDING)
        self.assertTrue(HostProfile.objects.filter(user=user, city="Sofia").exists())

        me_response = self.client.get(reverse("account-me"))
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data["account_status"], User.AccountStatus.PENDING)
        self.assertFalse(me_response.data["is_platform_admin"])

    def test_signup_does_not_allow_admin_role(self):
        response = self.client.post(
            reverse("account-signup"),
            {
                "name": "Platform Admin",
                "email": "admin-signup@example.com",
                "role": User.Role.ADMIN,
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="admin-signup@example.com").exists())

    def test_anonymous_user_endpoint_cannot_create_admin_account(self):
        response = self.client.post(
            "/api/accounts/users/",
            {
                "username": "public-admin",
                "email": "public-admin@example.com",
                "password": "password123",
                "role": User.Role.ADMIN,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="public-admin").exists())

    def test_superuser_defaults_to_platform_admin(self):
        user = User.objects.create_superuser(
            username="root",
            email="root@example.com",
            password="password123",
        )

        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertEqual(user.account_status, User.AccountStatus.APPROVED)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_platform_admin)

    def test_login_and_logout_use_session_authentication(self):
        user = User.objects.create_user(
            username="cleaner@example.com",
            email="cleaner@example.com",
            password="password123",
            role=User.Role.CLEANER,
        )
        CleanerProfile.objects.create(user=user)

        login_response = self.client.post(
            reverse("account-login"),
            {"email": "cleaner@example.com", "password": "password123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(self.client.get(reverse("account-me")).status_code, 200)

        logout_response = self.client.post(reverse("account-logout"))
        self.assertEqual(logout_response.status_code, 204)
        self.assertEqual(self.client.get(reverse("account-me")).status_code, 403)

    def test_admin_can_approve_user_through_api(self):
        admin = User.objects.create_user(
            username="admin",
            password="password123",
            role=User.Role.ADMIN,
            account_status=User.AccountStatus.APPROVED,
        )
        pending = User.objects.create_user(
            username="pending",
            password="password123",
            role=User.Role.HOST,
        )
        self.client.force_authenticate(admin)

        response = self.client.post(f"/api/accounts/users/{pending.id}/approve/")

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertEqual(pending.account_status, User.AccountStatus.APPROVED)
        self.assertEqual(pending.approved_by, admin)

    def test_pending_host_cannot_create_property_or_job(self):
        host = User.objects.create_user(username="host", password="password123", role=User.Role.HOST)
        HostProfile.objects.create(user=host)
        property = Property.objects.create(host=host, name="Flat", city="Sofia")
        self.client.force_authenticate(host)

        property_response = self.client.post(
            "/api/properties/properties/",
            {"name": "New Flat", "city": "Sofia"},
            format="json",
        )
        job_response = self.client.post(
            "/api/marketplace/jobs/",
            {
                "property_id": property.id,
                "title": "Turnover",
                "scheduled_start": (timezone.now() + timedelta(days=1)).isoformat(),
                "scheduled_end": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(property_response.status_code, 403)
        self.assertEqual(job_response.status_code, 403)

    def test_cookie_consent_records_anonymous_visitor_choices(self):
        response = self.client.post(
            reverse("cookie-consent"),
            {
                "visitor_id": "visitor-123",
                "analytics": True,
                "marketing": False,
                "policy_version": "v1",
                "consent_version": "v1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        consent = CookieConsent.objects.get(visitor_id="visitor-123")
        self.assertTrue(consent.essential)
        self.assertTrue(consent.analytics)
        self.assertFalse(consent.marketing)


class AgencyWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agency_user = User.objects.create_user(
            username="agency@example.com",
            email="agency@example.com",
            password="password123",
            role=User.Role.AGENCY,
            account_status=User.AccountStatus.APPROVED,
        )
        self.agency = AgencyProfile.objects.create(
            user=self.agency_user,
            company_name="Agency One",
            city="Sofia",
        )
        self.cleaner = User.objects.create_user(
            username="cleaner@example.com",
            email="cleaner@example.com",
            password="password123",
            role=User.Role.CLEANER,
            account_status=User.AccountStatus.APPROVED,
        )
        CleanerProfile.objects.create(
            user=self.cleaner,
            display_name="Cleaner One",
            verification_status=CleanerProfile.VerificationStatus.VERIFIED,
        )

    def test_agency_invites_and_cleaner_accepts_membership(self):
        self.client.force_authenticate(self.agency_user)
        invite_response = self.client.post(
            f"/api/accounts/agencies/{self.agency.id}/invite-cleaner/",
            {"email": "cleaner@example.com"},
            format="json",
        )
        duplicate_response = self.client.post(
            f"/api/accounts/agencies/{self.agency.id}/invite-cleaner/",
            {"email": "cleaner@example.com"},
            format="json",
        )

        self.assertEqual(invite_response.status_code, 201)
        self.assertEqual(duplicate_response.status_code, 400)

        invitation = AgencyInvitation.objects.get()
        self.client.force_authenticate(self.cleaner)
        accept_response = self.client.post(f"/api/accounts/agency-invitations/{invitation.id}/accept/")

        self.assertEqual(accept_response.status_code, 201)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, AgencyInvitation.Status.ACCEPTED)
        self.assertTrue(
            AgencyMembership.objects.filter(
                agency=self.agency,
                cleaner=self.cleaner,
                status=AgencyMembership.Status.ACTIVE,
            ).exists()
        )

    def test_agency_can_assign_accepted_job_to_active_member(self):
        AgencyMembership.objects.create(agency=self.agency, cleaner=self.cleaner, invited_by=self.agency_user)
        host = User.objects.create_user(
            username="host",
            password="password123",
            role=User.Role.HOST,
            account_status=User.AccountStatus.APPROVED,
        )
        property = Property.objects.create(host=host, name="Center Flat", city="Sofia")
        job = CleaningJob.objects.create(
            property=property,
            host=host,
            title="Turnover",
            scheduled_start=timezone.now() + timedelta(days=1),
            scheduled_end=timezone.now() + timedelta(days=1, hours=2),
        )

        publish_job(job)
        application = submit_application(job=job, cleaner=self.agency_user)
        assignment = accept_application(application=application, accepted_by=host)

        self.client.force_authenticate(self.agency_user)
        response = self.client.post(
            f"/api/marketplace/assignments/{assignment.id}/assign-member/",
            {"assigned_member_id": self.cleaner.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        assignment.refresh_from_db()
        self.assertEqual(assignment.assigned_member, self.cleaner)
        self.assertEqual(Assignment.objects.filter(assigned_member=self.cleaner).count(), 1)
