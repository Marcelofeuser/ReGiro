from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CatalogFilters, ListingForm, ProposalForm, StoreForm, TextForm
from .finance import active_vip, blocked, config
from .models import CompanyBrand, Invoice, Deal, Favorite, Listing, ListingPhoto, Message, Rates, Report, Store


def rates():
    return Rates.objects.filter(pk=1).first() or Rates(pk=1)


def catalog(request):
    results = Listing.objects.filter(status=Listing.Status.ACTIVE, store__suspended=False).select_related("store")
    results = results.annotate(has_photo=Exists(ListingPhoto.objects.filter(listing=OuterRef("pk"))))
    filters = CatalogFilters(request.GET)
    filters.is_valid()
    query = filters.cleaned_data.get("q", "")
    for term in query.split():
        results = results.filter(
            Q(title__icontains=term) | Q(manufacturer__icontains=term) |
            Q(code__icontains=term) | Q(oem__icontains=term) | Q(vehicle__icontains=term) |
            Q(category__icontains=term) | Q(city__icontains=term)
        )
    mode = filters.cleaned_data.get("mode")
    condition = filters.cleaned_data.get("condition")
    max_price = filters.cleaned_data.get("max_price")
    if mode:
        results = results.filter(mode=mode)
    if condition:
        results = results.filter(condition=condition)
    if max_price is not None:
        results = results.filter(price__lte=max_price)
    order = filters.cleaned_data.get("order")
    results = results.order_by({"low": "price", "high": "-price"}.get(order, "-created_at"), "-pk")
    page = Paginator(results, 24).get_page(request.GET.get("page"))
    return render(request, "catalog.html", {"page": page, "filters": filters})


@transaction.atomic
def register(request):
    if request.user.is_authenticated:
        if hasattr(request.user, "store"):
            return redirect("dashboard")
        raise PermissionDenied("Saia da conta atual para cadastrar uma loja.")
    account = UserCreationForm(request.POST if request.method == "POST" else None)
    profile = StoreForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and all([account.is_valid(), profile.is_valid()]):
        user = account.save()
        Store.objects.create(user=user, **profile.cleaned_data)
        login(request, user)
        return redirect("dashboard")
    return render(request, "register.html", {"account": account, "profile": profile})


def current_store(request, verified=False):
    store = getattr(request.user, "store", None)
    if not store or store.suspended or (verified and not store.verified):
        raise PermissionDenied("Esta ação requer uma loja aprovada e ativa.")
    return store


@login_required
def dashboard(request):
    store = current_store(request)
    listings = store.listings.order_by("-created_at", "-pk")
    deals = Deal.objects.filter(Q(buyer=store) | Q(seller=store)).select_related(
        "target", "buyer", "seller"
    ).order_by("-created_at", "-pk")
    favorites = Listing.objects.filter(
        favorite__store=store, status=Listing.Status.ACTIVE, store__suspended=False
    ).select_related("store").order_by("-created_at", "-pk")
    counts = {row["status"]: row["total"] for row in
              listings.order_by().values("status").annotate(total=Count("pk"))}
    metrics = [(label, counts.get(value, 0)) for value, label in Listing.Status.choices]
    tab = request.GET.get("tab", "listings")
    collections = {"listings": listings, "incoming": deals.filter(seller=store),
                   "outgoing": deals.filter(buyer=store), "favorites": favorites}
    if tab not in collections:
        tab = "listings"
    page = Paginator(collections[tab], 12).get_page(request.GET.get("page"))
    tabs = {"listings": "Meus anúncios", "incoming": "Propostas recebidas",
            "outgoing": "Propostas enviadas", "favorites": "Peças salvas"}
    return render(request, "dashboard.html", {
        "store": store, "page": page, "tab": tab, "metrics": metrics,
        "tabs": tabs, "tab_label": tabs[tab],
    })


@login_required
def store_profile(request):
    return render(request, "store_profile.html", {"store": current_store(request)})


