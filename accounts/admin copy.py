from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # Form fields displayed when editing a user in admin
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'username')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Form fields when creating a new user in admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active'),
        }),
    )
    
    list_display = ('email', 'username', 'role', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)



























































# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import CustomUser

# # class CustomUserAdmin(UserAdmin):
# #     model = CustomUser
# #     list_display = ['username', 'email', 'role', 'is_staff']

# # admin.site.register(CustomUser, CustomUserAdmin)



# from django.contrib import admin
# from .models import CustomUser, CyberCellReport
# from django.contrib.auth.admin import UserAdmin

# @admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin):
#     model = CustomUser
#     list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
#     fieldsets = UserAdmin.fieldsets + (
#         ('Role Info', {'fields': ('role',)}),
#     )

# @admin.register(CyberCellReport)
# class CyberCellReportAdmin(admin.ModelAdmin):
#     list_display = ('reference_number', 'name', 'status', 'updated_by', 'updated_on')
#     list_filter = ('status', 'region', 'mail_month')
#     search_fields = ('reference_number', 'name', 'email_id', 'mobile_number')
