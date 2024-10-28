from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import path
from .views import VoiceCloneView

urlpatterns = [
    path('clone/', VoiceCloneView.as_view(), name='voice-clone'),  # Matches the 'voice-clone' name
    path('test-voice-clone/', lambda request: render(request, 'voice_clone_test.html'), name='test_voice_clone'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