@login_required
def manage_listing(request, pk):
    store = current_store(request, verified=True)
    check_commerce(store)
    with transaction.atomic():
        item = get_object_or_404(store.listings.select_for_update(), pk=pk)
        if item.status != Listing.Status.ACTIVE:
            raise PermissionDenied
        if request.method == "POST" and request.POST.get("action") == "close":
            item.status = Listing.Status.CLOSED
            item.save(update_fields=["status"])
            messages.success(request, "Anúncio encerrado e retirado do catálogo.")
            return redirect("dashboard")
        has_proposals = item.proposals.exists() or item.offers.exists()
        form = ListingForm(request.POST, request.FILES, instance=item) if request.method == "POST" else ListingForm(instance=item)
        if request.method == "POST" and has_proposals:
            raise PermissionDenied("Anúncios com histórico de propostas não podem ser editados.")
        if form.is_valid():
            form.save()
            save_photo(item, form)
            messages.success(request, "Anúncio atualizado.")
            return redirect("dashboard")
    return render(request, "manage_listing.html", {"item": item, "form": form, "has_proposals": has_proposals})


def save_photo(item, form):
    content = form.cleaned_data["photo_file"]
    if content is not None:
        ListingPhoto.objects.update_or_create(listing=item, defaults={"content": content})


@login_required
@transaction.atomic
def publish(request):
    store = current_store(request, verified=True)
    check_commerce(store)
    form = ListingForm(request.POST, request.FILES) if request.method == "POST" else ListingForm()
    if form.is_valid():
        listing = form.save(commit=False)
        listing.store = store
        listing.save()
        save_photo(listing, form)
        return redirect("listing", pk=listing.pk)
    return render(request, "form.html", {"title": "Anunciar peça", "form": form, "listing_store": store})


def listing_detail(request, pk):
    listing = get_object_or_404(Listing.objects.select_related("store"), pk=pk, store__suspended=False)
    store = getattr(request.user, "store", None)
    active = listing.status == Listing.Status.ACTIVE
    if not active and store != listing.store:
        raise PermissionDenied
    return render(request, "listing.html", {
        "item": listing, "active": active, "store": store, "rates": rates(),
        "has_photo": ListingPhoto.objects.filter(listing=listing).exists(),
    })


