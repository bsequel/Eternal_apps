from django.urls import path
from .views import run_pdf_etl, cases_api, update_case_status

urlpatterns = [
    path('run-etl/', run_pdf_etl, name='run_pdf_etl'),
    path('cases/', cases_api, name='cases_api'),
    path('cases/<int:sno>/update/', update_case_status, name='update_case_status'), 
]
