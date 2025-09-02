# context_processors.py
def dashboard_permissions(request):
    """Context processor to make dashboard permissions available in templates"""
    if request.user.is_authenticated:
        return {
            'user_dashboards': {
                'cyber_cell': request.user.cyber_cell_access,
                'bank_balance': request.user.bank_balance_access,
                'payment_gateway': request.user.payment_gateway_access,
                'cams_carvy': request.user.cams_carvy_access,
                'consolidated': request.user.consolidated_access,
            }
        }
    return {}


# Template tag for checking dashboard access
# templatetags/dashboard_tags.py
from django import template

register = template.Library()

@register.simple_tag
def user_can_access_dashboard(user, dashboard_name):
    """Check if user can access a specific dashboard"""
    dashboard_permissions = {
        'cyber_cell': 'cyber_cell_access',
        'bank_balance': 'bank_balance_access',
        'payment_gateway': 'payment_gateway_access',
        'cams_carvy': 'cams_carvy_access',
        'consolidated': 'consolidated_access',
    }
    
    if dashboard_name in dashboard_permissions:
        return getattr(user, dashboard_permissions[dashboard_name], False)
    return False

@register.inclusion_tag('dashboard/sidebar.html', takes_context=True)
def dashboard_sidebar(context):
    """Render dashboard sidebar with user permissions"""
    user = context['request'].user
    if user.is_authenticated:
        accessible_dashboards = []
        
        dashboards = [
            {'name': 'cyber_cell', 'title': 'Cyber Cell', 'icon': 'fas fa-shield-alt', 'url': '/dashboard/cyber-cell/'},
            {'name': 'bank_balance', 'title': 'Bank Balance', 'icon': 'fas fa-university', 'url': '/dashboard/bank-balance/'},
            {'name': 'payment_gateway', 'title': 'Payment Gateway', 'icon': 'fas fa-credit-card', 'url': '/dashboard/payment-gateway/'},
            {'name': 'cams_carvy', 'title': 'Cams Carvy', 'icon': 'fas fa-camera', 'url': '/dashboard/cams-carvy/'},
            {'name': 'consolidated', 'title': 'Consolidated', 'icon': 'fas fa-chart-bar', 'url': '/dashboard/consolidated/'},
        ]
        
        for dashboard in dashboards:
            permission_attr = f"{dashboard['name']}_access"
            if getattr(user, permission_attr, False):
                accessible_dashboards.append(dashboard)
        
        return {'accessible_dashboards': accessible_dashboards}
    
    return {'accessible_dashboards': []}