def listing_photo(request, pk):
    store = getattr(request.user, "store", None)
    visible = Q(listing__status=Listing.Status.ACTIVE)
    if store and not store.suspended:
        visible |= Q(listing__store=store)
    photo = get_object_or_404(
        ListingPhoto.objects.filter(visible, listing__store__suspended=False), listing_id=pk,
    )
    return HttpResponse(bytes(photo.content), content_type="image/jpeg",
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@login_required
@require_POST
def favorite(request, pk):
    store = current_store(request)
    listing = get_object_or_404(Listing, pk=pk, status=Listing.Status.ACTIVE, store__suspended=False)
    if request.POST.get("action") == "remove":
        Favorite.objects.filter(store=store, listing=listing).delete()
    else:
        Favorite.objects.get_or_create(store=store, listing=listing)
    return redirect("dashboard")


@login_required
def report(request, pk):
    store = current_store(request)
    listing = get_object_or_404(Listing, pk=pk, status=Listing.Status.ACTIVE, store__suspended=False)
    form = TextForm(request.POST if request.method == "POST" else None)
    if form.is_valid():
        Report.objects.create(reporter=store, listing=listing, reason=form.cleaned_data["text"])
        messages.success(request, "Denúncia encaminhada para análise.")
        return redirect("listing", pk=pk)
    return render(request, "form.html", {"title": "Denunciar anúncio", "form": form})


@login_required
@transaction.atomic
def propose(request, pk):
    buyer = current_store(request, verified=True)
    check_commerce(buyer)
    target = get_object_or_404(Listing, pk=pk, status=Listing.Status.ACTIVE,
                               store__verified=True, store__suspended=False)
    check_commerce(target.store)
    if target.store_id == buyer.pk:
        raise PermissionDenied
    form = ProposalForm(request.POST if request.method == "POST" else None, store=buyer, target=target)
    fees = rates()
    if form.is_valid():
        offered = form.cleaned_data.get("offered")
        selected = [target] + ([offered] if offered else [])
        locked = list(Listing.objects.filter(pk__in=[item.pk for item in selected])
                      .order_by("pk").select_for_update())
        fields = [field.attname for field in Listing._meta.concrete_fields]
        original = {item.pk: item for item in selected}
        changed = len(locked) != len(selected) or any(
            getattr(item, field) != getattr(original[item.pk], field)
            for item in locked for field in fields
        )
        if changed:
            form.add_error(None, "Um anúncio mudou. Confira as condições antes de enviar.")
            return render(request, "form.html", {"title": f"Proposta · {target.title}",
                                                  "form": form, "proposal_rates": fees})
        amount = form.cleaned_data["amount"]
        fee = fees.swap_fee if offered else (amount * fees.commission / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        deal = Deal.objects.create(buyer=buyer, seller=target.store, target=target,
                                   offered=offered, amount=amount, fee=fee)
        return redirect("deal", pk=deal.pk)
    return render(request, "form.html", {"title": f"Proposta · {target.title}", "form": form,
                                          "proposal_rates": fees})


@login_required
@transaction.atomic
def deal_detail(request, pk):
    store = current_store(request)
    deals = Deal.objects.filter(Q(buyer=store) | Q(seller=store))
    if request.method == "POST":
        deals = deals.select_for_update()
    deal = get_object_or_404(deals, pk=pk)
    seller = deal.seller_id == store.pk
    proposed = deal.status == Deal.Status.PROPOSED
    accepted = deal.status == Deal.Status.ACCEPTED
    form = TextForm()
    if request.method == "POST":
        current_store(request, verified=True)
        action = request.POST.get("action")
        items = Listing.objects.filter(pk__in=[deal.target_id, deal.offered_id])
        if action == "accept" and seller and proposed:
            check_commerce(deal.buyer)
            check_commerce(deal.seller)
            available = items.filter(status=Listing.Status.ACTIVE, store__verified=True, store__suspended=False)
            # Lock both lots in a consistent order before checking availability.
            available_ids = list(available.order_by("pk").select_for_update(of=("self",))
                                 .values_list("pk", flat=True))
            if len(available_ids) != (2 if deal.offered_id else 1):
                messages.error(request, "Uma das peças está indisponível.")
                return redirect("deal", pk=pk)
            items.filter(pk__in=available_ids).update(status=Listing.Status.RESERVED)
            deal.status = Deal.Status.ACCEPTED
        elif action == "cancel" and proposed:
            deal.status = Deal.Status.CANCELLED
        elif action == "dispute" and accepted:
            deal.status = Deal.Status.DISPUTED
        elif action == "received" and accepted:
            if seller:
                deal.seller_received = True
            else:
                deal.buyer_received = True
            if deal.seller_received and deal.buyer_received:
                items.update(status=Listing.Status.SWAPPED if deal.offered_id else Listing.Status.SOLD)
                deal.status = Deal.Status.COMPLETE
                if deal.fee > 0:
                    from datetime import timedelta
                    from django.utils import timezone
                    Invoice.objects.get_or_create(deal=deal, defaults={
                        "store": deal.buyer if deal.offered_id else deal.seller,
                        "kind": Invoice.Kind.SWAP if deal.offered_id else Invoice.Kind.COMMISSION,
                        "reference": f"negociacao-{deal.pk}", "amount": deal.fee,
                        "due_date": timezone.localdate() + timedelta(days=config().fee_due_days),
                    })
        elif action == "message" and (proposed or accepted or deal.status == Deal.Status.DISPUTED):
            form = TextForm(request.POST)
            if form.is_valid():
                Message.objects.create(deal=deal, sender=store, body=form.cleaned_data["text"])
        else:
            raise PermissionDenied
        if not form.errors:
            deal.save()
            return redirect("deal", pk=pk)
    return render(request, "deal.html", {"deal": deal, "seller": seller, "proposed": proposed,
                                          "accepted": accepted, "form": form,
                                          "net": deal.amount - deal.fee,
                                          "chat_open": proposed or accepted or deal.status == Deal.Status.DISPUTED})


def vip(request):
    return render(request, "vip.html", {"rates": rates()})


def check_commerce(store):
    if store.suspended or not store.verified or blocked(store):
        raise PermissionDenied("Loja sem permissão para novas operações. Consulte o financeiro da empresa.")


def brand_logo(request, pk):
    brand = get_object_or_404(CompanyBrand.objects.exclude(logo=None), store_id=pk, enabled=True)
    return HttpResponse(bytes(brand.logo), content_type="image/jpeg",
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@login_required
def company_finance(request):
    store = current_store(request)
    return render(request, "company_finance.html", {
        "store": store, "blocked": blocked(store),
        "vip_active": active_vip().filter(store=store).exists(),
        "invoices": Paginator(store.invoices.order_by("-pk"), 25).get_page(request.GET.get("page")),
    })
