from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import (User, Plan, SalesOffer, PurchaseOffer, Demand, ProductionCapacity, 
    Solution, Period, Buying, Sale)
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.html import format_html
from .forms import PlanAdminForm


producers, created = Group.objects.get_or_create(name='Producers')
buyers, created = Group.objects.get_or_create(name='Buyers')

class MyUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'id', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

    add_form = UserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'user_type', 'password1', 'password2')}
        ),
    )


admin.site.register(User, MyUserAdmin)

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    form = PlanAdminForm
    list_display = ('name', 'status', 'administrator', 'is_public', 'sales_offers_link', 'purchase_offers_link')
    def sales_offers_link(self, obj):
        count = obj.sales_offers.count()
        url = (
            reverse("admin:scm_app_salesoffer_changelist")
            + "?"
            + urlencode({"plan__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} ofert</a>', url, count)
    def purchase_offers_link(self, obj):
        count = obj.purchase_offers.count()
        url = (
            reverse("admin:scm_app_purchaseoffer_changelist")
            + "?"
            + urlencode({"plan__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} ofert</a>', url, count)
    sales_offers_link.short_description = "oferty sprzedaży"
    purchase_offers_link.short_description = "oferty kupna"

@admin.register(SalesOffer)
class SalesOfferAdmin(admin.ModelAdmin):
    list_display = ('id','plan', 'number', 'producer', 'production_capacities')
    def production_capacities(self, obj):
        count = obj.production_capacities.count()
        url = (
            reverse("admin:scm_app_productioncapacity_changelist")
            + "?"
            + urlencode({"sales_offer__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{}</a>', url, count)
    production_capacities.short_description='wprowadzone progi produkcji'
 

class PurchaseOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'number', 'buyer', 'demands')
    def demands(self, obj):
        count = obj.demands.count()
        url = (
            reverse("admin:scm_app_demand_changelist")
            + "?"
            + urlencode({"purchase_offer__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{}</a>', url, count)
    demands.short_description='zapotrzebowania'

admin.site.register(PurchaseOffer, PurchaseOfferAdmin)


class DemandAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'demand', 'purchase_offer')

admin.site.register(Demand, DemandAdmin)


class ProductionCapacityAdmin(admin.ModelAdmin):
    list_display = ('sales_offer', 'production_level', 'production_cost')

admin.site.register(ProductionCapacity, ProductionCapacityAdmin)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('id', 'solution', 'number', 'sales_link', 'purchases_link')
    def sales_link(self, obj):
        count = obj.sales.count()
        url = (
            reverse("admin:scm_app_sale_changelist")
            + "?"
            + urlencode({"period__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} plan(ów) sprzedaży</a>', url, count)
    def purchases_link(self, obj):
        count = obj.purchases.count()
        url = (
            reverse("admin:scm_app_buying_changelist")
            + "?"
            + urlencode({"period__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} plan(ów) kupna</a>', url, count)
    sales_link.short_description = "plany sprzedaży"
    purchases_link.short_description = "plany kupna"


class BuyingAdmin(admin.ModelAdmin):
    list_display = ('period', 'buyer', 'purchase_amount', 'price')
admin.site.register(Buying, BuyingAdmin)


class SaleAdmin(admin.ModelAdmin):
    list_display = ('period', 'producer', 'production_amount', 'price')
admin.site.register(Sale, SaleAdmin)

@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'periods_link')
    def periods_link(self, obj):
        count = obj.solution_periods.count()
        url = (
            reverse("admin:scm_app_period_changelist")
            + "?"
            + urlencode({"solution__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} okres(ów)</a>', url, count)
    periods_link.short_description = "okresy w harmonogramie"
  