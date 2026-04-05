from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/optimize/', views.run_optimization, name='run_optimization'),
]
