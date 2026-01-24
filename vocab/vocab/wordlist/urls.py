from django.urls import path

from wordlist import views

urlpatterns = [path("", views.VocabRunner.as_view(), name="get-word")]
