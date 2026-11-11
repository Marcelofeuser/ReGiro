from django import forms

from .forms import ListingForm
from .models import CompanyBrand, Invoice, PlatformConfig, Store


class CompanyManagementForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ("verified", "suspended")


class BrandForm(forms.ModelForm):
    photo_file = forms.FileField(label="Logotipo", required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}))
    clean_photo_file = ListingForm.clean_photo_file

    class Meta:
        model = CompanyBrand
        fields = ("enabled", "display_name", "color")
        widgets = {"color": forms.TextInput(attrs={"type": "color"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo_file"].label = "Logotipo"
        self.fields["photo_file"].help_text = "JPEG, PNG ou WebP de até 5 MB. A identidade aparece nas telas da empresa."


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ("kind", "reference", "amount", "due_date", "period_start", "period_end")
        widgets = {field: forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
                   for field in ("due_date", "period_start", "period_end")}

    def clean_reference(self):
        value = self.cleaned_data["reference"]
        if value.startswith("negociacao-"):
            raise forms.ValidationError("Este prefixo é reservado às negociações concluídas.")
        return value

    def clean(self):
        data = super().clean()
        start, end = data.get("period_start"), data.get("period_end")
        if data.get("kind") == Invoice.Kind.VIP and (not start or not end):
            raise forms.ValidationError("Defina o início e o fim do período VIP.")
        if start and end and start > end:
            raise forms.ValidationError("O fim do período deve ser igual ou posterior ao início.")
        if data.get("kind") != Invoice.Kind.VIP and (start or end):
            raise forms.ValidationError("O período de benefícios é exclusivo da mensalidade VIP.")
        return data


class ConfigForm(forms.ModelForm):
    class Meta:
        model = PlatformConfig
        fields = ("auto_block", "grace_days", "fee_due_days", "vip_price")
