from django.urls import path, include

# from rest_framework import routers
from rest_framework.routers import DefaultRouter
from .views import OfferViewSet

# from kanban_app.api.views import BoardListView, TasksView, EmailCheckView

# router = routers.SimpleRouter()
# router.register(r'boards', BoardListView)
# router.register(r'tasks', TasksView, basename='tasks')
# router.register(r'email-check', EmailCheckView, basename='email-check')
# urlpatterns = [path("", include(router.urls))]

router = DefaultRouter()
router.register(r"offers", OfferViewSet, basename="offer")


urlpatterns = [
    path("", include(router.urls)),
]
