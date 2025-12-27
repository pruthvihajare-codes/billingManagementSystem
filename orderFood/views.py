from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from billing.models import *
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from django.db.models import Max
from django.db import connection
from django.utils.timezone import localtime
from billingManagementSystem.encryption import encrypt_parameter, decrypt_parameter
from django.utils.timezone import make_aware
from datetime import datetime, time
from django.db.models import F
import json
from django.db import transaction
from django.utils import timezone
 

@login_required
def orderDetailIndex(request):
    full_name = getattr(request.user, 'full_name', 'User')
    try:
        # Get all active tables by category
        non_ac_tables = TableMaster.objects.filter(category='Non-AC', is_active=1)
        ac_tables = TableMaster.objects.filter(category='AC', is_active=1)
        bar_tables = TableMaster.objects.filter(category='Bar', is_active=1)

        # Get tables that have active orders (status 1 or 2)
        from django.db.models import Q
        
        # Get active orders with status
        active_orders = Order.objects.filter(
            Q(status_id=1) | Q(status_id=2)
        ).select_related('status').values('table_no', 'table_category', 'status__status_name')
        
        # Create lookup dictionary
        order_lookup = {}
        for order in active_orders:
            key = f"{order['table_no']}|{order['table_category']}"
            order_lookup[key] = order['status__status_name']
        
        # Add has_order and status to each table object
        def add_table_status(tables):
            for table in tables:
                key = f"{table.table_number}|{table.category}"
                table.has_order = key in order_lookup
                table.order_status = order_lookup.get(key, '')
            return tables
        
        non_ac_tables = add_table_status(non_ac_tables)
        ac_tables = add_table_status(ac_tables)
        bar_tables = add_table_status(bar_tables)

        return render(request, 'Shared/index.html', {
            'non_ac_tables': non_ac_tables,
            'ac_tables': ac_tables,
            'bar_tables': bar_tables,
            'full_name': full_name,
        })

    except Exception as e:
        print(f"Error rendering Shared/index.html: {e}")
        return render(request, 'Shared/404.html', {'full_name': full_name}, status=404)

# @login_required
# def orderCreate(request):
#     full_name = getattr(request.user, 'full_name', 'User')

#     try:
#         if request.method == "GET":

#             tableName = decrypt_parameter(str(request.GET.get("tableNo")))
#             Category = decrypt_parameter(str(request.GET.get("category")))

#             menu_items = MenuDetails.objects.filter(seating_category=Category).values_list('menu_name', flat=True)

#             # Get tax rates (ADD THIS LINE)
#             tax_rates = get_tax_rates()

#             return render(request, 'OrderFood/orderFoodCreate.html', {
#                 "tableName":tableName,
#                 "Category":Category,
#                 "menu_items":menu_items,
#                 "tax_rates":tax_rates,
#             })


#         elif request.method == "POST":
#             final_order_flag = request.POST.get("finalOrder", '')
#             category = request.POST.get("Category", '')
#             service = request.POST.get("service", '')
#             dish = request.POST.get("dish", '')
#             selectedQty = request.POST.get("quantity", '')

#             if final_order_flag == 'finalOrder':
#                 menu_item = None

#                 if selectedQty == 'H':
#                     menu_item = MenuDetails.objects.filter(
#                         seating_category=category,
#                         menu_name=dish,
#                         menu_quantity_half__isnull=False
#                     ).first()
#                 elif selectedQty == 'F':
#                     menu_item = MenuDetails.objects.filter(
#                         seating_category=category,
#                         menu_name=dish,
#                         menu_quantity_full__isnull=False
#                     ).first()

#                 if menu_item:
#                     menu_item_data = model_to_dict(menu_item)
#                 else:
#                     menu_item_data = {}

#                 return JsonResponse({
#                     'message': 'Final order received successfully!',
#                     'menu_item': menu_item_data
#                 })

#             else:
#                 menu_names = MenuDetails.objects.filter(menu_category=category).values_list('menu_name', flat=True)
#                 options = [{'id': idx, 'name': name} for idx, name in enumerate(menu_names)]
#                 return JsonResponse({'options': options})

#     except Exception as e:
#         print(f"Error rendering orderFoodCreate.html: {e}")
#         return render(request, 'Shared/404.html', {'full_name': full_name}, status=404)

