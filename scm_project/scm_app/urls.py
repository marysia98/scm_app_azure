from django.urls import path

from .views import (HomePage, PlanListView, PlanDetailView,  SalesOfferDetailView, AddSalesOfferView, UpdateSalesOfferView,
    PurchaseOfferDetailView, AddPurchaseOfferView, UpdatePurchaseOfferView, DeletePurchaseOfferView, DeleteSalesOfferView, CustomLoginView, SchedulesView, ScheduleDetailView)


urlpatterns = [
    path('profile/', HomePage.as_view(), name='profile'),
    path('plans/', PlanListView.as_view(), name='plans'),
    path('plans/<int:pk>/', PlanDetailView.as_view(), name='plan_details'),
    path('login/', CustomLoginView.as_view(), name='login'),

    path('salesoffer/<int:pk>/', SalesOfferDetailView.as_view(), name='sales_offer_details'),
    path('salesoffer/add/<plan>/', AddSalesOfferView.as_view(), name='create_sales_offer'),
    path('salesoffer/update/<int:pk>/', UpdateSalesOfferView.as_view(), name='update_sales_offer'),
    path('salesoffer/delete/<int:pk>/', DeleteSalesOfferView.as_view(), name='delete_sales_offer'),

    path('purchaseoffer/<int:pk>/', PurchaseOfferDetailView.as_view(), name='purchase_offer_details'),
    path('purchaseoffer/add/<plan>/', AddPurchaseOfferView.as_view(), name='create_purchase_offer'),
    path('purchaseoffer/update/<int:pk>/', UpdatePurchaseOfferView.as_view(), name='update_purchase_offer'),
    path('purchaseoffer/delete/<int:pk>/', DeletePurchaseOfferView.as_view(), name='delete_purchase_offer'),

    path('schedules/<int:pk>/', ScheduleDetailView.as_view(), name='schedule_details'),
    path('schedules/', SchedulesView.as_view(), name='schedules'),
]