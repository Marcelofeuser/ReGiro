from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Store(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    legal_name = models.CharField("Razão social", max_length=160)
    name = models.CharField("Nome fantasia", max_length=120)
    cnpj = models.CharField("CNPJ", max_length=14, unique=True)
    address = models.CharField("Endereço comercial", max_length=200)
    phone = models.CharField("Telefone", max_length=25)
    email = models.EmailField("E-mail")
    contact = models.CharField("Responsável", max_length=120)
    verified = models.BooleanField("Verificada", default=False)
    suspended = models.BooleanField("Suspensa", default=False)

    def __str__(self):
        return self.name


class Listing(models.Model):
    class Mode(models.TextChoices):
        SALE = "sale", "Venda direta"
        OFFER = "offer", "Aceito oferta"
        SWAP = "swap", "Aceito troca"

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        RESERVED = "reserved", "Reservado"
        SOLD = "sold", "Vendido"
        SWAPPED = "swapped", "Trocado"
        CLOSED = "closed", "Encerrado"

    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField("Título", max_length=120)
    description = models.TextField("Descrição", max_length=3000)
    category = models.CharField("Categoria", max_length=80)
    manufacturer = models.CharField("Fabricante", max_length=80)
    code = models.CharField("Código da peça", max_length=80)
    oem = models.CharField("Referência OEM", max_length=80, blank=True)
    vehicle = models.CharField("Aplicação (marca, modelo, ano, motor e versão)", max_length=180, blank=True)
    condition = models.CharField("Condição", max_length=25, choices=[
        (value, value) for value in ("Nova lacrada", "Nova sem embalagem", "Usada revisada", "Usada no estado")
    ])
    quantity = models.PositiveIntegerField("Quantidade", validators=[MinValueValidator(1)])
    price = models.DecimalField("Preço em R$", max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    city = models.CharField("Cidade e UF", max_length=100)
    delivery = models.CharField("Entrega ou retirada", max_length=160)
    provenance = models.TextField("Nota fiscal, garantia e procedência", max_length=1000)
    reason = models.CharField("Motivo do anúncio", max_length=100, blank=True)
    mode = models.CharField("Negociação", max_length=8, choices=Mode, default=Mode.SALE)
    status = models.CharField(max_length=10, choices=Status, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Rates(models.Model):
    commission = models.DecimalField("Comissão (%)", max_digits=5, decimal_places=2, default=6,
        validators=[MinValueValidator(0), MaxValueValidator(100)])
    swap_fee = models.DecimalField("Tarifa de troca (R$)", max_digits=8, decimal_places=2, default=10,
        validators=[MinValueValidator(0)])

    def __str__(self):
        return "Tarifas ReGiro"


class Deal(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposta enviada"
        ACCEPTED = "accepted", "Aceita"
        COMPLETE = "complete", "Concluída"
        CANCELLED = "cancelled", "Cancelada"
        DISPUTED = "disputed", "Em disputa"

    buyer = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="outgoing")
    seller = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="incoming")
    target = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="proposals")
    offered = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="offers", null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status, default=Status.PROPOSED)
    buyer_received = models.BooleanField(default=False)
    seller_received = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(Store, on_delete=models.PROTECT)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    reporter = models.ForeignKey(Store, on_delete=models.PROTECT)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT)
    reason = models.TextField(max_length=1000)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Favorite(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["store", "listing"], name="unique_favorite")]


class ListingPhoto(models.Model):
    listing = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name="photo")
    content = models.BinaryField(editable=False)
