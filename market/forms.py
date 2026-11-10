import re
from io import BytesIO

from django import forms
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import Listing, Store


class StoreForm(forms.ModelForm):
    cnpj = forms.CharField(label="CNPJ", max_length=18)

    class Meta:
        model = Store
        fields = ("legal_name", "name", "cnpj", "address", "phone", "email", "contact")

    def clean_cnpj(self):
        cnpj = re.sub(r"[./\s-]", "", self.cleaned_data["cnpj"])
        if not re.fullmatch(r"[0-9]{14}", cnpj) or len(set(cnpj)) == 1:
            raise forms.ValidationError("Informe um CNPJ numérico válido.")
        for length, weights in [(12, (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)),
                                (13, (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))]:
            remainder = sum(int(digit) * weight for digit, weight in zip(cnpj, weights)) % 11
            if int(cnpj[length]) != (11 - remainder if remainder >= 2 else 0):
                raise forms.ValidationError("Confira os dígitos do CNPJ.")
        return cnpj


class ListingForm(forms.ModelForm):
    photo_file = forms.FileField(
        label="Foto da peça", required=False,
        help_text="Use uma foto real da peça, em JPEG, PNG ou WebP, de até 5 MB.",
        widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
    )

    def clean_photo_file(self):
        upload = self.cleaned_data["photo_file"]
        if not upload:
            return None
        if upload.size > 5 * 1024 * 1024:
            raise forms.ValidationError("A foto deve ter até 5 MB.")
        try:
            with Image.open(upload, formats=["JPEG", "PNG", "WEBP"]) as source:
                if source.width * source.height > 24_000_000:
                    raise forms.ValidationError("A foto deve ter até 24 megapixels.")
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((1200, 1200))
                output = BytesIO()
                image.save(output, "JPEG", quality=80, optimize=True)
                return output.getvalue()
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError) as error:
            raise forms.ValidationError("Envie uma foto válida em JPEG, PNG ou WebP.") from error

    class Meta:
        model = Listing
        exclude = ("store", "status")


class ProposalForm(forms.Form):
    amount = forms.DecimalField(label="Valor da oferta ou diferença a pagar (R$)",
                                min_value=0, max_digits=10, decimal_places=2)
    offered = forms.ModelChoiceField(label="Peça que sua loja oferece em troca",
                                     queryset=Listing.objects.none(), required=False)

    def __init__(self, *args, store, target, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = target
        self.fields["amount"].initial = target.price
        if target.mode == Listing.Mode.SWAP:
            self.fields["offered"].queryset = store.listings.filter(status=Listing.Status.ACTIVE)
        else:
            self.fields.pop("offered")
        if target.mode == Listing.Mode.SALE:
            self.fields["amount"].disabled = True

    def clean(self):
        data = super().clean()
        if data.get("amount") == 0 and not data.get("offered"):
            self.add_error("amount", "Informe um valor acima de zero para uma venda.")
        return data


class TextForm(forms.Form):
    text = forms.CharField(label="Mensagem", max_length=1000, widget=forms.Textarea(attrs={"rows": 3}))


class CatalogFilters(forms.Form):
    q = forms.CharField(label="Buscar", max_length=120, required=False,
                        widget=forms.TextInput(attrs={"placeholder": "Peça, código, veículo ou cidade"}))
    mode = forms.ChoiceField(label="Negociação", required=False,
                             choices=[("", "Todas"), *Listing.Mode.choices])
    condition = forms.ChoiceField(label="Condição", required=False,
                                  choices=[("", "Todas"), *Listing._meta.get_field("condition").choices])
    max_price = forms.DecimalField(label="Até (R$)", required=False, min_value=0,
                                   max_digits=10, decimal_places=2)
    order = forms.ChoiceField(label="Ordenar", required=False, choices=[
        ("", "Mais recentes"), ("low", "Menor preço"), ("high", "Maior preço"),
    ])
