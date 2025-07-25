from django.urls import path
from .views import *


app_name = "content_gen"

urlpatterns = [
    path('generate/', GptRequestView.as_view(), name='generate_endpoint'),
    path('replicate/', CodingReplicatorView.as_view(), name='replicate_endpoint'),
    path('prompt/', PromptView.as_view(), name='prompt_endpoint'),
    path('curate/', CodingCuratorView.as_view(), name='coding_curator_endpoint'),
]
