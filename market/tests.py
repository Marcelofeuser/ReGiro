from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from PIL import Image

from .models import CompanyBrand, Deal, Invoice, Listing, ListingPhoto, ManagementEvent, PlatformConfig, Store


class MarketplaceFlowTests(TestCase):
    def store(self, username, cnpj):
        user = get_user_model().objects.create_user(username=username)
        return Store.objects.create(user=user, legal_name=username, name=username, cnpj=cnpj,
                                    address="Rua Um", phone="11999999999",
                                    email=f"{username}@example.com", contact="Responsável", verified=True)

    def listing(self, store, title):
        return Listing.objects.create(store=store, title=title, description="Lote novo",
                                      category="Motor", manufacturer="Marca", code="ABC",
                                      condition="Nova lacrada", quantity=1, price=100,
                                      city="São Paulo, SP", delivery="Retirada",
                                      provenance="Nota fiscal", mode=Listing.Mode.SWAP)

    def test_registration_catalog_and_two_party_swap(self):
        response = self.client.post(reverse("register"), {
            "username": "proponente", "password1": "Secure-local-2026!", "password2": "Secure-local-2026!",
            "legal_name": "Loja Um Ltda", "name": "Loja Um", "cnpj": "04.252.011/0001-10",
            "address": "Rua Um", "phone": "11999999999", "email": "loja@example.com",
            "contact": "Responsável",
        })
        self.assertRedirects(response, reverse("dashboard"))
        buyer = Store.objects.get(name="Loja Um")
        self.assertEqual(self.client.get(reverse("publish")).status_code, 403)
        buyer.verified = True
        buyer.save()
        seller = self.store("vendedora", "22333333333333")
        outsider = self.store("outra", "33333333333333")
        target = self.listing(seller, "Alternador")
        offered = self.listing(buyer, "Kit de freio")
        self.assertContains(self.client.get(reverse("catalog"), {"q": "Alternador"}), "Alternador")
        self.assertNotContains(self.client.get(reverse("catalog"), {"q": "Alternador"}), "Kit de freio")
        self.assertContains(self.client.get(reverse("listing", args=[target.pk])), "Iniciar negociação")
        proposal_url = reverse("propose", args=[target.pk])
        self.assertContains(self.client.get(proposal_url), "tarifa única")
        response = self.client.post(proposal_url, {"amount": "25.00", "offered": offered.pk})
        deal = Deal.objects.get()
        url = reverse("deal", args=[deal.pk])
        self.assertRedirects(response, url)
        self.assertEqual(deal.fee, Decimal("10"))
        self.client.force_login(outsider.user)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(buyer.user)
        self.assertEqual(self.client.post(url, {"action": "accept"}).status_code, 403)
        self.client.post(url, {"action": "message", "text": "Podemos retirar amanhã?"})
        self.client.force_login(seller.user)
        self.assertContains(self.client.get(url), "Podemos retirar amanhã?")
        self.client.post(url, {"action": "accept"})
        target.refresh_from_db()
        self.assertEqual(target.status, Listing.Status.RESERVED)
        self.client.post(url, {"action": "received"})
        deal.refresh_from_db()
        self.assertEqual(deal.status, Deal.Status.ACCEPTED)
        self.client.force_login(buyer.user)
        self.client.post(url, {"action": "received"})
        deal.refresh_from_db()
        target.refresh_from_db()
        offered.refresh_from_db()
        self.assertEqual(deal.status, Deal.Status.COMPLETE)
        self.assertEqual(Invoice.objects.get(deal=deal).amount, deal.fee)
        self.assertEqual(target.status, Listing.Status.SWAPPED)
        self.assertEqual(offered.status, Listing.Status.SWAPPED)
        self.assertEqual(self.client.post(url, {"action": "received"}).status_code, 403)

    def test_dashboard_listing_management_is_owner_only(self):
        owner = self.store("dona", "12345678912345")
        other = self.store("outra", "54321987654321")
        listing = self.listing(owner, "Alternador")
        url = reverse("manage_listing", args=[listing.pk])
        self.client.force_login(other.user)
        self.assertEqual(self.client.post(url, {"action": "close"}).status_code, 404)
        self.assertNotContains(self.client.get(reverse("dashboard")), "Alternador")
        self.client.force_login(owner.user)
        self.assertContains(self.client.get(reverse("dashboard")), "Alternador")
        self.assertContains(self.client.get(url), "Salvar alterações")
        self.assertRedirects(self.client.post(url, {"action": "close"}), reverse("dashboard"))
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.CLOSED)
        self.assertNotContains(self.client.get(reverse("catalog")), "Alternador")

    def test_company_credentials_and_inventory_are_independent(self):
        companies = [
            ("loja_alfa", "Access-alfa-3!2026", "Alfa Comércio", "04.252.011/0001-10", "Disco Alfa"),
            ("loja_beta", "Access-beta-7!2026", "Beta Comércio", "11.222.333/0001-81", "Disco Beta"),
        ]
        for username, password, name, cnpj, title in companies:
            self.assertRedirects(self.client.post(reverse("register"), {
                "username": username, "password1": password, "password2": password,
                "legal_name": name, "name": name, "cnpj": cnpj, "address": "Rua Um",
                "phone": "11999999999", "email": f"{username}@example.com", "contact": "Responsável",
            }), reverse("dashboard"))
            store = Store.objects.get(name=name)
            store.verified = True
            store.save(update_fields=["verified"])
            response = self.client.post(reverse("publish"), {
                "title": title, "description": "Lote novo", "category": "Freios",
                "manufacturer": "Marca", "code": "ABC", "condition": "Nova lacrada",
                "quantity": 1, "price": "100.00", "city": "São Paulo, SP",
                "delivery": "Retirada", "provenance": "Nota fiscal", "mode": Listing.Mode.SALE,
                "store": Store.objects.exclude(pk=store.pk).values_list("pk", flat=True).first() or store.pk,
            })
            item = Listing.objects.get(title=title)
            self.assertRedirects(response, reverse("listing", args=[item.pk]))
            self.assertEqual(item.store, store)
            self.client.post(reverse("logout"))

        username, password, name, _, title = companies[0]
        self.assertFalse(self.client.login(username=username, password=companies[1][1]))
        self.assertTrue(self.client.login(username=username, password=password))
        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, title)
        self.assertNotContains(dashboard, companies[1][4])
        profile = self.client.get(reverse("store_profile"))
        self.assertContains(profile, name)
        self.assertNotContains(profile, companies[1][2])
        other_item = Listing.objects.get(title=companies[1][4])
        self.assertEqual(self.client.get(reverse("manage_listing", args=[other_item.pk])).status_code, 404)
        self.assertContains(self.client.get(reverse("catalog")), other_item.title)


    def test_photo_is_validated_and_follows_listing_visibility(self):
        owner = self.store("fotografa", "12345678912345")
        listing = self.listing(owner, "Alternador")
        payload = {
            "title": listing.title, "description": listing.description, "category": listing.category,
            "manufacturer": listing.manufacturer, "code": listing.code, "condition": listing.condition,
            "quantity": 1, "price": "100.00", "city": listing.city,
            "delivery": listing.delivery, "provenance": listing.provenance, "mode": listing.mode,
        }
        photo_url = reverse("listing_photo", args=[listing.pk])
        manage_url = reverse("manage_listing", args=[listing.pk])
        self.client.force_login(owner.user)
        bad_photo = SimpleUploadedFile("peca.png", b"not an image", content_type="image/png")
        self.assertContains(self.client.post(manage_url, {**payload, "photo_file": bad_photo}),
                            "Envie uma foto válida")
        self.assertFalse(ListingPhoto.objects.exists())
        image = BytesIO()
        Image.new("RGB", (40, 30), "green").save(image, "PNG")
        photo = SimpleUploadedFile("peca.png", image.getvalue(), content_type="image/png")
        self.assertRedirects(self.client.post(manage_url, {**payload, "photo_file": photo}),
                             reverse("dashboard"))
        self.client.logout()
        response = self.client.get(photo_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        with Image.open(BytesIO(response.content)) as served:
            self.assertEqual(served.format, "JPEG")
        self.assertContains(self.client.get(reverse("catalog")), photo_url)
        listing.status = Listing.Status.CLOSED
        listing.save(update_fields=["status"])
        self.assertEqual(self.client.get(photo_url).status_code, 404)
        self.client.force_login(owner.user)
        self.assertEqual(self.client.get(photo_url).status_code, 200)


class PlatformManagementTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("gestor", "gestor@example.com", "test-pass")
        self.user = get_user_model().objects.create_user("empresa", password="company-pass")
        self.store = Store.objects.create(
            user=self.user, legal_name="Empresa Ltda", name="Empresa",
            cnpj="04252011000110", address="Rua Um", phone="11999999999",
            email="empresa@example.com", contact="Responsável", verified=True,
        )
        self.invoice = Invoice.objects.create(
            store=self.store, kind=Invoice.Kind.VIP, reference="vip-teste", amount=50,
            due_date=timezone.localdate() - timedelta(days=10),
            period_start=timezone.localdate() - timedelta(days=1),
            period_end=timezone.localdate() + timedelta(days=29),
        )

    def test_global_admin_authorization_and_company_isolation(self):
        self.client.force_login(self.user)
        for name in ("management", "management_companies", "management_users",
                     "management_export", "management_settings"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403)
        self.assertEqual(self.client.get(reverse("management_company", args=[self.store.pk])).status_code, 403)
        self.assertContains(self.client.get(reverse("company_finance")), "vip-teste")
        other_user = get_user_model().objects.create_user("outra")
        Store.objects.create(user=other_user, name="Outra", legal_name="Outra", cnpj="12345678912345")
        self.client.force_login(other_user)
        self.assertNotContains(self.client.get(reverse("company_finance")), "vip-teste")
        self.client.force_login(self.admin)
        for name in ("management", "management_companies", "management_users", "management_settings"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertContains(self.client.get(reverse("management_company", args=[self.store.pk])), "Empresa Ltda")

    def test_receipt_refund_and_repeated_requests_preserve_totals(self):
        self.client.force_login(self.admin)
        url = reverse("management_invoice", args=[self.invoice.pk])
        self.client.post(url, {"action": "pay"})
        self.client.post(url, {"action": "pay"})
        self.assertEqual(ManagementEvent.objects.count(), 1)
        overview = self.client.get(reverse("management"))
        self.assertEqual(overview.context["net"], Decimal("50"))
        self.assertEqual(overview.context["vip_count"], 1)
        self.client.post(url, {"action": "refund"})
        self.client.post(url, {"action": "refund"})
        overview = self.client.get(reverse("management"))
        self.assertEqual(overview.context["net"], Decimal("0"))
        self.assertEqual(overview.context["refunds"], Decimal("50"))
        self.assertEqual(overview.context["vip_count"], 0)
        self.assertEqual(ManagementEvent.objects.count(), 2)

    def test_financial_block_releases_after_receipt(self):
        PlatformConfig.objects.create(pk=1, auto_block=True, grace_days=5)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("publish")).status_code, 403)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertContains(self.client.get(reverse("company_finance")), "bloqueadas")
        self.client.force_login(self.admin)
        self.client.post(reverse("management_invoice", args=[self.invoice.pk]), {"action": "pay"})
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("publish")).status_code, 200)

    def test_white_label_and_configuration_validation(self):
        self.client.force_login(self.admin)
        company_url = reverse("management_company", args=[self.store.pk])
        self.client.post(company_url, {
            "action": "brand", "enabled": "on", "display_name": "Marca da Loja", "color": "#274faf",
        })
        self.assertTrue(CompanyBrand.objects.get(store=self.store).enabled)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("dashboard")), "Marca da Loja")
        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get(reverse("management")), "Marca da Loja")
        self.client.post(company_url, {
            "action": "brand", "enabled": "on", "display_name": "Bad", "color": "bad",
        })
        self.assertEqual(CompanyBrand.objects.get(store=self.store).color, "#274faf")

    def test_projection_writeoff_and_csv_formula_escaping(self):
        future = Invoice.objects.create(
            store=self.store, kind=Invoice.Kind.MONTHLY, reference="=sensitive", amount=100,
            due_date=timezone.localdate() + timedelta(days=15),
        )
        self.client.force_login(self.admin)
        overview = self.client.get(reverse("management"))
        self.assertEqual(overview.context["projection"], Decimal("100"))
        self.assertEqual(overview.context["overdue"], Decimal("50"))
        self.client.post(reverse("management_invoice", args=[self.invoice.pk]), {"action": "writeoff"})
        self.assertEqual(self.client.get(reverse("management")).context["losses"], Decimal("50"))
        self.assertContains(self.client.get(reverse("management_export")), "'=sensitive")
