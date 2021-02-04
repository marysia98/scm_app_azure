from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib import admin
from django.urls import reverse
from django.core.exceptions import ValidationError
import datetime

class User(AbstractUser):
    USER_TYPE = (
        (1, 'admin'),
        (2, 'producent'),
        (3, 'nabywca'),
    )
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE, verbose_name="typ użytkownika")
    REQUIRED_FIELDS = ['user_type']
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)



class Plan(models.Model):
    PLAN_STATUS = (
        (0, 'nieaktywny'),
        (1, 'aktywny')
    )
    # to get 'human-readable' names use function: get_<name_of_model>_display()
    PLAN_TYPES = (
        (0, 'poufna'),
        (1, 'publiczna'),
    )

    PRICE_TYPES = (
        (0, 'jednakowa'),
        (1, 'zróżnicowana'),
    )

    name = models.CharField(max_length=100, verbose_name="tytuł aukcji")
    description = models.CharField(max_length=400, verbose_name="opis", default="")
    status = models.PositiveSmallIntegerField(choices=PLAN_STATUS, default=0)
    schedule_beginning = models.DateField(default=datetime.date.today()+datetime.timedelta(days=1), verbose_name="start harmonogramu")
    periods_amount = models.PositiveSmallIntegerField(verbose_name="liczba okresów")
    period_length = models.PositiveSmallIntegerField(verbose_name="długość okresu")
    plan_type = models.PositiveSmallIntegerField(choices=PLAN_TYPES, default=0, verbose_name="typ planu")
    price_type = models.PositiveSmallIntegerField(choices=PRICE_TYPES, default=0, verbose_name="typ ceny")
    administrator = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={"user_type": 1}, on_delete=models.PROTECT)
    start_date = models.DateField(default=datetime.date.today, verbose_name="początek zbierania ofert")
    end_date = models.DateField(default=datetime.date.today, verbose_name="zakończenie zbierania ofert")
   
    def calculate_plan_status(self):
        now = datetime.date.today()
        if self.pk:
            if self.status == 1:
                if now < self.start_date:
                    return 'jeszcze nie rozpoczęto składania ofert'
                if self.start_date <= now and now <= self.end_date:
                    return 'rozpoczęto składanie ofert'
                if now > self.end_date:
                    return 'zakończono składanie ofert'
            else:
                return 'nieaktywny'
        return ''

    def is_public(self):
        if self.plan_type == 0:
            return False
        else:
            return True

    def is_scheduled(self):
        if self.solution:
            return True
        return False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plan_details', args=[str(self.id)])
    
    def save(self, *args, **kwargs):
        if self.pk:
            if (self.calculate_plan_status()=='zakończono składanie ofert' or self.calculate_plan_status()=='nieaktywny'):
                raise ValidationError("nie można wprowadzać zmian w nieaktywnych aukcjach")
        else:
            if self.start_date < datetime.date.today()+datetime.timedelta(days=1):
                raise ValidationError("Rozpoczecie aukcji nalezy oglaszac co najmniej 24h przed rozpoczęciem zbierania ofert")
            if self.start_date >= self.end_date:
                raise ValidationError("Aukcja musi trwac co najmniej 24h, wprowadz poprawną datę zakończenia")
            if self.schedule_beginning <= self.end_date:
                raise ValidationError("Planowany harmonogram musi dotyczyć okresu po zakończeniu zbierania ofert")
        super(Plan, self).save(*args, **kwargs)
    class Meta():
        verbose_name="Aukcja"
        verbose_name_plural="Aukcje"


class SalesOffer(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="sales_offers", verbose_name="plan")
    number = models.PositiveIntegerField(null=True, verbose_name="numer oferty")
    producer = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={"user_type": 2}, on_delete=models.PROTECT, related_name="sales_offers", verbose_name="producent")
    setup_cost = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="koszt początkowy")
    stock_level = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=0, default=0, verbose_name="stan magazynu")
    stock_cost = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2, default=0, verbose_name="koszt magazynowania")
    max_stock_capacity = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=0, default=0, verbose_name="maksymalna pojemność magazynu")

    def __str__(self):
        return str(self.id)

  # auto increment sales offer number within particular Plan
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if SalesOffer.objects.filter(plan=self.plan).count() != 0:
            recent = SalesOffer.objects.filter(plan=self.plan).order_by('-number')[0]
            print(recent)
            self.number = recent.number + 1
            super(SalesOffer, self).save(force_insert, force_update, using, update_fields)
        else:
            self.number = 1
            super(SalesOffer, self).save(force_insert, force_update, using, update_fields)

    def get_absolute_url(self):
        return reverse('sales_offer_details', kwargs={'pk': self.id})

    class Meta():
        db_table = 'SalesOffer'
        verbose_name="Oferta sprzedaży"
        verbose_name_plural="Oferty sprzedaży"  


