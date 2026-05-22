from rest_framework.routers import DefaultRouter

from apps.marketplace.views import (
    AssignmentViewSet,
    CleanerApplicationViewSet,
    CleaningBatchViewSet,
    CleaningJobViewSet,
    MarketplaceCalendarView,
)
from django.urls import path


router = DefaultRouter()
router.register("batches", CleaningBatchViewSet, basename="cleaning-batch")
router.register("jobs", CleaningJobViewSet, basename="cleaning-job")
router.register("applications", CleanerApplicationViewSet, basename="cleaner-application")
router.register("assignments", AssignmentViewSet, basename="assignment")

urlpatterns = [
    path("calendar/", MarketplaceCalendarView.as_view(), name="marketplace-calendar"),
] + router.urls
