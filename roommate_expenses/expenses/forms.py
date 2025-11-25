# expenses/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Group, Expense
import re

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password must contain both letters and numbers.")
        return password
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

class GroupJoinForm(forms.Form):
    code = forms.CharField(max_length=20, label="Group Code")
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not Group.objects.filter(code=code).exists():
            raise forms.ValidationError("Invalid group code. Please check and try again.")
        return code

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'paid_by', 'shared_among']
        widgets = {
            'shared_among': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, group=None, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        if group:
            # Limit user choices to the current group members
            group_members = group.members.all()
            self.fields['paid_by'].queryset = group_members
            self.fields['shared_among'].queryset = group_members