from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django.contrib.auth.views import LoginView
from .forms import CustomAuthenticationForm

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from .check_permissions import is_producer

from django.forms import modelformset_factory, widgets
from .models import SalesOffer, ProductionCapacity, Plan, PurchaseOffer, User, Period, Sale, Buying,  Solution

from django.core.exceptions import ObjectDoesNotExist
from .forms import SalesOfferForm, PurchaseOfferForm, setDemandFormSet, ProductionCapacityFormSet

from .check_permissions import is_producer, is_buyer

from django.urls import reverse_lazy
from scm_project.settings import BASE_DIR

from .serializers import PlanSerializer, SolutionSerializer
from rest_framework import viewsets

from django.db.models.expressions import RawSQL

import datetime

# Create your views here.

from django.template.defaulttags import register

@register.filter
def get_range(value):
    return range(value)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

class StartPage(TemplateView):
    template_name = "home.html"


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm


class HomePage(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = "profile.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user.username
        context['user_type'] = self.request.user.user_type
        return context


class PlanListView(LoginRequiredMixin, ListView):
    model = Plan
    context_object_name = 'plan_list'
    template_name = 'plans.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cur_user_id = self.request.user.id
        #for those plans user has already made an offer
        if is_producer(self.request.user):
            context['my_plans'] = Plan.objects.filter(sales_offers__producer_id=cur_user_id)  
            context['my_offers'] = SalesOffer.objects.filter(producer_id=cur_user_id)
        if is_buyer(self.request.user):
            context['my_plans'] = Plan.objects.filter(purchase_offers__buyer_id=cur_user_id)  
            context['my_offers'] = PurchaseOffer.objects.filter(buyer_id=cur_user_id)
        return context


class PlanDetailView(LoginRequiredMixin, DetailView):
    model = Plan
    template_name = 'plan_details.html'


class AddSalesOfferView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SalesOffer
    template_name = 'index.html'
    form_class = SalesOfferForm
    def test_func(self):
        # czy użytkownik jest producentem
        if not is_producer(self.request.user):
            return False
        # czy plan ma status: rozpoczęto składanie ofert
        plan = Plan.objects.get(pk=self.kwargs['plan']) 
        if not plan.calculate_plan_status() == 'rozpoczęto składanie ofert':
            return False
        return True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["formset_title"] = "Zdolności produkcyjne"
        if self.request.POST:
            data["offer_details"] = ProductionCapacityFormSet(self.request.POST)
        else:
            data["offer_details"] = ProductionCapacityFormSet()
        return data

    def form_valid(self, form):
        form.instance.producer = self.request.user
        form.instance.plan = Plan.objects.get(id=self.kwargs['plan'])
        context = self.get_context_data()
        capacities = context["offer_details"]
        self.object = form.save()
        if capacities.is_valid():
            capacities.instance = self.object
            capacities.save()
        return super().form_valid(form)

    def get_success_url(self):
        # return reverse('plans')
        return reverse_lazy('sales_offer_details', kwargs={'pk': self.object.pk})


class UpdateSalesOfferView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SalesOffer
    template_name = 'index.html'
    form_class = SalesOfferForm

    def test_func(self):
        # czy użytkownik jest producentem
        if not is_producer(self.request.user):
            return False
        # czy plan ma status: rozpoczęto składanie ofert
        plan = Plan.objects.get(sales_offers__id=self.kwargs['pk']) 
        if not plan.calculate_plan_status() == 'rozpoczęto składanie ofert':
            print("niespełniony warunek")
            return False
        # czy to jest oferta sprzedaży zalogowanego użytkownika
        sale_offer = SalesOffer.objects.get(id=self.kwargs['pk'])
        if not sale_offer.producer == self.request.user:
            return False
        return True
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["formset_title"] = "Zdolności produkcyjne"
        if self.request.POST:
            data["offer_details"] = ProductionCapacityFormSet(self.request.POST, instance=self.object)
        else:
            data["offer_details"] = ProductionCapacityFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        # form.instance.producer = self.request.user
        # form.instance.plan = Plan.objects.get(id=self.kwargs['plan'])
        context = self.get_context_data()
        capacities = context["offer_details"]
        self.object = form.save()
        if capacities.is_valid():
            capacities.instance = self.object
            capacities.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sales_offer_details', kwargs={'pk': self.object.pk})


class SalesOfferDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        # czy użytkownik jest producentem
        if not is_producer(self.request.user):
            return False
        # czy to jest oferta sprzedaży zalogowanego użytkownika
        sale_offer = SalesOffer.objects.get(id=self.kwargs['pk'])
        if not sale_offer.producer == self.request.user:
            return False
        return True

    model = SalesOffer
    template_name = 'sales_offer_details.html'


class DeleteSalesOfferView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    def test_func(self):
        # czy użytkownik jest producentem
        if not is_producer(self.request.user):
            return False
        # czy to jest oferta sprzedaży zalogowanego użytkownika
        sale_offer = SalesOffer.objects.get(id=self.kwargs['pk'])
        if not sale_offer.producer == self.request.user:
            return False
        return True
    model = SalesOffer
    template_name = 'salesoffer_confirm_delete.html'
    success_url = reverse_lazy('plans')


class AddPurchaseOfferView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PurchaseOffer
    template_name = 'index.html'
    form_class = PurchaseOfferForm
    def test_func(self):
        # czy użytkownik jest nabywcą
        if not is_buyer(self.request.user):
            return False
        # czy plan ma status: rozpoczęto składanie ofert
        plan = Plan.objects.get(pk=self.kwargs['plan']) 
        if not plan.calculate_plan_status() == 'rozpoczęto składanie ofert':
            print("niespełniony warunek")
            return False
        return True
    
    def get_context_data(self, **kwargs):
        num_of_demands = Plan.objects.get(id=self.kwargs['plan']).periods_amount
        DemandFormSet = setDemandFormSet(num_of_demands)
        data = super().get_context_data(**kwargs)
        data["formset_title"] = "Zapotrzebowanie"
        if self.request.POST:
            data["offer_details"] = DemandFormSet(self.request.POST)
        else:
            data["offer_details"] = DemandFormSet()
        return data

    def form_valid(self, form):
        form.instance.buyer = self.request.user
        form.instance.plan = Plan.objects.get(id=self.kwargs['plan'])
        context = self.get_context_data()
        demands = context["offer_details"]
        self.object = form.save()
        if demands.is_valid():
            demands.instance = self.object
            demands.save()
        return super().form_valid(form)

    def get_success_url(self):
        # return reverse('plans')
        return reverse_lazy('purchase_offer_details', kwargs={'pk': self.object.pk})


class UpdatePurchaseOfferView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PurchaseOffer
    template_name = 'index.html'
    form_class = PurchaseOfferForm
    def test_func(self):
        # czy użytkownik jest nabywcą
        if not is_buyer(self.request.user):
            return False
        # czy plan ma status: rozpoczęto składanie ofert
        plan = Plan.objects.get(purchase_offers__id=self.kwargs['pk']) 
        if not plan.calculate_plan_status() == 'rozpoczęto składanie ofert':
            print("niespełniony warunek")
            return False
        # czy to jest oferta kupna zalogowanego użytkownika
        purchase_offer = PurchaseOffer.objects.get(id=self.kwargs['pk'])
        if not purchase_offer.buyer == self.request.user:
            return False
        return True
    
    def get_context_data(self, **kwargs):
        DemandFormSet = setDemandFormSet(4)
        data = super().get_context_data(**kwargs)
        data["formset_title"] = "Zapotrzebowanie"
        if self.request.POST:
            data["offer_details"] = DemandFormSet(self.request.POST, instance=self.object)
        else:
            data["offer_details"] = DemandFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        demands = context["offer_details"]
        self.object = form.save()
        if demands.is_valid():
            demands.instance = self.object
            demands.save()
        return super().form_valid(form)

    def get_success_url(self):
        # return reverse('plans')
        return reverse_lazy('purchase_offer_details', kwargs={'pk': self.object.pk})


class PurchaseOfferDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        # czy użytkownik jest nabywcą
        if not is_buyer(self.request.user):
            return False
        # czy to jest oferta kupna zalogowanego użytkownika
        purchase_offer = PurchaseOffer.objects.get(id=self.kwargs['pk'])
        if not purchase_offer.buyer == self.request.user:
            return False
        return True

    model = PurchaseOffer
    template_name = 'purchase_offer_details.html'


class DeletePurchaseOfferView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    def test_func(self):
        # czy użytkownik jest nabywcą
        if not is_buyer(self.request.user):
            return False
        # czy to jest oferta kupna zalogowanego użytkownika
        purchase_offer = PurchaseOffer.objects.get(id=self.kwargs['pk'])
        if not purchase_offer.buyer == self.request.user:
            return False
        return True
    model = PurchaseOffer
    template_name = 'purchaseoffer_confirm_delete.html'
    success_url = reverse_lazy('plans')


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class SolutionViewSet(viewsets.ModelViewSet):
    queryset = Solution.objects.all()
    serializer_class = SolutionSerializer


class SchedulesView(LoginRequiredMixin, ListView):
    model = Solution
    context_object_name = 'schedule_list'
    template_name = 'schedule.html'

    def test_func(self):
        # czy użytkownik jest nabywcą lub producentem
        if not (is_buyer(self.request.user) or is_producer(self.request.user)):
            return False
        return True
    def get_context_data(self, **kwargs):
        context = super(SchedulesView, self).get_context_data(**kwargs)
        cur_user_id = self.request.user.id
        # context['scheduled_plans'] = Plan.objects.raw('select p.id from scm_app_plan p right join scm_app_solution s on p.id=s.plan_id')
        if is_producer(self.request.user):
            context['my_schedules'] = Solution.objects.filter(solution_periods__sales__producer=cur_user_id).distinct()
        if is_buyer(self.request.user):
            context['my_schedules'] = Solution.objects.filter(solution_periods__purchases__buyer=cur_user_id).distinct()
        context['scheduled_plans'] = Plan.objects.raw(""" select * from
                                    scm_app_solution harm left join scm_app_plan p 
                                    on harm.plan_id=p.id
                                    join public."SalesOffer" s 
                                    on p.id=s.plan_id
                                    join scm_app_user u
                                    on s.producer_id=u.id' """)
        context['schedules'] = Solution.objects.raw(""" select * from
                                    scm_app_solution harm left join scm_app_plan p 
                                    on harm.plan_id=p.id
                                    join public."SalesOffer" s 
                                    on p.id=s.plan_id
                                    join scm_app_user u
                                    on s.producer_id=u.id """)

        return context



class ScheduleDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        # czy użytkownik był uwzględniany w danym harmonogramie
        buyers = User.objects.filter(purchases__period__solution__id=self.kwargs['pk']).distinct()
        producers = User.objects.filter(sales__period__solution__id=self.kwargs['pk']).distinct()
        if not ((self.request.user in buyers) or (self.request.user in producers)):
            return False
        return True

    model = Solution
    template_name = 'schedule_2.html'

    def get_context_data(self, **kwargs):
        context = super(ScheduleDetailView, self).get_context_data(**kwargs)
        plan_is_public = Plan.objects.get(solution__id=self.kwargs['pk']).is_public()
        context['plan_is_public'] = plan_is_public 
        if plan_is_public:
            context['periods']=Period.objects.filter(solution__id=self.kwargs['pk'])
            context['number_of_periods']=Period.objects.filter(solution__id=self.kwargs['pk']).count()
            context['number_of_prod'] = Sale.objects.filter(period__solution__id=self.kwargs['pk']).count()
            context['number_of_buyers'] = Buying.objects.filter(period__solution__id=self.kwargs['pk']).count()
            
            buyers_set = User.objects.filter(purchases__period__solution__id=self.kwargs['pk']).distinct()
            buyers_dict={}
            for buyer in buyers_set:
                buyers_dict[buyer] = Buying.objects.filter(period__solution__id=self.kwargs['pk']).filter(buyer=buyer)

            context['buyers_dict']=buyers_dict

            producers_set = User.objects.filter(sales__period__solution__id=self.kwargs['pk']).distinct()
            producers_dict={}
            for producer in producers_set:
                producers_dict[producer] = Sale.objects.filter(period__solution__id=self.kwargs['pk']).filter(producer=producer)

            context['producers_dict']=producers_dict

        else:
            if is_producer(self.request.user):
                context['user_type'] = 'producer'
                context['user_data'] = Sale.objects.filter(period__solution__id=self.kwargs['pk'])
            if is_buyer(self.request.user):
                context['user_type'] = 'buyer'
                context['user_data'] = Buying.objects.filter(period__solution__id=self.kwargs['pk'])
        
        return context