# models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import decimal
from django.conf import settings
from django.db import models
from django.conf import settings
from decimal import Decimal
import hashlib, json, decimal


class CamsPortfolio(models.Model):
    folio_no = models.CharField(max_length=20, verbose_name="Folio Number")
    entity_name = models.CharField(max_length=200, verbose_name="Entity Name")
    isin = models.CharField(
        max_length=12,
        verbose_name="ISIN",
        help_text="International Securities Identification Number",
        null=True,
        blank=True
    )
    scheme_name = models.CharField(max_length=200, verbose_name="Scheme Name")
    cost_value = models.CharField(max_length=50, verbose_name="Cost Value (INR)")
    unit_balance = models.CharField(max_length=50, verbose_name="Unit Balance")
    nav_date = models.DateField(verbose_name="NAV Date")
    market_value = models.CharField(max_length=50, verbose_name="Market Value (INR)")

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    # Additional fields for filtering
    month = models.IntegerField(verbose_name="Month", help_text="1-12", null=True, blank=True)
    year = models.IntegerField(verbose_name="Year", null=True, blank=True)

    # Hash field
    entry_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)

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

    # ---------- 🔹 Calculated Properties ----------
    @property
    def profit_loss(self):
        try:
            market_val = Decimal(str(self.market_value).replace(',', '')) if self.market_value else Decimal('0')
            cost_val = Decimal(str(self.cost_value).replace(',', '')) if self.cost_value else Decimal('0')
            return market_val - cost_val
        except (ValueError, TypeError, decimal.InvalidOperation):
            return Decimal('0')

    @property
    def profit_loss_percentage(self):
        try:
            market_val = Decimal(str(self.market_value).replace(',', '')) if self.market_value else Decimal('0')
            cost_val = Decimal(str(self.cost_value).replace(',', '')) if self.cost_value else Decimal('0')
            if cost_val > 0:
                return float(((market_val - cost_val) / cost_val) * 100)
            return 0
        except (ValueError, TypeError, decimal.InvalidOperation):
            return 0

    @property
    def is_profit(self):
        try:
            market_val = Decimal(str(self.market_value).replace(',', '')) if self.market_value else Decimal('0')
            cost_val = Decimal(str(self.cost_value).replace(',', '')) if self.cost_value else Decimal('0')
            return market_val > cost_val
        except (ValueError, TypeError, decimal.InvalidOperation):
            return False

    # ---------- 🔹 Summary ----------
    @classmethod
    def get_summary_stats(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()

        from django.db.models import Count

        total_market_value = Decimal('0')
        total_cost_value = Decimal('0')

        for item in queryset:
            try:
                if item.market_value:
                    total_market_value += Decimal(str(item.market_value).replace(',', ''))
                if item.cost_value:
                    total_cost_value += Decimal(str(item.cost_value).replace(',', ''))
            except (ValueError, TypeError, decimal.InvalidOperation):
                continue

        stats = queryset.aggregate(
            total_entities=Count('entity_name', distinct=True),
            total_folios=Count('folio_no', distinct=True),
        )

        stats['total_market_value'] = total_market_value
        stats['total_cost_value'] = total_cost_value

        for key, value in stats.items():
            if value is None:
                stats[key] = 0

        return stats

    # ---------- 🔹 Entry Hash ----------
    def generate_hash(self):
        """Generate SHA-256 hash from all key fields"""
        hash_data = {
            'folio_no': self.folio_no,
            'entity_name': self.entity_name,
            'isin': self.isin,
            'scheme_name': self.scheme_name,
            'cost_value': self.cost_value,
            'unit_balance': self.unit_balance,
            'nav_date': str(self.nav_date) if self.nav_date else None,
            'market_value': self.market_value,
            'month': self.month,
            'year': self.year,
        }
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def save(self, *args, **kwargs):
        """Auto-generate entry_hash before saving"""
        if not self.entry_hash:
            self.entry_hash = self.generate_hash()
        super().save(*args, **kwargs)

    

# =======================     consolidated   ========================
# =======================     consolidated   ========================



from django.db import models
import hashlib, json


class CAMSTransaction(models.Model):
    """Model for CAMS transaction data"""
    entity_name = models.CharField(max_length=255, help_text="Name of the entity/investor")
    amc_name = models.CharField(max_length=255, help_text="Asset Management Company name")
    folio_number = models.CharField(max_length=100, help_text="Folio number")
    isin = models.CharField(max_length=20, help_text="ISIN code")
    scheme_name = models.TextField(help_text="Mutual fund scheme name")
    transaction_date = models.DateField(null=True, blank=True, help_text="Date of transaction")
    transaction_description = models.CharField(max_length=255, null=True, blank=True, help_text="Transaction type/description")
    value = models.CharField(max_length=50, null=True, blank=True, help_text="Transaction value")
    stamp_duty = models.CharField(max_length=50, null=True, blank=True, help_text="Stamp duty amount")
    units = models.CharField(max_length=50, null=True, blank=True, help_text="Number of units")
    nav = models.CharField(max_length=50, null=True, blank=True, help_text="Net Asset Value")
    unit_balance = models.CharField(max_length=50, null=True, blank=True, help_text="Unit balance after transaction")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 🔹 Hash field
    entry_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'cams_transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['folio_number']),
            models.Index(fields=['isin']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['entity_name']),
            models.Index(fields=['amc_name']),
            models.Index(fields=['scheme_name']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_description']),
            models.Index(fields=['value']),
            models.Index(fields=['stamp_duty']),
            models.Index(fields=['units']),
            models.Index(fields=['nav']),
            models.Index(fields=['unit_balance']),
        ]
        unique_together = ['folio_number', 'isin','entity_name','amc_name','scheme_name','transaction_date','transaction_description','value','stamp_duty','units','nav','unit_balance']

    def __str__(self):
        return f"{self.entity_name} - {self.folio_number} - {self.transaction_date}"

    # ---------- 🔹 Entry Hash ----------
    def generate_hash(self):
        """Generate SHA-256 hash from all fields"""
        hash_data = {
            'entity_name': self.entity_name,
            'amc_name': self.amc_name,
            'folio_number': self.folio_number,
            'isin': self.isin,
            'scheme_name': self.scheme_name,
            'transaction_date': str(self.transaction_date) if self.transaction_date else None,
            'transaction_description': self.transaction_description,
            'value': self.value,
            'stamp_duty': self.stamp_duty,
            'units': self.units,
            'nav': self.nav,
            'unit_balance': self.unit_balance,
        }
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def save(self, *args, **kwargs):
        """Auto-generate entry_hash before saving"""
        if not self.entry_hash:
            self.entry_hash = self.generate_hash()
        super().save(*args, **kwargs)


from django.db import models
from decimal import Decimal
import hashlib, json, decimal


class CAMSSummary(models.Model):
    """Model for CAMS summary/portfolio data"""
    entity_name = models.CharField(max_length=255, help_text="Name of the entity/investor", null=True, blank=True)
    amc_name = models.CharField(max_length=255, help_text="Asset Management Company name", null=True, blank=True)
    folio_number = models.CharField(max_length=100, help_text="Folio number", null=True, blank=True)
    isin = models.CharField(max_length=20, help_text="ISIN code", null=True, blank=True)
    scheme_name = models.TextField(help_text="Mutual fund scheme name", null=True, blank=True)
    closing_unit_balance = models.CharField(max_length=50, help_text="Closing unit balance", null=True, blank=True)
    nav = models.CharField(max_length=50, help_text="Current Net Asset Value", null=True, blank=True)
    total_cost_value = models.CharField(max_length=50, help_text="Total cost/investment value", null=True, blank=True)
    market_value = models.CharField(max_length=50, help_text="Current market value", null=True, blank=True)
    nav_date = models.DateField(null=True, blank=True, help_text="Date of nav")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 🔹 Hash field
    entry_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'cams_summary'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['folio_number']),
            models.Index(fields=['isin']),
            models.Index(fields=['entity_name']),
            models.Index(fields=['amc_name']),
            models.Index(fields=['scheme_name']),
            models.Index(fields=['closing_unit_balance']),
            models.Index(fields=['nav']),
            models.Index(fields=['total_cost_value']),
            models.Index(fields=['market_value']),
            models.Index(fields=['nav_date']),
        ]
        unique_together = ['folio_number', 'isin','entity_name','amc_name','scheme_name','closing_unit_balance','nav','total_cost_value','market_value','nav_date']  # Prevent duplicate summary records

    def __str__(self):
        return f"{self.entity_name} - {self.folio_number} - ₹{self.market_value}"

    # ---------- 🔹 Gain/Loss ----------
    @property
    def gain_loss(self):
        """Calculate gain/loss"""
        try:
            market_val = Decimal(str(self.market_value).replace(',', '')) if self.market_value else Decimal('0')
            cost_val = Decimal(str(self.total_cost_value).replace(',', '')) if self.total_cost_value else Decimal('0')
            return market_val - cost_val
        except (ValueError, TypeError, decimal.InvalidOperation):
            return Decimal('0')

    @property
    def gain_loss_percentage(self):
        """Calculate gain/loss percentage"""
        try:
            market_val = Decimal(str(self.market_value).replace(',', '')) if self.market_value else Decimal('0')
            cost_val = Decimal(str(self.total_cost_value).replace(',', '')) if self.total_cost_value else Decimal('0')
            if cost_val > 0:
                return float(((market_val - cost_val) / cost_val) * 100)
            return 0
        except (ValueError, TypeError, decimal.InvalidOperation):
            return 0

    # ---------- 🔹 Entry Hash ----------
    def generate_hash(self):
        """Generate SHA-256 hash from all fields"""
        hash_data = {
            'entity_name': self.entity_name,
            'amc_name': self.amc_name,
            'folio_number': self.folio_number,
            'isin': self.isin,
            'scheme_name': self.scheme_name,
            'closing_unit_balance': self.closing_unit_balance,
            'nav': self.nav,
            'total_cost_value': self.total_cost_value,
            'market_value': self.market_value,
        }
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def save(self, *args, **kwargs):
        """Auto-generate entry_hash before saving"""
        if not self.entry_hash:
            self.entry_hash = self.generate_hash()
        super().save(*args, **kwargs)
