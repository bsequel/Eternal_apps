# admin.py - Django Admin configuration for CustomUser
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'is_active', 'date_joined', 'get_dashboard_access')
    list_filter = ('role', 'is_active', 'cyber_cell_access', 'bank_balance_access', 
                   'payment_gateway_access', 'cams_carvy_access', 'consolidated_access')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    # Add dashboard permissions to the admin form
    fieldsets = UserAdmin.fieldsets + (
        ('Dashboard Permissions', {
            'fields': (
                'cyber_cell_access',
                'bank_balance_access', 
                'payment_gateway_access',
                'cams_carvy_access',
                'consolidated_access'
            ),
            'classes': ('collapse',)
        }),
        ('Role', {
            'fields': ('role',),
        }),
    )
    
    def get_dashboard_access(self, obj):
        """Display dashboard access summary"""
        dashboards = []
        if obj.cyber_cell_access:
            dashboards.append('Cyber Cell')
        if obj.bank_balance_access:
            dashboards.append('Bank Balance')
        if obj.payment_gateway_access:
            dashboards.append('Payment Gateway')
        if obj.cams_carvy_access:
            dashboards.append('Cams Carvy')
        if obj.consolidated_access:
            dashboards.append('Consolidated')
        
        return ', '.join(dashboards) if dashboards else 'No access'
    
    get_dashboard_access.short_description = 'Dashboard Access'
    
    # Custom actions
    def grant_all_dashboard_access(self, request, queryset):
        """Grant all dashboard access to selected users"""
        updated = queryset.update(
            cyber_cell_access=True,
            bank_balance_access=True,
            payment_gateway_access=True,
            cams_carvy_access=True,
            consolidated_access=True
        )
        self.message_user(request, f'{updated} users granted all dashboard access.')
    
    grant_all_dashboard_access.short_description = "Grant all dashboard access"
    
    def revoke_all_dashboard_access(self, request, queryset):
        """Revoke all dashboard access from selected users"""
        updated = queryset.update(
            cyber_cell_access=False,
            bank_balance_access=False,
            payment_gateway_access=False,
            cams_carvy_access=False,
            consolidated_access=False
        )
        self.message_user(request, f'{updated} users revoked from all dashboards.')
    
    revoke_all_dashboard_access.short_description = "Revoke all dashboard access"
    
    actions = ['grant_all_dashboard_access', 'revoke_all_dashboard_access']