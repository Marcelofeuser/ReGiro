import csv
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .finance import active_vip, blocked, config, monthly_series, projection_series, total
from .management_forms import BrandForm, CompanyManagementForm, ConfigForm, InvoiceForm
from .models import CompanyBrand, Invoice, ManagementEvent, Store
from .views import rates
from django.forms import modelform_factory
from .models import Rates


def platform_admin(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def event(request, description, store=None):
    ManagementEvent.objects.create(actor=request.user, store=store, description=description)


@platform_admin
def overview(request):
    invoices = Invoice.objects.select_related("store").order_by("-created_at")
    today = timezone.localdate()
    received = total(invoices.filter(paid_at__isnull=False))
    refunds = total(invoices.filter(refunded_at__isnull=False))
    pending = invoices.filter(status=Invoice.Status.OPEN)
    series = monthly_series()
    current_net = series[-1]["received"] - series[-1]["refunded"]
    previous_net = series[-2]["received"] - series[-2]["refunded"]
    growth = ((current_net - previous_net) / previous_net * 100) if previous_net > 0 else None
    categories = [{"label": label, "value": total(invoices.filter(kind=kind, paid_at__isnull=False))
                   - total(invoices.filter(kind=kind, refunded_at__isnull=False))}
                  for kind, label in Invoice.Kind.choices]
    return render(request, "management/overview.html", {
        "received": received, "refunds": refunds, "net": received - refunds,
        "losses": total(invoices.filter(status=Invoice.Status.LOST)),
        "projections": projection_series(),
        "overdue": total(pending.filter(due_date__lt=today)),
        "outstanding": total(pending), "vip_count": active_vip().values("store").distinct().count(),
        "vip_total": invoices.filter(kind=Invoice.Kind.VIP).values("store").distinct().count(),
        "vip_debtors": pending.filter(kind=Invoice.Kind.VIP, due_date__lt=today).values("store").distinct().count(),
        "company_count": Store.objects.count(), "users_count": get_user_model().objects.count(),
        "projection": total(pending.filter(due_date__gte=today, due_date__lte=today + timedelta(days=30))),
        "month": series[-1]["label"], "growth": growth, "series": series, "categories": categories,
        "invoices": Paginator(invoices, 20).get_page(request.GET.get("page")),
        "events": ManagementEvent.objects.select_related("actor", "store").order_by("-pk")[:12],
        "vip_paying_month": invoices.filter(kind=Invoice.Kind.VIP, paid_at__date__gte=today.replace(day=1))
                                      .values("store").distinct().count(),
    })


@platform_admin
def companies(request):
    query = request.GET.get("q", "")[:120]
    stores = Store.objects.select_related("user").filter(
        Q(name__icontains=query) | Q(cnpj__icontains=query) | Q(user__username__icontains=query)
    ).order_by("name", "pk")
    page = Paginator(stores, 25).get_page(request.GET.get("page"))
    for store in page:
        store.financial_blocked = blocked(store)
    return render(request, "management/companies.html", {"page": page, "q": query})


@platform_admin
def users(request):
    query = request.GET.get("q", "")[:120]
    accounts = get_user_model().objects.select_related("store").filter(
        Q(username__icontains=query) | Q(email__icontains=query) | Q(store__name__icontains=query)
    ).order_by("username", "pk")
    return render(request, "management/users.html", {
        "page": Paginator(accounts, 25).get_page(request.GET.get("page")), "q": query,
    })


@platform_admin
@transaction.atomic
def company(request, pk):
    store = get_object_or_404(Store.objects.select_for_update(), pk=pk)
    brand = CompanyBrand.objects.filter(store=store).first() or CompanyBrand(store=store)
    action = request.POST.get("action")
    form = CompanyManagementForm(request.POST if action == "company" else None, instance=store)
    brand_form = BrandForm(request.POST if action == "brand" else None, request.FILES or None, instance=brand)
    invoice_form = InvoiceForm(request.POST if action == "invoice" else None,
                               initial={"kind": Invoice.Kind.VIP, "amount": config().vip_price or None})
    if request.method == "POST":
        if action == "company" and form.is_valid():
            form.save()
            event(request, f"Cadastro alterado. Verificada={store.verified}, suspensa={store.suspended}.", store)
        elif action == "brand" and brand_form.is_valid():
            brand = brand_form.save(commit=False)
            photo = brand_form.cleaned_data["photo_file"]
            if photo:
                brand.logo = photo
            brand.save()
            event(request, "Identidade visual atualizada.", store)
        elif action == "invoice" and invoice_form.is_valid():
            invoice = invoice_form.save(commit=False)
            invoice.store = store
            invoice.save()
            event(request, f"Cobrança {invoice.reference} registrada, R$ {invoice.amount}.", store)
        else:
            return render(request, "management/company.html", {
                "store": store, "form": form, "brand_form": brand_form, "invoice_form": invoice_form,
                "invoices": store.invoices.order_by("-pk")[:50], "blocked": blocked(store),
            })
        messages.success(request, "Alteração registrada no histórico.")
        return redirect("management_company", pk=pk)
    return render(request, "management/company.html", {
        "store": store, "form": form, "brand_form": brand_form, "invoice_form": invoice_form,
        "invoices": store.invoices.order_by("-pk")[:50], "blocked": blocked(store),
    })


@platform_admin
@require_POST
@transaction.atomic
def invoice_action(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_for_update(), pk=pk)
    action = request.POST.get("action")
    if action == "pay" and invoice.status == Invoice.Status.OPEN:
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = timezone.now()
    elif action == "cancel" and invoice.status == Invoice.Status.OPEN:
        invoice.status = Invoice.Status.CANCELLED
    elif action == "writeoff" and invoice.overdue:
        invoice.status = Invoice.Status.LOST
        invoice.lost_at = timezone.now()
    elif action == "refund" and invoice.status == Invoice.Status.PAID:
        invoice.status = Invoice.Status.REFUNDED
        invoice.refunded_at = timezone.now()
    else:
        messages.info(request, "Este lançamento já foi atualizado ou a ação não se aplica.")
        return redirect("management_company", pk=invoice.store_id)
    invoice.save(update_fields=["status", "paid_at", "refunded_at", "lost_at"])
    event(request, f"Cobrança {invoice.reference} — {invoice.get_status_display()} (registro manual).", invoice.store)
    messages.success(request, "Registro manual salvo.")
    return redirect("management_company", pk=invoice.store_id)


@platform_admin
@transaction.atomic
def settings(request):
    instance = config()
    form = ConfigForm(request.POST if request.method == "POST" else None, instance=instance)
    rate_class = modelform_factory(Rates, fields=("commission", "swap_fee"))
    rate_form = rate_class(request.POST if request.method == "POST" else None, instance=rates())
    if request.method == "POST" and all([form.is_valid(), rate_form.is_valid()]):
        form.save()
        rate_form.save()
        event(request, (
            f"Configurações atualizadas: comissão {rate_form.instance.commission}%, "
            f"troca R$ {rate_form.instance.swap_fee}, VIP R$ {form.instance.vip_price}, "
            f"bloqueio {form.instance.auto_block}, tolerância {form.instance.grace_days} dias, "
            f"vencimento de tarifas {form.instance.fee_due_days} dias."
        ))
        messages.success(request, "Configurações salvas.")
        return redirect("management_settings")
    return render(request, "management/settings.html", {"form": form, "rate_form": rate_form})


@platform_admin
def export_finance(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="financeiro-regiro.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Empresa", "CNPJ", "Referência", "Tipo", "Valor", "Vencimento", "Situação", "Recebido em", "Estornado em"])
    for invoice in Invoice.objects.select_related("store").order_by("pk").iterator():
        row = [invoice.store.name, invoice.store.cnpj, invoice.reference, invoice.get_kind_display(),
               str(invoice.amount), str(invoice.due_date), invoice.get_status_display(),
               str(invoice.paid_at or ""), str(invoice.refunded_at or "")]
        writer.writerow(["'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else value for value in row])
    return response
