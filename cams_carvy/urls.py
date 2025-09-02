# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('cams-carvy/', views.cams_carvy_dashboard, name='cams_carvy_dashboard'),
    path('api/portfolio-data/', views.get_portfolio_data,
         name='get_portfolio_data'),


    path('api/update-isin/', views.update_isin, name='update_isin'),
    path('api/summary-stats/', views.get_summary_stats, name='get_summary_stats'),

    path('download/summary/', views.DownloadSummaryView.as_view(),
         name='download_summary'),
    path('download/detail/', views.DownloadDetailView.as_view(),
         name='download_detail'),

    path('run-cams-etl/', views.parse_cams_view, name='cams_import'),


    path('download-current/', views.download_current_month, name='download_current'),
    path('download-previous/', views.download_previous_month,
         name='download_previous'),

]


# # urls.py
# from django.urls import path
# from . import views

# urlpatterns = [
#     path('cams-carvy/', views.cams_carvy_dashboard, name='cams_carvy_dashboard'),
#     path('api/portfolio-data/', views.get_portfolio_data, name='get_portfolio_data'),
#     path('api/update-isin/', views.update_isin, name='update_isin'),
#     path('api/summary-stats/', views.get_summary_stats, name='get_summary_stats'),
# ]


# # urls.py
# from django.urls import path
# from .views import CamsCarbyView, CamsPortfolioAPIView, CamsSummaryAPIView

# app_name = 'cams'

# urlpatterns = [
#     path('cams/', CamsCarbyView.as_view(), name='cams_carvy'),
#     path('api/portfolio/', CamsPortfolioAPIView.as_view(), name='portfolio_api'),
#     path('api/summary/', CamsSummaryAPIView.as_view(), name='summary_api'),
# ]
