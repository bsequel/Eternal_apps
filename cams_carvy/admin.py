# admin.py
from django.contrib import admin
from .models import CamsPortfolio

@admin.register(CamsPortfolio)
class CamsPortfolioAdmin(admin.ModelAdmin):
    list_display = [
        'folio_no', 'entity_name', 'isin', 'scheme_name', 
        'cost_value', 'unit_balance', 'market_value', 
        'profit_loss', 'nav_date', 'updated_at', 'updated_by'
    ]
    list_filter = [
        'entity_name', 'month', 'year', 'nav_date', 'updated_at'
    ]
    search_fields = [
        'folio_no', 'entity_name', 'isin', 'scheme_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'profit_loss', 'profit_loss_percentage']
    ordering = ['-updated_at']
    
    def profit_loss(self, obj):
        return f"₹{obj.profit_loss:,.2f}"
    profit_loss.short_description = 'Profit/Loss'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.updated_by = request.user
        else:  # If updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)



# # admin.py
# from django.contrib import admin
# from django.utils.html import format_html
# from django.db.models import Sum
# from .models import CamsPortfolio

# @admin.register(CamsPortfolio)
# class CamsPortfolioAdmin(admin.ModelAdmin):
#     list_display = [
#         'folio_no', 'entity_name', 'scheme_name', 'cost_value_formatted', 
#         'market_value_formatted', 'profit_loss_formatted', 'nav_date', 
#         'updated_by', 'updated_at'
#     ]
#     list_filter = [
#         'nav_date', 'month', 'year', 'updated_by', 'entity_name'
#     ]
#     search_fields = [
#         'folio_no', 'entity_name', 'isin', 'scheme_name'
#     ]
#     readonly_fields = [
#         'profit_loss', 'profit_loss_percentage', 'created_at', 'updated_at'
#     ]
#     fieldsets = (
#         ('Portfolio Information', {
#             'fields': (
#                 'folio_no', 'entity_name', 'isin', 'scheme_name'
#             )
#         }),
#         ('Financial Details', {
#             'fields': (
#                 'cost_value', 'unit_balance', 'market_value', 'nav_date'
#             )
#         }),
#         ('Period Information', {
#             'fields': (
#                 'month', 'year'
#             )
#         }),
#         ('Calculated Fields', {
#             'fields': (
#                 'profit_loss', 'profit_loss_percentage'
#             ),
#             'classes': ('collapse',)
#         }),
#         ('Audit Information', {
#             'fields': (
#                 'updated_by', 'created_at', 'updated_at'
#             ),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def cost_value_formatted(self, obj):
#         return f"₹{obj.cost_value:,.2f}"
#     cost_value_formatted.short_description = "Cost Value"
#     cost_value_formatted.admin_order_field = 'cost_value'
    
#     def market_value_formatted(self, obj):
#         color = "green" if obj.is_profit else "red"
#         return format_html(
#             '<span style="color: {}; font-weight: bold;">₹{:,.2f}</span>',
#             color, obj.market_value
#         )
#     market_value_formatted.short_description = "Market Value"
#     market_value_formatted.admin_order_field = 'market_value'
    
#     def profit_loss_formatted(self, obj):
#         profit_loss = obj.profit_loss
#         color = "green" if profit_loss > 0 else "red" if profit_loss < 0 else "black"
#         symbol = "+" if profit_loss > 0 else ""
#         return format_html(
#             '<span style="color: {}; font-weight: bold;">{}{:,.2f}</span>',
#             color, symbol, profit_loss
#         )
#     profit_loss_formatted.short_description = "P&L"
    
#     def changelist_view(self, request, extra_context=None):
#         # Add summary statistics to the changelist view
#         response = super().changelist_view(request, extra_context=extra_context)
        
#         try:
#             qs = response.context_data['cl'].queryset
#             summary = qs.aggregate(
#                 total_cost=Sum('cost_value'),
#                 total_market=Sum('market_value'),
#             )
            
#             extra_context = extra_context or {}
#             extra_context['summary'] = {
#                 'total_cost': summary['total_cost'] or 0,
#                 'total_market': summary['total_market'] or 0,
#                 'total_profit_loss': (summary['total_market'] or 0) - (summary['total_cost'] or 0),
#                 'total_records': qs.count(),
#             }
#             response.context_data.update(extra_context)
#         except (AttributeError, KeyError):
#             pass
            
#         return response
    
#     def save_model(self, request, obj, form, change):
#         if not change:  # Creating new record
#             obj.updated_by = request.user
#         else:  # Updating existing record
#             obj.updated_by = request.user
#         super().save_model(request, obj, form, change)

# # Custom admin site configuration
# admin.site.site_header = "CAMS Portfolio Admin"
# admin.site.site_title = "CAMS Admin"
# admin.site.index_title = "Welcome to CAMS Portfolio Administration"