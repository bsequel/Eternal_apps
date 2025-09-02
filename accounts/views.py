from datetime import datetime, timedelta
import random
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from .forms import AdminCreateUserForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
# from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import RegisterForm, LoginForm, RoleUpdateForm, AdminCreateUserForm
from .models import CustomUser
from .decorators import role_required
from django.shortcuts import get_object_or_404
User = get_user_model()
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import json
from .models import CustomUser
from .forms import UserDashboardPermissionForm, BulkDashboardPermissionForm

def home(request):
    return render(request, 'accounts/index.html')


VIEW_ONLY_EMAILS = ['bheem@gmail.com', 'anumeha@gmail.com']
ADMIN_EMAILS = ['huzefa1@gmail.com', 'anuska@gmail.com']


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            if user.email in VIEW_ONLY_EMAILS:
                user.role = 'viewer'
            elif user.email in ADMIN_EMAILS:
                user.role = 'admin'
            else:
                user.role = 'viewer'

            user.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # username=email because USERNAME_FIELD='email'
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                # return redirect('home')
                return redirect('dashboard_cards')
            else:
                form.add_error(None, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# @role_required('admin')
@login_required
def dashboard_view(request):
    if request.user.role != 'admin':
        users = CustomUser.objects.all()
        section = request.GET.get("section", "cyber-cell")
        return render(request, 'accounts/dashboard_viewer.html', {
            'users': users,
            'active_section': section
        })

    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            # Redirect to avoid re-submitting the form
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCreateUserForm()

    users = CustomUser.objects.all()
    section = request.GET.get("section", "cyber-cell")
    return render(request, 'accounts/dashboard.html', {
        'create_form': form,
        'users': users,
        'active_section': section
    })
    # return render(request, 'accounts/home.html')


# @role_required('admin')
@login_required
def dashboard_cards_view(request):

    if request.user.role == 'admin':
        return render(request, 'accounts/dashboard_cards.html')
    else:
        return render(request, 'accounts/dashboard_cards_viewer.html')


@require_POST
@login_required
def update_role_ajax(request):
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    user_id = request.POST.get('user_id')
    new_role = request.POST.get('role')

    if new_role not in ['admin', 'viewer']:
        return JsonResponse({'success': False, 'error': 'Invalid role.'}, status=400)

    try:
        user = User.objects.get(pk=user_id)
        user.role = new_role
        user.save()
        return JsonResponse({'success': True, 'message': 'Role updated successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)


# @require_POST
# @login_required
# def create_user_ajax(request):
#     if not hasattr(request.user, 'role') or request.user.role != 'admin':
#         return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

#     form = AdminCreateUserForm(request.POST)
#     if form.is_valid():
#         form.save()
#         return JsonResponse({'success': True, 'message': 'User created successfully.'})
#     else:
#         return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)


@login_required
@api_view(['GET'])
def dummy_cases_api(request):
    statuses = ['Pending', 'Picked', 'Closed']
    regions = ['North', 'South', 'East', 'West']
    stations = ['Station A', 'Station B', 'Station C', 'Station D']

    def random_date(start, end):
        return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

    start_date = datetime.now() - timedelta(days=180)
    end_date = datetime.now()
    cases = []
    for i in range(1, 61):  # 60 rows
        complaint_date = random_date(start_date, end_date)
        mail_date = complaint_date + timedelta(days=random.randint(0, 5))
        transaction_date = mail_date + timedelta(days=random.randint(0, 5))
        total_fraud = round(random.uniform(1000, 100000), 2)
        cases.append({
            'sno': i,
            'complaint_date': complaint_date.strftime('%Y-%m-%d'),
            'mail_date': mail_date.strftime('%Y-%m-%d'),
            'mail_month': mail_date.strftime('%B'),
            'amount': f'₹{round(random.uniform(1000, 100000), 2)}',
            'reference_number': f'REF{random.randint(10000,99999)}',
            'police_station_address': random.choice(stations),
            'account_number': f'{random.randint(10000000,99999999)}',
            'name': f'User {i}',
            'mobile_number': f'+91{random.randint(9000000000,9999999999)}',
            'email_id': f'user{i}@example.com',
            'status': random.choice(statuses),
            'ageing_days': (datetime.now() - complaint_date).days,
            'debit_from_bank': random.choice(['Yes', 'No']),
            'region': random.choice(regions),
            'utr_number': f'UTR{random.randint(1000000000,9999999999)}',
            'utr_amount': f'₹{round(random.uniform(1000, 100000), 2)}',
            'transaction_datetime': transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
            'total_fraudulent_amount': f'₹{total_fraud}',
            'updated_on': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'updated_by': 'Admin',
        })
    total_amount = sum(
        float(c['total_fraudulent_amount'].replace('₹', '')) for c in cases)
    return Response({
        'cases': cases,
        'total_amount': f'₹{total_amount:,.2f}'
    })


# def users_json(request):
#     users = []
#     for u in User.objects.all():
#         badge_class = "badge-admin" if u.role == "admin" else "badge-viewer"
#         role_badge = f'<span class="badge {badge_class}" id="role-badge-{u.id}">{u.role.title()}</span>'
#         role_select = f"""
#             <select class="form-select form-select-sm"
#                     onchange="updateUserRole('{u.id}', this.value)">
#                 <option value="viewer" {"selected" if u.role == "viewer" else ""}>Viewer</option>
#                 <option value="admin" {"selected" if u.role == "admin" else ""}>Admin</option>
#             </select>
#         """
#         users.append({
#             "username": u.username,
#             "email": u.email,
#             "role_badge": role_badge,
#             "role_select": role_select
#         })
#     return JsonResponse({"data": users})


# def users_json(request):
#     # DataTables params
#     draw = int(request.GET.get("draw", 1))
#     start = int(request.GET.get("start", 0))
#     length = int(request.GET.get("length", 10))
#     search_value = request.GET.get("search[value]", "")
#     order_column_index = request.GET.get("order[0][column]", "0")
#     order_dir = request.GET.get("order[0][dir]", "asc")

#     # Map column index → model field
#     columns = ["id", "username", "email", "role"]
#     order_column = columns[int(order_column_index)]

#     # Queryset
#     qs = User.objects.all()

#     # Searching
#     if search_value:
#         qs = qs.filter(username__icontains=search_value) | qs.filter(
#             email__icontains=search_value)

#     records_total = User.objects.count()
#     records_filtered = qs.count()

#     # Ordering
#     if order_dir == "desc":
#         order_column = f"-{order_column}"
#     qs = qs.order_by(order_column)

#     # Pagination
#     qs = qs[start:start+length]

#     # Format response
#     data = [
#         {
#             "id": u.id,
#             "username": u.username,
#             "email": u.email,
#             "role": u.role,
#         }
#         for u in qs
#     ]

#     return JsonResponse({
#         "draw": draw,
#         "recordsTotal": records_total,
#         "recordsFiltered": records_filtered,
#         "data": data,
#     })

# views.py

User = get_user_model()


def users_json(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # Filter users by search
    qs = User.objects.all()
    if search_value:
        qs = qs.filter(username__icontains=search_value)

    total = User.objects.count()
    filtered = qs.count()

    # Ordering
    order_column_index = request.GET.get('order[0][column]')
    order_dir = request.GET.get('order[0][dir]')
    columns = ['id', 'username', 'email', 'role']

    if order_column_index is not None and order_dir is not None:
        order_column = columns[int(order_column_index)]
        if order_dir == 'desc':
            order_column = '-' + order_column
        qs = qs.order_by(order_column)
    else:
        # ✅ Default ordering: newest first
        qs = qs.order_by('-id')

    # Pagination
    qs = qs[start:start + length]

    data = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role
        }
        for u in qs
    ]

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })


