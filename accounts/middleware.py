# middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class DashboardAccessMiddleware:
    """Middleware to check dashboard access permissions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define dashboard URL patterns and their required permissions
        self.dashboard_permissions = {
            '/dashboard/cyber-cell/': 'cyber_cell_access',
            '/dashboard/bank-balance/': 'bank_balance_access', 
            '/dashboard/payment-gateway/': 'payment_gateway_access',
            '/dashboard/cams-carvy/': 'cams_carvy_access',
            '/dashboard/consolidated/': 'consolidated_access',
        }

    def __call__(self, request):
        # Check if user is accessing a protected dashboard
        if request.user.is_authenticated:
            for url_pattern, permission in self.dashboard_permissions.items():
                if request.path.startswith(url_pattern):
                    # Check if user has the required permission
                    if not getattr(request.user, permission, False):
                        messages.error(request, 'You do not have permission to access this dashboard.')
                        return redirect('dashboard_home')  # Redirect to main dashboard
        
        response = self.get_response(request)
        return response


