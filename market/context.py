import re

from .models import CompanyBrand


def branding(request):
    if request.path.startswith(("/admin/", "/gestao/")):
        return {}
    store = getattr(request.user, "store", None)
    if not store:
        return {}
    brand = CompanyBrand.objects.filter(store=store, enabled=True).defer("logo").first()
    if not brand:
        return {}
    return {"company_brand": {
        "store_id": store.pk, "display_name": brand.display_name or store.name,
        "color": brand.color if re.fullmatch(r"#[0-9a-fA-F]{6}", brand.color) else "#006b50",
        "has_logo": CompanyBrand.objects.filter(pk=brand.pk).exclude(logo=None).exists(),
    }}
