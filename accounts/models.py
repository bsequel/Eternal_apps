# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('viewer', 'Viewer'),
    )
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default='viewer'
    )

    # Make email unique and require email for login standardization
    email = models.EmailField(unique=True)

    # Set email as USERNAME_FIELD for authentication by email, not username
    USERNAME_FIELD = 'email'
    # username still required by AbstractUser, but no login by username
    REQUIRED_FIELDS = ['username']

    # Dashboard permissions
    cyber_cell_access = models.BooleanField(
        default=False, verbose_name="Cyber Cell Dashboard")
    bank_balance_access = models.BooleanField(
        default=False, verbose_name="Bank Balance Dashboard")
    payment_gateway_access = models.BooleanField(
        default=False, verbose_name="Payment Gateway Dashboard")
    cams_carvy_access = models.BooleanField(
        default=False, verbose_name="Cams Carvy Dashboard")
    consolidated_access = models.BooleanField(
        default=False, verbose_name="Consolidated Dashboard")

    def __str__(self):
        # Prefer email string representation; fallback to username
        return self.email if self.email else self.username

    def get_accessible_dashboards(self):
        """Return list of dashboards user has access to"""
        dashboards = []
        if self.cyber_cell_access:
            dashboards.append('cyber_cell')
        if self.bank_balance_access:
            dashboards.append('bank_balance')
        if self.payment_gateway_access:
            dashboards.append('payment_gateway')
        if self.cams_carvy_access:
            dashboards.append('cams_carvy')
        if self.consolidated_access:
            dashboards.append('consolidated')
        return dashboards
