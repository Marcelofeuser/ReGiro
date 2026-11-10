from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("admin/", admin.site.urls),
    path("entrar/", LoginView.as_view(template_name="login.html"), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
    path("cadastro/", views.register, name="register"),
    path("painel/", views.dashboard, name="dashboard"),
    path("painel/empresa/", views.store_profile, name="store_profile"),
    path("anunciar/", views.publish, name="publish"),
    path("painel/anuncios/<int:pk>/", views.manage_listing, name="manage_listing"),
    path("pecas/<int:pk>/", views.listing_detail, name="listing"),
    path("pecas/<int:pk>/foto/", views.listing_photo, name="listing_photo"),
    path("pecas/<int:pk>/favorito/", views.favorite, name="favorite"),
    path("pecas/<int:pk>/denunciar/", views.report, name="report"),
    path("pecas/<int:pk>/propor/", views.propose, name="propose"),
    path("negociacoes/<int:pk>/", views.deal_detail, name="deal"),
    path("clube/", views.vip, name="vip"),
]
