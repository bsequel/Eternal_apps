from django import forms
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()
        return user
# class RegisterForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput)
#     password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

#     class Meta:
#         model = CustomUser
#         fields = ['username', 'email', 'password', 'password2']

#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get("password")
#         password2 = cleaned_data.get("password2")

#         if password and password2 and password != password2:
#             raise forms.ValidationError("Passwords do not match")

#         return cleaned_data

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.set_password(self.cleaned_data['password'])  # use only password (not password2)
#         if commit:
#             user.save()
#         return user

# class LoginForm(forms.Form):
#     email = forms.EmailField()
#     password = forms.CharField(widget=forms.PasswordInput)


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class RoleUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['role']


class AdminCreateUserForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("password1")
        pw2 = cleaned_data.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CreateUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2',
                  'role']  # ✅ include all required fields

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


# forms.py


class UserDashboardPermissionForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'cyber_cell_access',
            'bank_balance_access',
            'payment_gateway_access',
            'cams_carvy_access',
            'consolidated_access'
        ]
        widgets = {
            'cyber_cell_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bank_balance_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_gateway_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cams_carvy_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'consolidated_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BulkDashboardPermissionForm(forms.Form):
    """Form for bulk updating dashboard permissions"""
    users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    cyber_cell_access = forms.BooleanField(
        required=False, label="Cyber Cell Dashboard")
    bank_balance_access = forms.BooleanField(
        required=False, label="Bank Balance Dashboard")
    payment_gateway_access = forms.BooleanField(
        required=False, label="Payment Gateway Dashboard")
    cams_carvy_access = forms.BooleanField(
        required=False, label="Cams Carvy Dashboard")
    consolidated_access = forms.BooleanField(
        required=False, label="Consolidated Dashboard")
