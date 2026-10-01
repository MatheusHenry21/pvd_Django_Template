from django import forms
from .models import Produto

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'codigo',
            'categoria',
            'nome',
            'preco',
            'estoque',
            'ativo',
        ]

        widgets = {
            'codigo': forms.TextInput(
                attrs={
                    'placeholder': '',
                }
            ),

            'categoria': forms.Select(),

            'nome': forms.TextInput(
                attrs={
                    'placeholder': '',
                }
            ),

            'preco': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0',
                }
            ),

            'estoque': forms.NumberInput(
                attrs={
                    'step': '0.001',
                    'min': '0',
                }
            ),

            'ativo': forms.CheckboxInput(),
        }