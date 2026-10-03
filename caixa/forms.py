from django import forms

from .models import Caixa, MovimentacaoCaixa


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

class MovimentacaoCaixaForm(forms.ModelForm):

    class Meta:
        model = MovimentacaoCaixa

        fields = [
            'valor',
            'descricao',
            'observacao',
        ]

        labels = {
            'valor': 'Valor do suprimento (R$)',
            'descricao': 'Motivo / Descrição',
            'observacao': 'Observação complementar',
        }

        widgets = {
            'valor': forms.NumberInput(attrs={
                'class': 'caixa-form-input',
                'placeholder': '0,00',
                'step': '0.01',
                'min': '0.01',
            }),

            'descricao': forms.TextInput(attrs={
                'class': 'caixa-form-input',
                'placeholder': 'Ex: Reforço de caixa, Troco para operação...',
            }),

            'observacao': forms.Textarea(attrs={
                'class': 'caixa-form-input caixa-form-textarea',
                'placeholder': 'Opcional...',
                'rows': 3,
            }),
        }

class SangriaForm(forms.ModelForm):

    class Meta:
        model = MovimentacaoCaixa

        fields = [
            'valor',
            'descricao',
            'observacao',
        ]

        labels = {
            'valor': 'Valor a retirar (R$)',
            'descricao': 'Finalidade / Destino',
            'observacao': 'Observação',
        }

        widgets = {
            'valor': forms.NumberInput(
                attrs={
                    'class': 'caixa-form-input',
                    'placeholder': '0,00',
                    'step': '0.01',
                    'min': '0.01',
                }
            ),

            'descricao': forms.TextInput(
                attrs={
                    'class': 'caixa-form-input',
                    'placeholder': (
                        'Ex: Pagamento fornecedor, Conta de luz, Material...'
                    ),
                }
            ),

            'observacao': forms.Textarea(
                attrs={
                    'class': 'caixa-form-input caixa-form-textarea',
                    'placeholder': (
                        'Opcional — número de NF, nome do fornecedor, etc.'
                    ),
                }
            ),
        }