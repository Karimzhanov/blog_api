from rest_framework.routers import DefaultRouter
from apps.posts.views import PostViewSet

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")

urlpatterns = router.urls
