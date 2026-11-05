from django.urls import path
from . import views

app_name = 'portfolios'

urlpatterns = [
    path('portfolio/', views.portfolio_builder_view, name='builder'),
    path('portfolio/preview/', views.preview_portfolio_view, name='preview'),
    path('portfolio/project/<int:project_id>/delete/', views.delete_project_view, name='delete_project'),
    path('u/<str:username>/', views.public_portfolio_view, name='public'),
]
