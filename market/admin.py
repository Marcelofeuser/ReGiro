from django.contrib import admin

from .models import Deal, Listing, Rates, Report, Store

admin.site.site_header = "Administração ReGiro"


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "verified", "suspended")
    list_filter = ("verified", "suspended")
    search_fields = ("name", "cnpj")


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "status", "price")
    list_filter = ("status", "mode")
    search_fields = ("title", "code", "store__name")


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("target", "buyer", "seller", "status", "amount", "fee")
    list_filter = ("status",)
    readonly_fields = tuple(field.name for field in Deal._meta.fields if field.name != "id")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("listing", "reporter", "resolved", "created_at")
    list_filter = ("resolved",)
    readonly_fields = ("listing", "reporter", "reason", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(Rates)
class RatesAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return super().has_add_permission(request) and not Rates.objects.exists()

    def save_model(self, request, obj, form, change):
        obj.pk = 1
        super().save_model(request, obj, form, change)