@login_required
def orderCreate(request):
    full_name = getattr(request.user, 'full_name', 'User')

    try:
        if request.method == "GET":
            tableName = decrypt_parameter(str(request.GET.get("tableNo")))
            Category = decrypt_parameter(str(request.GET.get("category")))

            menu_items = MenuDetails.objects.filter(seating_category=Category).values_list('menu_name', flat=True)
            tax_rates = get_tax_rates()

            return render(request, 'OrderFood/orderFoodCreate.html', {
                "tableName": tableName,
                "Category": Category,
                "menu_items": menu_items,
                "tax_rates": tax_rates,
            })

        elif request.method == "POST":
            final_order_flag = request.POST.get("finalOrder", '')
            category = request.POST.get("Category", '')
            service = request.POST.get("service", '')
            dish = request.POST.get("dish", '')
            selectedQty = request.POST.get("quantity", '')
            
            if final_order_flag == 'finalOrder':
                # Get the menu item
                menu_item = MenuDetails.objects.filter(
                    seating_category=category,
                    menu_name=dish,
                    menu_isActive=True
                ).first()
                
                if not menu_item:
                    return JsonResponse({
                        'error': 'Item not found',
                        'menu_item': {}
                    })
                
                qty_display = ""
                unit_price = 0
                total_price = 0
                
                # Handle different measurement types
                if menu_item.menu_measurement == 'half_full':
                    # For half/full items
                    if selectedQty == 'H':
                        price = menu_item.menu_half_price
                        qty_display = "Half"
                        unit_price = float(price) if price else 0
                        total_price = unit_price
                    elif selectedQty == 'F':
                        price = menu_item.menu_full_price
                        qty_display = "Full"
                        unit_price = float(price) if price else 0
                        total_price = unit_price
                    else:
                        return JsonResponse({
                            'error': 'Invalid portion for this item',
                            'menu_item': {}
                        })
                else:
                    # For non-half/full items (piece, bottle, ml, etc.)
                    qty = int(request.POST.get("qty", 1))
                    
                    if menu_item.menu_measurement == 'piece':
                        # For piece-based items like pizza
                        unit_price = float(menu_item.menu_full_price) if menu_item.menu_full_price else 0
                        qty_display = f"{qty} {menu_item.measurement_unit or menu_item.menu_measurement}"
                        total_price = unit_price * qty  # Total price for all pieces
                        selectedQty = 'F'
                    elif menu_item.menu_measurement == 'ml':
                        # For ml items (like Pepsi 500ml bottle)
                        # quantity = number of bottles
                        quantity = int(request.POST.get("qty", 1))
                        
                        # For fixed bottle items, price is per bottle
                        unit_price = float(menu_item.menu_full_price)  # Price per bottle
                        
                        # Get ml_qty for display
                        ml_qty = request.POST.get("ml_qty", '500')
                        try:
                            ml_qty = int(ml_qty)
                            qty_display = f"{ml_qty}ml"
                        except:
                            qty_display = menu_item.measurement_unit or "500ml"
                        
                        total_price = unit_price * quantity
                    
                    else:
                        # For other measurement types (bottle, glass, slice, plate)
                        unit_price = float(menu_item.menu_full_price) if menu_item.menu_full_price else 0
                        qty_display = f"{qty} {menu_item.measurement_unit or menu_item.menu_measurement}"
                        total_price = unit_price * qty
                        selectedQty = 'F'
                
                # Prepare response data
                menu_item_data = {
                    'menu_name': menu_item.menu_name,
                    'menu_category': menu_item.menu_category,
                    'menu_type': menu_item.menu_type,
                    'menu_measurement': menu_item.menu_measurement,
                    'measurement_unit': menu_item.measurement_unit,
                    'qty_display': qty_display,
                    'unit_price': str(unit_price),  # Price per unit
                    'total_price': str(total_price),  # Total price for the quantity
                    'selected_qty': selectedQty,
                    'quantity': request.POST.get("qty", "1"),
                    'ml_qty': request.POST.get("ml_qty", "")
                }
                
                return JsonResponse({
                    'message': 'Item added successfully',
                    'menu_item': menu_item_data
                })

            else:
                menu_names = MenuDetails.objects.filter(menu_category=category).values_list('menu_name', flat=True)
                options = [{'id': idx, 'name': name} for idx, name in enumerate(menu_names)]
                return JsonResponse({'options': options})
           
    except Exception as e:
        print(f"Error in orderCreate: {e}")
        return JsonResponse({'error': str(e)})

