# management/commands/create_sample_cams_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random
from cams_carvy.models import CamsPortfolio  # Replace 'your_app' with your actual app name

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample CAMS portfolio data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--records',
            type=int,
            default=50,
            help='Number of sample records to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new records'
        )

    def handle(self, *args, **options):
        # Get or create a default user
        user, created = User.objects.get_or_create(
            username='system_admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'System',
                'last_name': 'Admin'
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f"Created user: {user.username}")

        # Clear existing data if requested
        if options['clear']:
            CamsPortfolio.objects.all().delete()
            self.stdout.write("Cleared existing CAMS portfolio data")

        # Sample data arrays
        entity_names = [
            'ACME Corporation Ltd',
            'Tech Innovations Pvt Ltd',
            'Global Solutions Ltd',
            'Digital Dynamics Corp',
            'Smart Systems Ltd',
            'Future Tech Industries',
            'Quantum Solutions Pvt Ltd',
            'NextGen Technologies',
            'Alpha Enterprises Ltd',
            'Beta Holdings Corp'
        ]

        scheme_names = [
            'HDFC Top 100 Fund - Growth',
            'ICICI Prudential Bluechip Fund',
            'SBI Large Cap Fund - Regular',
            'Axis Bluechip Fund - Growth',
            'Kotak Select Focus Fund',
            'DSP Midcap Fund - Regular',
            'Franklin India Prima Fund',
            'Aditya Birla SL Frontline Equity Fund',
            'Nippon India Large Cap Fund',
            'UTI Mastershare Unit Scheme'
        ]

        # Create sample records
        records_created = 0
        for i in range(options['records']):
            # Generate random data
            folio_no = f"{random.randint(10000000, 99999999)}/{random.randint(10, 99)}"
            entity_name = random.choice(entity_names)
            isin = f"INE{random.randint(100, 999)}{random.choice(['A', 'B', 'C'])}01{random.randint(10, 99)}"
            scheme_name = random.choice(scheme_names)
            
            # Generate financial data
            cost_value = Decimal(random.randint(25000, 200000))
            unit_balance = Decimal(f"{random.uniform(500, 5000):.3f}")
            
            # Market value with some profit/loss variation
            market_multiplier = random.uniform(0.8, 1.3)  # -20% to +30%
            market_value = Decimal(f"{float(cost_value) * market_multiplier:.2f}")
            
            # Random NAV date within last 30 days
            nav_date = date.today() - timedelta(days=random.randint(0, 30))
            
            # Month and year from nav_date
            month = nav_date.month
            year = nav_date.year

            # Create the record
            portfolio = CamsPortfolio.objects.create(
                folio_no=folio_no,
                entity_name=entity_name,
                isin=isin,
                scheme_name=scheme_name,
                cost_value=cost_value,
                unit_balance=unit_balance,
                nav_date=nav_date,
                market_value=market_value,
                month=month,
                year=year,
                updated_by=user
            )
            
            records_created += 1
            
            if records_created % 10 == 0:
                self.stdout.write(f"Created {records_created} records...")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {records_created} CAMS portfolio records'
            )
        )
        
        # Display summary statistics
        stats = CamsPortfolio.get_summary_stats()
        self.stdout.write("\nSummary Statistics:")
        self.stdout.write(f"Total Entities: {stats['total_entities']}")
        self.stdout.write(f"Total Folios: {stats['total_folios']}")
        self.stdout.write(f"Total Market Value: ₹{stats['total_market_value']:,.2f}")
        self.stdout.write(f"Total Cost Value: ₹{stats['total_cost_value']:,.2f}")
        
        profit_loss = stats['total_market_value'] - stats['total_cost_value']
        self.stdout.write(f"Total P&L: ₹{profit_loss:,.2f}")
        
        if stats['total_cost_value'] > 0:
            profit_loss_pct = (profit_loss / stats['total_cost_value']) * 100
            self.stdout.write(f"P&L Percentage: {profit_loss_pct:.2f}%")