@require_POST
@login_required
def update_user_role(request, user_id):
    if request.method == "POST":
        role = request.POST.get("role")
        user = get_object_or_404(User, id=user_id)
        user.role = role
        user.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@require_POST
@login_required
def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@require_POST
@login_required
def create_user_ajax(request):
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    form = AdminCreateUserForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': 'User created successfully.'})

    # DEBUG LOGGING
    print("Form errors:", form.errors.get_json_data())

    errors = {field: [err['message'] for err in errs]
              for field, errs in form.errors.get_json_data().items()}
    return JsonResponse({'success': False, 'errors': errors}, status=400)








def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.role == 'admin'
def is_viewer(user):
    """Check if user is admin"""
    return user.is_authenticated and user.role == 'viewer'

@login_required
@user_passes_test(is_admin)
def user_dashboard_management(request):
    """Main view for managing user dashboard permissions"""
    users = CustomUser.objects.all().order_by('email')
    
    # Handle bulk update
    if request.method == 'POST':
        bulk_form = BulkDashboardPermissionForm(request.POST)
        if bulk_form.is_valid():
            selected_users = bulk_form.cleaned_data['users']
            
            # Update permissions for selected users
            for user in selected_users:
                user.cyber_cell_access = bulk_form.cleaned_data['cyber_cell_access']
                user.bank_balance_access = bulk_form.cleaned_data['bank_balance_access']
                user.payment_gateway_access = bulk_form.cleaned_data['payment_gateway_access']
                user.cams_carvy_access = bulk_form.cleaned_data['cams_carvy_access']
                user.consolidated_access = bulk_form.cleaned_data['consolidated_access']
                user.save()
            
            messages.success(request, f'Dashboard permissions updated for {len(selected_users)} users.')
            return redirect('user_dashboard_management')
    else:
        bulk_form = BulkDashboardPermissionForm()
    
    context = {
        'users': users,
        'bulk_form': bulk_form,
    }
    return render(request, 'accounts/dashboard_permissions.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def update_user_dashboard_permission(request):
    """AJAX view to update individual dashboard permissions"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        dashboard = data.get('dashboard')
        enabled = data.get('enabled', False)
        
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Map dashboard names to model fields
        dashboard_fields = {
            'cyber_cell': 'cyber_cell_access',
            'bank_balance': 'bank_balance_access',
            'payment_gateway': 'payment_gateway_access',
            'cams_carvy': 'cams_carvy_access',
            'consolidated': 'consolidated_access',
        }
        
        if dashboard in dashboard_fields:
            setattr(user, dashboard_fields[dashboard], enabled)
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Dashboard permission updated for {user.email}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid dashboard name'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@user_passes_test(is_admin)
def edit_user_permissions(request, user_id):
    """Edit individual user dashboard permissions"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = UserDashboardPermissionForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dashboard permissions updated for {user.email}')
            return redirect('user_dashboard_management')
    else:
        form = UserDashboardPermissionForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'accounts/edit_permissions.html', context)