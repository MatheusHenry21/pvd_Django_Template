from decimal import Decimal
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Prefetch, Sum, Q, Count
from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import CaixaForm, MovimentacaoCaixaForm, SangriaForm, FechamentoCaixaForm
from .models import Caixa, MovimentacaoCaixa
from vendas.models import Venda

class OperacaoCaixaView(LoginRequiredMixin, TemplateView):

    template_name = 'caixa/operacao.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        caixa = (
            Caixa.objects
            .filter(
                status=Caixa.Status.ABERTO
            )
            .select_related('usuario_abertura')
            .order_by('-data_abertura')
            .first()
        )

        context['caixa'] = caixa

        if not caixa:
            context['vendas'] = Venda.objects.none()
            context['total_vendas'] = Decimal('0.00')
            context['total_entradas'] = Decimal('0.00')
            context['total_saidas'] = Decimal('0.00')
            context['saldo_atual'] = Decimal('0.00')
            context['movimentacoes'] = []

            return context

        vendas = (
            Venda.objects
            .filter(
                caixa=caixa,
                status=Venda.Status.FINALIZADA
            )
            .select_related('usuario')
            .order_by('-data')
        )

        total_vendas = (
            vendas.aggregate(
                total=Sum('total')
            )['total']
            or Decimal('0.00')
        )

        suprimentos = (
            MovimentacaoCaixa.objects
            .filter(
                caixa=caixa,
                tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO
            )
            .select_related('usuario')
            .order_by('-data')
        )

        total_suprimentos = (
            suprimentos.aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        sangrias = (
            MovimentacaoCaixa.objects
            .filter(
                caixa=caixa,
                tipo=MovimentacaoCaixa.Tipo.SANGRIA
            )
            .select_related('usuario')
            .order_by('-data')
        )

        total_sangrias = (
            sangrias.aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        total_entradas = (
            total_vendas
            + total_suprimentos
        )

        total_saidas = total_sangrias

        saldo_atual = (
            caixa.valor_inicial
            + total_entradas
            - total_saidas
        )

        movimentacoes = []

        for venda in vendas:
            movimentacoes.append({
                'data': venda.data,
                'descricao': f'Venda #{venda.id:05d}',
                'tipo': 'VENDA',
                'valor': venda.total,
                'entrada': True,
            })

        for suprimento in suprimentos:
            movimentacoes.append({
                'data': suprimento.data,
                'descricao': suprimento.descricao,
                'tipo': 'SUPRIMENTO',
                'valor': suprimento.valor,
                'entrada': True,
            })

        for sangria in sangrias:
            movimentacoes.append({
                'data': sangria.data,
                'descricao': sangria.descricao,
                'tipo': 'SANGRIA',
                'valor': sangria.valor,
                'entrada': False,
            })

        movimentacoes.sort(
            key=lambda movimentacao: movimentacao['data'],
            reverse=True
        )

        paginator = Paginator(
            movimentacoes,
            15
        )

        pagina = self.request.GET.get('page')

        movimentacoes_paginadas = paginator.get_page(pagina)

        context['vendas'] = vendas
        context['total_vendas'] = total_vendas
        context['total_entradas'] = total_entradas
        context['total_saidas'] = total_saidas
        context['saldo_atual'] = saldo_atual
        context['movimentacoes'] = movimentacoes_paginadas
        context['page_obj'] = movimentacoes_paginadas

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

    def get_periodo(self):

        periodo = self.request.GET.get(
            'periodo',
            'semana'
        )

        hoje = timezone.localdate()

        if periodo == 'mes':

            inicio = hoje.replace(
                day=1
            )

            if inicio.month == 12:

                fim = inicio.replace(
                    year=inicio.year + 1,
                    month=1
                )

            else:

                fim = inicio.replace(
                    month=inicio.month + 1
                )

        elif periodo == 'ano':

            inicio = hoje.replace(
                month=1,
                day=1
            )

            fim = inicio.replace(
                year=inicio.year + 1
            )

        else:

            # Semana começando na segunda-feira
            inicio = hoje - timedelta(
                days=hoje.weekday()
            )

            fim = inicio + timedelta(
                days=7
            )

            periodo = 'semana'

        inicio_datetime = timezone.make_aware(
            datetime.combine(
                inicio,
                datetime.min.time()
            )
        )

        fim_datetime = timezone.make_aware(
            datetime.combine(
                fim,
                datetime.min.time()
            )
        )

        return (
            periodo,
            inicio,
            fim,
            inicio_datetime,
            fim_datetime
        )

    def get_queryset(self):

        (
            periodo,
            inicio,
            fim,
            inicio_datetime,
            fim_datetime
        ) = self.get_periodo()

        queryset = (
            Caixa.objects
            .filter(
                status=Caixa.Status.FECHADO,
                data_abertura__gte=inicio_datetime,
                data_abertura__lt=fim_datetime
            )
            .select_related(
                'usuario_abertura',
                'usuario_fechamento'
            )
            .prefetch_related(
                Prefetch(
                    'vendas',
                    queryset=Venda.objects.filter(
                        status=Venda.Status.FINALIZADA
                    ),
                    to_attr='vendas_finalizadas'
                ),
                Prefetch(
                    'movimentacoes',
                    to_attr='movimentacoes_historico'
                )
            )
        )

        busca = self.request.GET.get(
            'busca',
            ''
        ).strip()

        if busca:

            filtro = (
                Q(
                    usuario_abertura__first_name__icontains=busca
                )
                |
                Q(
                    usuario_abertura__last_name__icontains=busca
                )
                |
                Q(
                    usuario_abertura__username__icontains=busca
                )
                |
                Q(
                    usuario_fechamento__first_name__icontains=busca
                )
                |
                Q(
                    usuario_fechamento__last_name__icontains=busca
                )
                |
                Q(
                    usuario_fechamento__username__icontains=busca
                )
            )

            try:

                data_busca = datetime.strptime(
                    busca,
                    '%d/%m/%Y'
                ).date()

                filtro |= Q(
                    data_abertura__date=data_busca
                )

                filtro |= Q(
                    data_fechamento__date=data_busca
                )

            except ValueError:

                pass

            queryset = queryset.filter(filtro)

        return queryset.order_by('-data_abertura')
    
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        (
            periodo,
            inicio,
            fim,
            inicio_datetime,
            fim_datetime
        ) = self.get_periodo()

        # ========================================
        # TOTAL FATURADO
        # SOMENTE VENDAS DE CAIXAS FECHADOS
        # ========================================

        total_faturado = (
            Venda.objects
            .filter(
                caixa__status=Caixa.Status.FECHADO,
                status=Venda.Status.FINALIZADA,
                data__gte=inicio_datetime,
                data__lt=fim_datetime
            )
            .aggregate(
                total=Sum('total')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # TOTAL DE SUPRIMENTOS
        # SOMENTE CAIXAS FECHADOS
        # ========================================

        total_suprimentos = (
            MovimentacaoCaixa.objects
            .filter(
                caixa__status=Caixa.Status.FECHADO,
                tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO,
                data__gte=inicio_datetime,
                data__lt=fim_datetime
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # TOTAL DE SANGRIAS
        # SOMENTE CAIXAS FECHADOS
        # ========================================

        total_sangrias = (
            MovimentacaoCaixa.objects
            .filter(
                caixa__status=Caixa.Status.FECHADO,
                tipo=MovimentacaoCaixa.Tipo.SANGRIA,
                data__gte=inicio_datetime,
                data__lt=fim_datetime
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # CONTEXTO
        # ========================================

        context['total_faturado'] = total_faturado

        context['total_suprimentos'] = total_suprimentos

        context['total_sangrias'] = total_sangrias

        context['periodo'] = periodo

        context['data_inicio'] = inicio

        context['data_fim'] = fim - timedelta(
            days=1
        )

        for caixa in context['caixas']:

            vendas = caixa.vendas_finalizadas
            movimentacoes = caixa.movimentacoes_historico

            # ========================================
            # VENDAS
            # ========================================

            caixa.total_vendas = len(vendas)

            caixa.faturamento = sum(
                (venda.total for venda in vendas),
                Decimal('0.00')
            )

            # ========================================
            # MOVIMENTAÇÕES
            # ========================================

            caixa.total_suprimentos = sum(
                (
                    movimentacao.valor
                    for movimentacao in movimentacoes
                    if movimentacao.tipo == MovimentacaoCaixa.Tipo.SUPRIMENTO
                ),
                Decimal('0.00')
            )

            caixa.total_sangrias = sum(
                (
                    movimentacao.valor
                    for movimentacao in movimentacoes
                    if movimentacao.tipo == MovimentacaoCaixa.Tipo.SANGRIA
                ),
                Decimal('0.00')
            )

            # ========================================
            # SALDO ESPERADO
            # ========================================

            caixa.saldo_esperado = (
                caixa.valor_inicial
                + caixa.faturamento
                + caixa.total_suprimentos
                - caixa.total_sangrias
            )

            # ========================================
            # SALDO FINAL
            # ========================================

            caixa.saldo_final = (
                caixa.valor_final
                or Decimal('0.00')
            )

            # ========================================
            # DIFERENÇA
            # ========================================

            caixa.diferenca = (
                caixa.saldo_final
                - caixa.saldo_esperado
            )

            if caixa.diferenca > 0:

                caixa.diferenca_tipo = 'positiva'

            elif caixa.diferenca < 0:

                caixa.diferenca_tipo = 'negativa'

            else:

                caixa.diferenca_tipo = 'zero'

        return context
      
class SuprimentoCaixaView(LoginRequiredMixin, CreateView):

    model = MovimentacaoCaixa
    form_class = MovimentacaoCaixaForm
    template_name = 'caixa/suprimento.html'
    success_url = reverse_lazy('caixa:operacao')

    def get_caixa(self):
        return Caixa.objects.filter(
            status=Caixa.Status.ABERTO
        ).first()

    def dispatch(self, request, *args, **kwargs):

        if not self.get_caixa():
            return redirect('caixa:operacao')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        caixa = self.get_caixa()

        vendas = caixa.vendas.filter(
            status=Venda.Status.FINALIZADA
        ).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        suprimentos = caixa.movimentacoes.filter(
            tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO
        ).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')

        sangrias = caixa.movimentacoes.filter(
            tipo=MovimentacaoCaixa.Tipo.SANGRIA
        ).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')

        saldo_atual = (
            caixa.valor_inicial
            + vendas
            + suprimentos
            - sangrias
        )

        context['caixa'] = caixa
        context['saldo_atual'] = saldo_atual
        context['responsavel'] = self.request.user

        return context

    def form_valid(self, form):
        form.instance.caixa = self.get_caixa()
        form.instance.usuario = self.request.user
        form.instance.tipo = MovimentacaoCaixa.Tipo.SUPRIMENTO

        response = super().form_valid(form)

        valor_formatado = (
            f'{self.object.valor:,.2f}'
            .replace(',', 'X')
            .replace('.', ',')
            .replace('X', '.')
        )

        messages.success(
            self.request,
            f'Suprimento de R$ {valor_formatado} registrado.'
        )

        return response

    def form_invalid(self, form):
        if not self.request.POST.get('descricao', '').strip():
            messages.error(
                self.request,
                'Informe o motivo do suprimento.'
            )

        return super().form_invalid(form)

class SangriaCaixaView(LoginRequiredMixin, CreateView):
    model = MovimentacaoCaixa
    form_class = SangriaForm
    template_name = 'caixa/sangria.html'
    success_url = reverse_lazy('caixa:operacao')

    def dispatch(self, request, *args, **kwargs):
        self.caixa = Caixa.objects.filter(
            status=Caixa.Status.ABERTO
        ).first()

        if not self.caixa:
            return redirect('caixa:operacao')

        return super().dispatch(request, *args, **kwargs)

    def get_saldo_atual(self):
        total_vendas = (
            self.caixa.vendas
            .filter(status=Venda.Status.FINALIZADA)
            .aggregate(total=Sum('total'))['total']
            or Decimal('0.00')
        )

        total_suprimentos = (
            self.caixa.movimentacoes
            .filter(tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO)
            .aggregate(total=Sum('valor'))['total']
            or Decimal('0.00')
        )

        total_sangrias = (
            self.caixa.movimentacoes
            .filter(tipo=MovimentacaoCaixa.Tipo.SANGRIA)
            .aggregate(total=Sum('valor'))['total']
            or Decimal('0.00')
        )

        return (
            self.caixa.valor_inicial
            + total_vendas
            + total_suprimentos
            - total_sangrias
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['caixa'] = self.caixa
        context['saldo_atual'] = self.get_saldo_atual()
        return context

    def form_valid(self, form):
        valor_sangria = form.cleaned_data['valor']
        saldo_atual = self.get_saldo_atual()

        if valor_sangria > saldo_atual:
            form.add_error(
                'valor',
                f'A sangria não pode ser maior que o saldo disponível de R$ {saldo_atual:.2f}.'
            )
            return self.form_invalid(form)

        form.instance.caixa = self.caixa
        form.instance.usuario = self.request.user
        form.instance.tipo = MovimentacaoCaixa.Tipo.SANGRIA

        response = super().form_valid(form)

        valor_formatado = (
            f'{self.object.valor:,.2f}'
            .replace(',', 'X')
            .replace('.', ',')
            .replace('X', '.')
        )

        messages.success(
            self.request,
            f'Sangria de R$ {valor_formatado} registrada.'
        )

        return response

class FecharCaixaView(LoginRequiredMixin, UpdateView):
    model = Caixa
    form_class = FechamentoCaixaForm
    template_name = 'caixa/fechar.html'
    success_url = reverse_lazy('caixa:operacao')

    def get_object(self, queryset=None):
        return (
            Caixa.objects
            .filter(status=Caixa.Status.ABERTO)
            .order_by('-data_abertura')
            .first()
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object():
            messages.error(
                request,
                'Não existe nenhum caixa aberto.'
            )
            return redirect('caixa:operacao')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        caixa = self.object

        total_vendas = (
            caixa.vendas
            .filter(status=Venda.Status.FINALIZADA)
            .aggregate(total=Sum('total'))['total']
            or Decimal('0.00')
        )

        total_suprimentos = (
            caixa.movimentacoes
            .filter(tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO)
            .aggregate(total=Sum('valor'))['total']
            or Decimal('0.00')
        )

        total_sangrias = (
            caixa.movimentacoes
            .filter(tipo=MovimentacaoCaixa.Tipo.SANGRIA)
            .aggregate(total=Sum('valor'))['total']
            or Decimal('0.00')
        )

        saldo_esperado = (
            caixa.valor_inicial
            + total_vendas
            + total_suprimentos
            - total_sangrias
        )

        context['caixa'] = caixa
        context['saldo_esperado'] = saldo_esperado
        return context

    def form_valid(self, form):
        form.instance.usuario_fechamento = self.request.user
        form.instance.data_fechamento = timezone.now()
        form.instance.status = Caixa.Status.FECHADO

        response = super().form_valid(form)

        messages.success(
            self.request,
            'Caixa fechado com sucesso.'
        )

        return response
    
class FecharCaixaView(LoginRequiredMixin, UpdateView):

    model = Caixa
    form_class = FechamentoCaixaForm
    template_name = 'caixa/fechar.html'
    success_url = reverse_lazy('caixa:operacao')

    def get_object(self, queryset=None):

        return (
            Caixa.objects
            .filter(
                status=Caixa.Status.ABERTO
            )
            .order_by('-data_abertura')
            .first()
        )

    def dispatch(self, request, *args, **kwargs):

        if not self.get_object():

            messages.error(
                request,
                'Não existe nenhum caixa aberto.'
            )

            return redirect('caixa:operacao')

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        caixa = self.object

        # ========================================
        # VENDAS
        # ========================================

        total_vendas = (
            caixa.vendas
            .filter(
                status=Venda.Status.FINALIZADA
            )
            .aggregate(
                total=Sum('total')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # SUPRIMENTOS
        # ========================================

        total_suprimentos = (
            caixa.movimentacoes
            .filter(
                tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # SANGRIAS
        # ========================================

        total_sangrias = (
            caixa.movimentacoes
            .filter(
                tipo=MovimentacaoCaixa.Tipo.SANGRIA
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # SALDO ESPERADO
        # ========================================

        saldo_esperado = (
            caixa.valor_inicial
            + total_vendas
            + total_suprimentos
            - total_sangrias
        )

        context['caixa'] = caixa
        context['saldo_esperado'] = saldo_esperado

        return context

    def form_valid(self, form):
        valor_sangria = form.cleaned_data['valor']
        saldo_atual = self.get_saldo_atual()

        if valor_sangria > saldo_atual:
            form.add_error(
                'valor',
                f'A sangria não pode ser maior que o saldo disponível de R$ {saldo_atual:.2f}.'
            )

            return self.form_invalid(form)

        form.instance.caixa = self.caixa
        form.instance.usuario = self.request.user
        form.instance.tipo = MovimentacaoCaixa.Tipo.SANGRIA

        response = super().form_valid(form)

        valor_formatado = (
            f'{self.object.valor:,.2f}'
            .replace(',', 'X')
            .replace('.', ',')
            .replace('X', '.')
        )

        messages.success(
            self.request,
            f'Sangria de R$ {valor_formatado} registrada.'
        )

        return response