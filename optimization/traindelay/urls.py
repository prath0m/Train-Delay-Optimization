from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/optimize/', views.run_optimization, name='run_optimization'),
    path('api/shap/', views.run_shap, name='run_shap'),
]
