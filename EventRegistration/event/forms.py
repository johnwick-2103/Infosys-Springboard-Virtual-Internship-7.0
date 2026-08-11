from django import forms
from .models import Event, EventRegistration, Venue, Resource, Vendor, Budget

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'category', 'venue_ref', 'start_date', 'end_date', 'start_time', 'end_time',
                  'venue', 'location', 'description', 'banner', 'speaker_name', 'organizer',
                  'max_participants', 'registration_deadline', 'sponsors', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'id': 'event', 'placeholder': 'Enter event name'}),
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'category'}),
            'venue_ref': forms.Select(attrs={'class': 'form-control', 'id': 'venue_ref'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'start'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'end'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'venue': forms.TextInput(attrs={'class': 'form-control', 'id': 'venue', 'placeholder': 'Enter venue name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location/address'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'id': 'description', 'placeholder': 'Enter description', 'rows': 4}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
            'speaker_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Speaker / Guest name'}),
            'organizer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organizer name'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'registration_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sponsors': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sponsor names (comma-separated)'}),
            'status': forms.Select(attrs={'class': 'form-control', 'id': 'status'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be earlier than start date.")
        return cleaned_data


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ['event', 'full_name', 'email', 'phone']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control', 'id': 'event'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'email', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'phone', 'placeholder': 'Phone Number'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        clean_phone = ''.join(c for c in phone if c.isdigit())
        if len(clean_phone) != 10:
            raise forms.ValidationError("Mobile number must be exactly 10 digits.")
        return clean_phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        if not email.lower().endswith('@gmail.com'):
            raise forms.ValidationError("Email address must end with @gmail.com.")
        return email


from django.contrib.auth.models import User
from .models import UserProfile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if not email.endswith('@gmail.com'):
                raise forms.ValidationError("Email address must end with @gmail.com.")
        return email


class UsernameChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter new username',
                'autocomplete': 'off',
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError("Username cannot be empty.")
        qs = User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already taken. Please choose a different one.")
        return username


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'phone', 'profile_picture', 'department', 'designation', 'bio',
            'language', 'timezone', 'date_format', 'time_format', 'dashboard_layout',
            'show_email', 'show_phone', 'profile_visibility', 'allow_contact_requests',
            'event_updates', 'new_member_notifications', 'report_notifications', 'contact_messages', 'email_notifications',
            'email_login_alerts', 'password_change_alerts', 'security_notifications'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write a short bio about yourself...'}),
            'language': forms.Select(attrs={'class': 'form-select form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-select form-control'}),
            'date_format': forms.Select(attrs={'class': 'form-select form-control'}, choices=[
                ('DD/MM/YYYY', 'DD/MM/YYYY (31/07/2026)'),
                ('MM/DD/YYYY', 'MM/DD/YYYY (07/31/2026)'),
                ('YYYY-MM-DD', 'YYYY-MM-DD (2026-07-31)'),
                ('D MMM YYYY', 'D MMM YYYY (31 Jul 2026)'),
            ]),
            'time_format': forms.Select(attrs={'class': 'form-select form-control'}, choices=[
                ('12h', '12-hour (8:15 PM)'),
                ('24h', '24-hour (20:15)'),
            ]),
            'dashboard_layout': forms.Select(attrs={'class': 'form-select form-control'}, choices=[
                ('Grid', 'Grid Layout'),
                ('List', 'List Layout'),
                ('Compact', 'Compact View'),
                ('Detailed', 'Detailed View'),
            ]),
            'profile_visibility': forms.Select(attrs={'class': 'form-select form-control'}, choices=[
                ('Public', 'Public (Everyone)'),
                ('Members', 'Members Only'),
                ('Private', 'Private (Only Me)'),
            ]),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            clean_phone = ''.join(c for c in phone if c.isdigit())
            if len(clean_phone) != 10:
                raise forms.ValidationError("Mobile number must be exactly 10 digits.")
            return clean_phone
        return phone


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'location', 'address', 'capacity', 'contact_person', 'phone', 'email', 'available_date', 'image', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City / Area'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@venue.com'}),
            'available_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'resource_type', 'quantity', 'available_quantity', 'assigned_event', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resource name'}),
            'resource_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'assigned_event': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'company_name', 'service_type', 'phone', 'email', 'address',
                  'assigned_event', 'contract_status', 'payment_status', 'performance_rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor name'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'service_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Catering, AV, Decoration'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'vendor@email.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
            'assigned_event': forms.Select(attrs={'class': 'form-control'}),
            'contract_status': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'performance_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '5', 'step': '0.1'}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['event', 'total_budget', 'venue_cost', 'catering_cost', 'marketing_cost',
                  'equipment_cost', 'decoration_cost', 'staff_cost', 'transport_cost',
                  'other_expenses', 'sponsorship_amount']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'total_budget': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'venue_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'catering_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'marketing_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'equipment_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'decoration_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'staff_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'transport_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'other_expenses': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'sponsorship_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
        }
