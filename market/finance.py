from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .models import Invoice, PlatformConfig, Store


def config():
    return PlatformConfig.objects.filter(pk=1).first() or PlatformConfig(pk=1)


def blocked(store):
    policy = config()
    return policy.auto_block and store.invoices.filter(
        status=Invoice.Status.OPEN,
        due_date__lt=timezone.localdate() - timedelta(days=policy.grace_days),
    ).exists()


def active_vip():
    today = timezone.localdate()
    return Invoice.objects.filter(kind=Invoice.Kind.VIP, status=Invoice.Status.PAID,
                                  period_start__lte=today, period_end__gte=today)


def total(query):
    return query.aggregate(value=Sum("amount"))["value"] or Decimal("0")


def monthly_series():
    today = timezone.localdate()
    points = []
    for offset in range(11, -1, -1):
        index = today.year * 12 + today.month - 1 - offset
        year, month = divmod(index, 12)
        month += 1
        received = Invoice.objects.filter(paid_at__year=year, paid_at__month=month)
        refunded = Invoice.objects.filter(refunded_at__year=year, refunded_at__month=month)
        points.append({
            "label": f"{month:02d}/{year}", "received": float(total(received)),
            "refunded": float(total(refunded)),
            "lost": float(total(Invoice.objects.filter(lost_at__year=year, lost_at__month=month))),
            "companies": Store.objects.filter(user__date_joined__year=year,
                                              user__date_joined__month=month).count(),
        })
    return points


def projection_series():
    today = timezone.localdate()
    points = []
    for offset in range(3):
        index = today.year * 12 + today.month - 1 + offset
        year, month = divmod(index, 12)
        month += 1
        pending = Invoice.objects.filter(
            status=Invoice.Status.OPEN, due_date__gte=today,
            due_date__year=year, due_date__month=month,
        )
        points.append({"label": f"{month:02d}/{year}", "expected": float(total(pending))})
    return points
