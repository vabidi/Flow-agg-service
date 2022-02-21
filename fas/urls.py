from django.urls import path

from . import views

urlpatterns = [
        path('flows', views.flows, name='flows'),
        path('', views.index, name='index'),
]
