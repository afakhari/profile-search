from rest_framework.generics import RetrieveAPIView

from .models import Profile
from .serializers import ProfileDetailSerializer


class ProfileDetailView(RetrieveAPIView):
    queryset = Profile.objects.prefetch_related("skills", "experiences", "educations")
    serializer_class = ProfileDetailSerializer

