from django import forms
from django.utils import timezone

class ExpensesEntryForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'input'}
        ),
        initial=timezone.now().date()
    )
    description = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'class': 'input', 'placeholder': 'Enter description here...'})
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'input price-input', 'placeholder': 'Enter price here...'})
    )
    paid_by = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'readonly': 'readonly'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['paid_by'].initial = f"{self.user.first_name} {self.user.last_name}"

    def clean_paid_by(self):
        paid_by = self.cleaned_data.get('paid_by')
        expected_name = f"{self.user.first_name} {self.user.last_name}"
        if paid_by != expected_name:
            raise forms.ValidationError("The paid_by field must match the logged-in user.")
        return paid_by

