from django import forms

from .models import Caixa


class CaixaForm(forms.ModelForm):

    class Meta:
        model = Caixa

        fields = ['valor_inicial']

        labels = {
            'valor_inicial': 'Valor inicial (R$)',
        }

        widgets = {
            'valor_inicial': forms.NumberInput(
                attrs={
                    'class': 'caixa-form-input',
                    'placeholder': '0,00',
                    'step': '0.01',
                    'min': '0',
                }
            ),
        }