class PurchaseOffer(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="purchase_offers", verbose_name="plan")
    number = models.PositiveIntegerField(verbose_name="numer oferty")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={"user_type": 3}, on_delete=models.PROTECT, related_name="purchase_offers", verbose_name="nabywca")
    retail_unit_price = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="cena kupna")
    stock_level = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=0, verbose_name="stan magazynu")
    stock_cost = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2, verbose_name="koszt magazynowania")
    max_stock_capacity = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=0, verbose_name="maksymalna pojemność magazynu")
   
    def __str__(self):
        return str(self.id)
    # auto increment purchase offer number within particular Plan

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if PurchaseOffer.objects.filter(plan=self.plan).count() != 0:
            recent = PurchaseOffer.objects.filter(plan=self.plan).order_by('-number')[0]
            self.number = recent.number + 1
            super(PurchaseOffer, self).save(force_insert, force_update, using, update_fields)
        else:
            self.number = 1
            super(PurchaseOffer, self).save(force_insert, force_update, using, update_fields)
    
    def get_absolute_url(self):
        return reverse('purchase_offer_details', kwargs={'pk': self.id})
    
    class Meta():
        verbose_name="Oferta kupna"
        verbose_name_plural="Oferty kupna"


class Demand(models.Model):
    number = models.PositiveSmallIntegerField(verbose_name="numer okresu", default=1, editable=False)
    demand = models.PositiveSmallIntegerField(verbose_name="zapotrzebowanie", default=0)
    purchase_offer = models.ForeignKey(PurchaseOffer, on_delete=models.CASCADE, related_name="demands", verbose_name="oferta kupna")
    
    class Meta():
        verbose_name="Zapotrzebowanie"
        verbose_name_plural="Zapotrzebowania"

    # wstawienie kolejnego numeru okresu
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if Demand.objects.filter(purchase_offer=self.purchase_offer.id).count() != 0:
            # dla oferty wprowadzone bylo juz zapotrzebowanie
            recent = Demand.objects.filter(purchase_offer=self.purchase_offer.id).order_by('-number')[0]
            self.number = recent.number + 1
            super(Demand, self).save(force_insert, force_update, using, update_fields)
        else:
            self.number = 1
            super(Demand, self).save(force_insert, force_update, using, update_fields)


class ProductionCapacity(models.Model):
    sales_offer = models.ForeignKey(SalesOffer, on_delete=models.CASCADE, related_name="production_capacities", default=3, verbose_name="oferta sprzedaży")
    production_level = models.PositiveSmallIntegerField(verbose_name="wielkość produkcji")
    production_cost = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="koszt produkcji")
    class Meta:
        verbose_name="Oferowana wielkość sprzedaży"
        verbose_name_plural = "Oferowane wielkości sprzedaży"
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)


class Solution(models.Model):
    plan = models.OneToOneField(Plan, on_delete=models.PROTECT, related_name="solution", verbose_name="aukcja")
    name = models.CharField(max_length=100, verbose_name="nazwa harmonogramu", default="harmonogram")
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
    def get_absolute_url(self):
        return reverse('schedule_details', kwargs={'pk': self.id})
    class Meta():
        verbose_name="Harmonogram"
        verbose_name_plural="Harmonogramy"


class Period(models.Model):
    number = models.PositiveSmallIntegerField(verbose_name="numer okresu")
    solution = models.ForeignKey(Solution, on_delete=models.PROTECT, related_name="solution_periods", verbose_name="harmonogram")
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
    class Meta():
        verbose_name="okres w harmonogramie"
        verbose_name_plural="Okresy w harmonogramie"


class Sale(models.Model):
    production_amount = models.PositiveSmallIntegerField(verbose_name="wielkość produkcji")
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="cena sprzedaży")
    period = models.ForeignKey(Period, on_delete=models.PROTECT, related_name="sales", verbose_name="okres")
    producer = models.ForeignKey(settings.AUTH_USER_MODEL,  limit_choices_to={"user_type": 2}, on_delete=models.PROTECT, related_name="sales", verbose_name="producent")
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
    class Meta():
        verbose_name="Sprzedaż"
        verbose_name_plural="Sprzedaż"


class Buying(models.Model):
    purchase_amount = models.PositiveSmallIntegerField(verbose_name="wielkość zamówienia")
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="cena kupna")
    period = models.ForeignKey(Period, on_delete=models.PROTECT, related_name="purchases", verbose_name="okres")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL,  limit_choices_to={"user_type": 3}, on_delete=models.PROTECT, related_name="purchases", verbose_name="nabywca")
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
    class Meta():
        verbose_name="Kupno"
        verbose_name_plural="Kupno"