@login_required
def get_dish_details(request):
    """Get details of a specific dish for frontend UI"""
    try:
        dish_name = request.GET.get('dish_name')
        category = request.GET.get('category')
        
        if not dish_name or not category:
            return JsonResponse({'success': False, 'error': 'Missing parameters'})
        
        dish = MenuDetails.objects.filter(
            menu_name=dish_name,
            seating_category=category,
            menu_isActive=True
        ).first()
        
        if dish:
            # Get price based on measurement type
            price = None
            if dish.menu_measurement == 'half_full':
                price = {
                    'half': str(dish.menu_half_price) if dish.menu_half_price else "0",
                    'full': str(dish.menu_full_price) if dish.menu_full_price else "0"
                }
            else:
                price = str(dish.menu_full_price) if dish.menu_full_price else "0"
            
            return JsonResponse({
                'success': True,
                'item': {
                    'menu_name': dish.menu_name,
                    'menu_category': dish.menu_category,
                    'menu_type': dish.menu_type,
                    'menu_measurement': dish.menu_measurement,
                    'measurement_unit': dish.measurement_unit,
                    'menu_half_price': str(dish.menu_half_price) if dish.menu_half_price else None,
                    'menu_full_price': str(dish.menu_full_price) if dish.menu_full_price else None,
                    'price': price
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Dish not found'})
    except Exception as e:
        print(f"Error in get_dish_details: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def get_tax_rates():
    try:
        """Get tax rates ONLY from database"""
        rates = {}
        
        # Get food GST
        food_param = TblParameterMaster.objects.filter(
            parameter_name='GST_RATE', 
            is_active=1
        ).first()
        if food_param:
            rates['food_gst'] = float(food_param.parameter_value)
        
        # Get drink GST
        drink_param = TblParameterMaster.objects.filter(
            parameter_name='DRINK_GST_RATE', 
            is_active=1
        ).first()
        if drink_param:
            rates['drink_gst'] = float(drink_param.parameter_value)
            
        # Get service charge rate
        service_param = TblParameterMaster.objects.filter(
            parameter_name='SERVICE_CHARGE_RATE', 
            is_active=1
        ).first()
        if service_param:
            rates['service_charge'] = float(service_param.parameter_value)
            
        # Check if service charge is enabled
        enabled_param = TblParameterMaster.objects.filter(
            parameter_name='SERVICE_CHARGE_ENABLED', 
            is_active=1
        ).first()
        if enabled_param:
            rates['service_enabled'] = enabled_param.parameter_value == '1'
        
        return rates
    except Exception as e:
        print(f"Error getting tax rates: {e}")
        return {}

@csrf_exempt
@login_required
def orderStoreDetails(request):
    if request.method == 'POST':
        try:
            data = request.POST
            table_no = data.get('table_no')
            TableCategory = data.get('TableCategory')
            order_items = json.loads(data.get('order_items'))

            user = request.user

            # Calculate daily_order_no that resets every day
            today = timezone.now().date()
            start_of_day = make_aware(datetime.combine(today, time.min))  # 00:00:00 today
            end_of_day = make_aware(datetime.combine(today, time.max))    # 23:59:59.999999 today

            last_order_today = Order.objects.filter(created_at__range=(start_of_day, end_of_day)).order_by('-daily_order_no').first()
            if last_order_today and last_order_today.daily_order_no:
                daily_order_no = last_order_today.daily_order_no + 1
            else:
                daily_order_no = 1

            # Get totals and GST info
            total_amount = float(data.get('total_amount', 0))
            gst_applied = int(data.get('gst_applied', 0))
            gst_amount = float(data.get('gst_amount', 0))
            grand_total = float(data.get('grand_total', 0))

            # Create the order
            order = Order.objects.create(
                table_no=table_no,
                created_by=user,
                created_at=timezone.now(),
                status_id=1,
                total_amount=total_amount,
                gst_applied=gst_applied,
                gst_amount=gst_amount,
                grand_total=grand_total,
                daily_order_no=daily_order_no,
                table_category=TableCategory
            )

            # Create related order details
            for item in order_items:
                OrderDetail.objects.create(
                    order=order,
                    menu_name=item['menu_name'],
                    menu_category=item['menu_category'],
                    quantity_type=item['quantity_type'],
                    quantity=item['quantity'],
                    price=item['price'],
                    created_by=user,
                    created_at=timezone.now(),
                    status_id=1
                )

            return JsonResponse({'status': 'success', 'order_id': order.pk, 'daily_order_no': daily_order_no})

        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=405)

@login_required
def orderDetailsView(request):
    full_name = getattr(request.user, 'full_name', 'User')

    try:
        order_id = decrypt_parameter(request.GET['order_id'])

        table_no = Order.objects.get(order_id=order_id).table_no

        order_details = OrderDetail.objects.filter(order__order_id=order_id).values(
            'menu_category', 'menu_name', 'quantity_type', 'price'
        )

        return render(request, 'OrderFood/orderDetailsView.html', {
            'order_details': order_details,
            'full_name': full_name,
            'order_id': order_id,
            'table_no': table_no
        })

    except Exception as e:
        print(f"Error rendering orderDetailsView: {e}")
        return render(request, 'Shared/404.html', {
            'full_name': full_name
        }, status=404)

@login_required
def editOrderCreate(request):
    full_name = getattr(request.user, 'full_name', 'User')

    try:
        tableName = decrypt_parameter(request.GET.get("tableNo"))
        Category = decrypt_parameter(request.GET.get("category"))

        # Fetch order
        order = Order.objects.filter(
            table_no=tableName,
            table_category=Category
        ).first()

        if not order:
            return render(request, 'Shared/404.html', status=404)

        order_details = OrderDetail.objects.filter(order=order)

        menu_items = MenuDetails.objects.filter(
            seating_category=Category
        ).values_list('menu_name', flat=True)

        return render(request, 'OrderFood/editOrderCreate.html', {
            "tableName": tableName,
            "Category": Category,
            "menu_items": menu_items,
            "selected_order": order,
            "order_details": order_details
        })

    except Exception as e:
        print("Edit Order Error:", e)
        return render(request, 'Shared/404.html', status=404)

@login_required
@transaction.atomic
def orderUpdateDetails(request):
    if request.method == "POST":
        try:
            order_id = decrypt_parameter(request.POST.get('order_id'))
            order_items = json.loads(request.POST.get('order_items'))

            order = Order.objects.get(order_id=order_id)

            # Delete existing items
            OrderDetail.objects.filter(order=order).delete()

            # Insert updated items
            for item in order_items:
                OrderDetail.objects.create(
                    order=order,
                    menu_name=item['menu_name'],
                    menu_category=item['menu_category'],
                    quantity_type=item['quantity_type'],
                    quantity=int(item['quantity']),
                    price=float(item['price']),
                    created_by=request.user
                )

            # Update order totals
            order.total_amount = request.POST.get('total_amount')
            order.gst_applied = request.POST.get('gst_applied')
            order.gst_amount = request.POST.get('gst_amount')
            order.grand_total = request.POST.get('grand_total')
            order.updated_by = request.user
            order.updated_at = timezone.now()
            order.save()

            return JsonResponse({"status": "success"})

        except Exception as e:
            print("Update Order Error:", e)
            return JsonResponse({"status": "error"}, status=500)

@login_required
def get_menu_price(request):
    menu_name = request.GET.get('menu_name')
    quantity_type = request.GET.get('quantity_type')
    seating_category = request.GET.get('seating_category')

    try:
        menu = MenuDetails.objects.get(
            menu_name=menu_name,
            seating_category=seating_category,
            menu_isActive=1
        )

        price = (
            menu.menu_half_price
            if quantity_type == 'H'
            else menu.menu_full_price
        )

        return JsonResponse({
            'price': float(price),
            'menu_category': menu.menu_category,
            'menu_type': menu.menu_type
        })

    except MenuDetails.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json

@csrf_exempt
def delete_order_item(request):
    if request.method == "POST":
        enc_id = request.POST.get('order_detail_id')
        order_detail_id = decrypt_parameter(enc_id)

        try:
            item = OrderDetail.objects.get(id=order_detail_id)
            order = item.order

            # Delete item
            item.delete()

            # Recalculate totals
            items = OrderDetail.objects.filter(order=order)

            total = sum(i.price * i.quantity for i in items)
            gst = total * Decimal('0.18') if order.gst_applied else Decimal('0.00')

            order.total_amount = total
            order.gst_amount = gst
            order.grand_total = total + gst
            order.save()

            return JsonResponse({'status': 'success'})

        except OrderDetail.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})

    return JsonResponse({'status': 'invalid'})
