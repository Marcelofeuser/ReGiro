from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views, management_views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("admin/", management_views.overview, name="management"),
    path("gestao/empresas/", management_views.companies, name="management_companies"),
    path("gestao/usuarios/", management_views.users, name="management_users"),
    path("gestao/empresas/<int:pk>/", management_views.company, name="management_company"),
    path("gestao/cobrancas/<int:pk>/", management_views.invoice_action, name="management_invoice"),
    path("gestao/configuracoes/", management_views.settings, name="management_settings"),
    path("gestao/exportar/", management_views.export_finance, name="management_export"),
    path("admin/", admin.site.urls),
    path("entrar/", LoginView.as_view(template_name="login.html"), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
    path("cadastro/", views.register, name="register"),
    path("painel/", views.dashboard, name="dashboard"),
    path("marca/<int:pk>/logo/", views.brand_logo, name="brand_logo"),
    path("painel/financeiro/", views.company_finance, name="company_finance"),
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
