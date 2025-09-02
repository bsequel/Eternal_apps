from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard-cards/', views.dashboard_cards_view, name='dashboard_cards'),

    # API
    path('api/dummy-cases/', views.dummy_cases_api, name='dummy_cases_api'),

    # User Management
    path("users-json/", views.users_json, name="users_json"),
    path("create-user/", views.create_user_ajax, name="create_user"),
    path('update-user-role/<int:user_id>/',
         views.update_user_role, name='update_user_role'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    # Role Management
    path('update-role/', views.update_role_ajax, name='update_role_ajax'),



    # Dashboard permission management URLs
    path('users/dashboard-permissions/',
         views.user_dashboard_management,
         name='user_dashboard_management'),

    path('users/dashboard-permissions/update/',
         views.update_user_dashboard_permission,
         name='update_user_dashboard_permission'),

    path('users/<int:user_id>/edit-permissions/',
         views.edit_user_permissions,
         name='edit_user_permissions'),
]


# from django.urls import path
# from . import views
# # from .views import dummy_cases_api

# urlpatterns = [
#     path('',views.home),
#     path('register/', views.register_view, name='register'),
#     # path('login/', views.login_view, name='login'),
#     path('login/', views.login_view, name='login'),
#     path('logout/', views.logout_view, name='logout'),


#     # path('dashboard/', views.dashboard_view, name='dashboard'),
#     # path('dashboard-cards/', views.dashboard_cards_view, name='dashboard_cards'),


#     path('dashboard-cards/', views.dashboard_view, name='dashboard'),
#     path('dashboard/', views.dashboard_cards_view, name='dashboard_cards'),


#     path('update-role/', views.update_role_ajax, name='update_role_ajax'),
#     # path('api/dummy-cases/', dummy_cases_api, name='dummy_cases_api'),
#     path('api/dummy-cases/', views.dummy_cases_api, name='dummy_cases_api'),

#     # path('create-user/', views.create_user_ajax, name='create_user_ajax'),

#     # path("users-json/", views.users_json, name="users_json"),
#     # path("create-user/", views.create_user_ajax, name="create_user_ajax"),
#     path("users-json/", views.users_json, name="users_json"),
#     path("create-user/", views.create_user_ajax, name="create_user"),
#     path('update-user-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
#     path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
# ]
