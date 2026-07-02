from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.response import Response
from apps.posts.models import Post
from apps.posts.permissions import IsAuthorOrReadOnly
from apps.posts.serializers import PostSerializer

POSTS_LIST_CACHE_KEY = "posts_list"
POSTS_LIST_CACHE_TTL = 60 


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author").all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def list(self, request, *args, **kwargs):
        cached_data = cache.get(POSTS_LIST_CACHE_KEY)
        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(POSTS_LIST_CACHE_KEY, response.data, POSTS_LIST_CACHE_TTL)
        return response

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        cache.delete(POSTS_LIST_CACHE_KEY)

    def perform_update(self, serializer):
        serializer.save()
        cache.delete(POSTS_LIST_CACHE_KEY)

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(POSTS_LIST_CACHE_KEY)
