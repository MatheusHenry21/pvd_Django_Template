from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from .forms import CaixaForm
from .models import Caixa


class OperacaoCaixa(LoginRequiredMixin, TemplateView):

    template_name = 'caixa/operacao.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        caixa = (
            Caixa.objects
            .select_related(
                'usuario_abertura',
                'usuario_fechamento'
            )
            .order_by('-data_abertura')
            .first()
        )

        context['caixa'] = caixa

        return context


class AbrirCaixa(LoginRequiredMixin, CreateView):

    model = Caixa
    form_class = CaixaForm

    template_name = 'caixa/abrir.html'

    success_url = reverse_lazy('caixa:operacao')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['responsavel'] = self.request.user
        context['data_hora'] = timezone.localtime()

        return context

    def dispatch(self, request, *args, **kwargs):

        if Caixa.objects.filter(
            status=Caixa.Status.ABERTO
        ).exists():

            messages.error(
                request,
                'Já existe um caixa aberto.'
            )

            return redirect('caixa:operacao')

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):

        form.instance.usuario_abertura = self.request.user

        form.instance.status = Caixa.Status.ABERTO

        response = super().form_valid(form)

        messages.success(
            self.request,
            'Caixa aberto com sucesso.'
        )

        return response


class HistoricoCaixa(LoginRequiredMixin, ListView):

    model = Caixa

    template_name = 'caixa/historico.html'

    context_object_name = 'caixas'

    def get_queryset(self):

        return (
            Caixa.objects
            .select_related(
                'usuario_abertura',
                'usuario_fechamento'
            )
            .order_by('-data_abertura')
        )