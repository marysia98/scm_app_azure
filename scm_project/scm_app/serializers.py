from rest_framework_json_api import serializers
from .models import Plan, SalesOffer, PurchaseOffer, ProductionCapacity, Demand, Sale, Buying, Period, Solution


class ProductionCapacitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionCapacity
        fields = ('production_level', 'production_cost')

class SalesOfferSerializer(serializers.ModelSerializer):
    production_capacities = ProductionCapacitiesSerializer(many=True)
    class Meta:
        model = SalesOffer
        exclude = ['number']
    def create(self, validated_data):
        capacity_validated_data = validated_data.pop('production_capacities')
        sales_offer = SalesOffer.objects.create(**validated_data)
        capacities_serializer = self.fields['production_capacities']
        for each in capacity_validated_data:
            each['sales_offer'] = sales_offer
        capacities = capacities_serializer.create(capacity_validated_data)
        return sales_offer

class DemandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demand
        fields = ('start_date', 'demand')

class PurchaseOfferSerializer(serializers.ModelSerializer):
    demands = DemandsSerializer(many=True, read_only=True)
    class Meta:
        model = PurchaseOffer
        fields = ('buyer', 'retail_unit_price', 'stock_level', 'stock_cost', 'max_stock_capacity', 'demands')

class PlanSerializer(serializers.ModelSerializer):
    sales_offers = SalesOfferSerializer(many=True, read_only=True)
    purchase_offers = PurchaseOfferSerializer(many=True, read_only=True)
    class Meta:
        model = Plan
        fields = ('price_type', 'periods_amount', 'sales_offers', 'purchase_offers')



class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ('producer', 'production_amount', 'price')

class BuyingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buying
        fields = ('buyer', 'purchase_amount', 'price')

class PeriodSerializer(serializers.ModelSerializer):
    sales = SaleSerializer(many=True)
    purchases = BuyingSerializer(many=True)
    class Meta:
        model = Period
        fields = ('number', 'sales', 'purchases')
    def create(self, validated_data):
        purchases_data = validated_data.pop('purchases')
        sales_data = validated_data.pop('sales')
        period = Period.objects.create(**validated_data)
        purchase_offer_serializer = self.fields['purchases']
        sale_offer_serializer = self.fields['sales']
        for each in purchases_data:
            each['period'] = period
        for each in sales_data:
            each['period'] = period
        purchases = purchase_offer_serializer.create(purchases_data)
        sales = sale_offer_serializer.create(sales_data)
        return period

class SolutionSerializer(serializers.ModelSerializer):
    solution_periods = PeriodSerializer(many=True)
    class Meta:
        model = Solution
        fields = ('plan', 'solution_periods')
    def create(self, validated_data):
        periods_data = validated_data.pop('solution_periods')
        solution = Solution.objects.create(**validated_data)
        period_serializer = self.fields['solution_periods']
        for each in periods_data:
            each['solution'] = solution
        period = period_serializer.create(periods_data)
        return solution