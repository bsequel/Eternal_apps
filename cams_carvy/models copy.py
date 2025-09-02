# models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.conf import settings
class CamsPortfolio(models.Model):
    folio_no = models.CharField(max_length=20, verbose_name="Folio Number")
    entity_name = models.CharField(max_length=200, verbose_name="Entity Name")
    # isin = models.CharField(max_length=12, verbose_name="ISIN", help_text="International Securities Identification Number")
    isin = models.CharField(max_length=12, verbose_name="ISIN", help_text="International Securities Identification Number", null=True, blank=True)
    scheme_name = models.CharField(max_length=200, verbose_name="Scheme Name")
    cost_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Cost Value (INR)")
    unit_balance = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="Unit Balance")
    nav_date = models.DateField(verbose_name="NAV Date")
    market_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Market Value (INR)")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)
    # updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True)
    
    # Additional fields for filtering
    month = models.IntegerField(verbose_name="Month", help_text="1-12",null=True, blank=True)
    year = models.IntegerField(verbose_name="Year",null=True, blank=True)
    
    class Meta:
        db_table = 'cams_portfolio'
        verbose_name = 'CAMS Portfolio'
        verbose_name_plural = 'CAMS Portfolios'
        indexes = [
            models.Index(fields=['entity_name']),
            models.Index(fields=['isin']),
            models.Index(fields=['folio_no']),
            models.Index(fields=['nav_date']),
        ]
        
    def __str__(self):
        return f"{self.folio_no} - {self.entity_name}"
    
    @property
    def profit_loss(self):
        """Calculate profit/loss"""
        return self.market_value - self.cost_value
    
    @property
    def profit_loss_percentage(self):
        """Calculate profit/loss percentage"""
        if self.cost_value > 0:
            return ((self.market_value - self.cost_value) / self.cost_value) * 100
        return 0
    
    @property
    def is_profit(self):
        """Check if investment is in profit"""
        return self.market_value > self.cost_value
    
    @classmethod
    def get_summary_stats(cls, queryset=None):
        """Get summary statistics"""
        if queryset is None:
            queryset = cls.objects.all()
            
        from django.db.models import Sum, Count
        
        stats = queryset.aggregate(
            total_entities=Count('entity_name', distinct=True),
            total_folios=Count('folio_no', distinct=True),
            total_market_value=Sum('market_value'),
            total_cost_value=Sum('cost_value')
        )
        
        # Handle None values
        for key, value in stats.items():
            if value is None:
                stats[key] = 0
                
        return stats
    

# =======================     consolidated   ========================
# =======================     consolidated   ========================



class CAMSTransaction(models.Model):
    """Model for CAMS transaction data"""
    entity_name = models.CharField(max_length=255, help_text="Name of the entity/investor")
    amc_name = models.CharField(max_length=255, help_text="Asset Management Company name")
    folio_number = models.CharField(max_length=100, help_text="Folio number")
    isin = models.CharField(max_length=20, help_text="ISIN code")
    scheme_name = models.TextField(help_text="Mutual fund scheme name")
    transaction_date = models.DateField(null=True, blank=True, help_text="Date of transaction")
    transaction_description = models.CharField(max_length=255, null=True, blank=True, help_text="Transaction type/description")
    value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text="Transaction value")
    stamp_duty = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text="Stamp duty amount")
    units = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text="Number of units")
    nav = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text="Net Asset Value")
    unit_balance = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text="Unit balance after transaction")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    
    class Meta:
        db_table = 'cams_transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['folio_number']),
            models.Index(fields=['isin']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['entity_name']),
        ]
    
    def __str__(self):
        return f"{self.entity_name} - {self.folio_number} - {self.transaction_date}"

class CAMSSummary(models.Model):
    """Model for CAMS summary/portfolio data"""
    entity_name = models.CharField(max_length=255, help_text="Name of the entity/investor",null=True, blank=True)
    amc_name = models.CharField(max_length=255, help_text="Asset Management Company name",null=True, blank=True)
    folio_number = models.CharField(max_length=100, help_text="Folio number",null=True, blank=True)
    isin = models.CharField(max_length=20, help_text="ISIN code",null=True, blank=True)
    scheme_name = models.TextField(help_text="Mutual fund scheme name",null=True, blank=True)
    closing_unit_balance = models.DecimalField(max_digits=15, decimal_places=4, help_text="Closing unit balance",null=True, blank=True)
    nav = models.DecimalField(max_digits=15, decimal_places=4, help_text="Current Net Asset Value",null=True, blank=True)
    total_cost_value = models.DecimalField(max_digits=15, decimal_places=4, help_text="Total cost/investment value",null=True, blank=True)
    market_value = models.DecimalField(max_digits=15, decimal_places=4, help_text="Current market value",null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  

    
    class Meta:
        db_table = 'cams_summary'
        ordering = ['-market_value', '-created_at']
        indexes = [
            models.Index(fields=['folio_number']),
            models.Index(fields=['isin']),
            models.Index(fields=['entity_name']),
        ]
        unique_together = ['folio_number', 'isin']  # Prevent duplicate summary records
    
    def __str__(self):
        return f"{self.entity_name} - {self.folio_number} - ₹{self.market_value}"

    @property
    def gain_loss(self):
        """Calculate gain/loss"""
        return self.market_value - self.total_cost_value
    
    @property
    def gain_loss_percentage(self):
        """Calculate gain/loss percentage"""
        if self.total_cost_value > 0:
            return ((self.market_value - self.total_cost_value) / self.total_cost_value) * 100
        return 0