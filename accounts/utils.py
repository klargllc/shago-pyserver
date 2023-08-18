from django.db.models import (
    Count,
    Sum,
    Avg,
    F,
    QuerySet,
    DecimalField
)
from datetime import datetime, timedelta
from places.models import (
    Order,
    FoodItem,
    OrderItem
)
import json
from places.api.serializers import FoodImageSerializer



def get_trending_products(queryset: QuerySet[Order] , end_date=14):
    stop_date = timezone.now() - timezone.timedelta(days=end_date)
    sales_data = queryset.filter(
                    created_on__gte=stop_date,
                    paid=True,
                    canceled=False,
                    closed=True
                ) \
                .prefetch_related('items', 'items__item') \
                .annotate(
                    total_quantity=Sum('items__quantity'),
                    total_sales=Sum(F('items__quantity') * F('items__item__price')),
                    average_price=Avg('items__item__price'),
                    total_revenue=Sum('items__item__price')
                ) \
                .order_by('-total_quantity')[:10]

    

    # Build product leaderboard
    leaderboard = []

    for sale in sales_data:
        food: FoodItem = sale.items.first().item
        leaderboard.append({
            'item': {
                'name': food.name,
                'image': FoodImageSerializer(food.image).data,
                'slug': food.slug
            }, # the fooditem name
            'units_sold': sale.total_quantity, # total quantity of item sold e.g 240 units
            'sales_revenue': sale.total_sales, # amount value of total quantity e.g $3,400
            'current_price': sale.items.first().item.price, # current selling price
            'average_price': sale.average_price, # average selling price
        })

    # Return leaderboard and average order value
    return leaderboard


def get_total_revenue(order_list: QuerySet[Order]):
    total_revenue = order_list.filter(
        canceled=False,
        closed=True,
        paid=True
    ) \
    .aggregate(total_revenue=Sum('subtotal'))['total_revenue']
    return total_revenue


def get_average_order_value(order_list: QuerySet[Order]):
    # Calculate average order value
    total_revenue = get_total_revenue()
    order_count = order_list.filter(
        paid=True,
        canceled=False,
        closed=True,
    ).count()
    average_order_value = (total_revenue / order_count) if (order_count > 0) else 0
    return average_order_value


def get_batch_product_sales_data(place_id):
    products = FoodItem.objects.filter(place_id=place_id).annotate(
        num_sales=Count('orderitem'), # number of sales in all orders
        total_sales=Sum(
            F('orderitem__quantity') * F('price'),
            output_field=DecimalField()
        ),
        avg_price=Avg('price'),
    ).order_by('-num_sales')
    return products


def get_single_product_sales_data(food):
    data = food.annotate(
        num_sales=Count('orderitem'), # number of sales in all orders
        total_sales=Sum(
            F('orderitem__quantity') * F('price'),
            output_field=DecimalField()
        ),
        avg_price=Avg('price'),
    )
    return {
        'total_sales': data['num_sales'],
        'total_revenue': data['total_sales'],
        'average_price': data['avg_price'],
    }


