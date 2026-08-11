from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Venue(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Booked', 'Booked'),
        ('Under Maintenance', 'Under Maintenance'),
        ('Closed', 'Closed'),
    ]

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=0)
    contact_person = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    available_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='venue_images/', blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='events')
    venue_ref = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=200)
    location = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField()
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    speaker_name = models.CharField(max_length=200, blank=True, null=True)
    organizer = models.CharField(max_length=200, blank=True, null=True)
    max_participants = models.PositiveIntegerField(default=0)
    registration_deadline = models.DateField(null=True, blank=True)
    sponsors = models.CharField(max_length=500, blank=True, null=True)
    limit_participants = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def seats_remaining(self):
        registered = self.registrations.count()
        return max(0, self.max_participants - registered)

    @property
    def is_full(self):
        return self.seats_remaining == 0

    def __str__(self):
        return self.title

class EventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.event.title}"

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('Projector', 'Projector'),
        ('Sound System', 'Sound System'),
        ('Microphone', 'Microphone'),
        ('Chairs', 'Chairs'),
        ('Tables', 'Tables'),
        ('Lighting', 'Lighting'),
        ('Generator', 'Generator'),
        ('Decoration', 'Decoration'),
        ('Transport', 'Transport'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Allocated', 'Allocated'),
        ('Under Repair', 'Under Repair'),
        ('Unavailable', 'Unavailable'),
    ]

    name = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES, default='Other')
    quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    assigned_event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.resource_type})"

class Vendor(models.Model):
    CONTRACT_STATUS = [
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS = [
        ('Unpaid', 'Unpaid'),
        ('Partial', 'Partial'),
        ('Paid', 'Paid'),
    ]

    name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    service_type = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    assigned_event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendors')
    contract_status = models.CharField(max_length=20, choices=CONTRACT_STATUS, default='Pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Unpaid')
    performance_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} – {self.service_type}"

class Budget(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='budget')
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    venue_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    catering_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    marketing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    equipment_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    decoration_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    staff_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sponsorship_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_expenses(self):
        return (self.venue_cost + self.catering_cost + self.marketing_cost +
                self.equipment_cost + self.decoration_cost + self.staff_cost +
                self.transport_cost + self.other_expenses)

    @property
    def remaining_budget(self):
        return self.total_budget + self.sponsorship_amount - self.total_expenses

    def __str__(self):
        return f"Budget – {self.event.title}"

class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('event', 'New Event'),
        ('reminder', 'Event Reminder'),
        ('registration', 'Registration'),
        ('member', 'Member Added'),
        ('completed', 'Event Completed'),
        ('budget', 'Budget Warning'),
        ('venue', 'Venue Booking'),
        ('approval', 'Pending Approval'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user}: {self.message[:50]}"

class Ticket(models.Model):
    registration = models.OneToOneField(EventRegistration, on_delete=models.CASCADE, related_name='ticket')
    ticket_number = models.CharField(max_length=20, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.ticket_number} – {self.registration.full_name}"

class AttendanceRecord(models.Model):
    ATTENDANCE_STATUS = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    registration = models.OneToOneField(EventRegistration, on_delete=models.CASCADE, related_name='attendance')
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='Absent')
    check_in_time = models.DateTimeField(null=True, blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_attendances')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration.full_name} – {self.status}"

class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('profile_update', 'Profile Updated'),
        ('password_change', 'Password Changed'),
        ('event_create', 'Event Created'),
        ('event_update', 'Event Updated'),
        ('event_delete', 'Event Deleted'),
        ('category_create', 'Category Created'),
        ('member_add', 'Member Added'),
        ('report_generate', 'Report Generated'),
        ('ticket_generate', 'Ticket Generated'),
        ('attendance_mark', 'Attendance Marked'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} – {self.action} at {self.created_at}"

class UserProfile(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('zh', 'Chinese'),
        ('ar', 'Arabic'),
        ('pt', 'Portuguese'),
        ('ja', 'Japanese'),
        ('ru', 'Russian'),
    ]

    TIMEZONE_CHOICES = [
        ('Asia/Kolkata', 'India (IST, UTC+5:30)'),
        ('UTC', 'UTC (Coordinated Universal Time)'),
        ('America/New_York', 'New York (EST/EDT, UTC-5/-4)'),
        ('America/Chicago', 'Chicago (CST/CDT, UTC-6/-5)'),
        ('America/Denver', 'Denver (MST/MDT, UTC-7/-6)'),
        ('America/Los_Angeles', 'Los Angeles (PST/PDT, UTC-8/-7)'),
        ('Europe/London', 'London (GMT/BST, UTC+0/+1)'),
        ('Europe/Paris', 'Paris (CET/CEST, UTC+1/+2)'),
        ('Europe/Berlin', 'Berlin (CET/CEST, UTC+1/+2)'),
        ('Asia/Dubai', 'Dubai (GST, UTC+4)'),
        ('Asia/Singapore', 'Singapore (SGT, UTC+8)'),
        ('Asia/Tokyo', 'Tokyo (JST, UTC+9)'),
        ('Australia/Sydney', 'Sydney (AEST/AEDT, UTC+10/+11)'),
        ('Pacific/Auckland', 'Auckland (NZST/NZDT, UTC+12/+13)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, default='IT')
    designation = models.CharField(max_length=100, blank=True, default='Organizer')
    bio = models.TextField(blank=True, null=True, default='')

    # Notifications settings
    receive_notifications = models.BooleanField(default=True)
    event_updates = models.BooleanField(default=True)
    new_member_notifications = models.BooleanField(default=True)
    report_notifications = models.BooleanField(default=True)
    contact_messages = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)

    # Security notifications
    email_login_alerts = models.BooleanField(default=True)
    password_change_alerts = models.BooleanField(default=True)
    security_notifications = models.BooleanField(default=True)

    # Appearance & Preferences
    theme_preference = models.CharField(max_length=20, default='slate')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='Asia/Kolkata')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    time_format = models.CharField(max_length=10, default='12h')
    dashboard_layout = models.CharField(max_length=20, default='Grid')

    # Privacy Settings
    show_email = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=False)
    profile_visibility = models.CharField(max_length=20, default='Public')
    allow_contact_requests = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
    instance.profile.save()

class EventWatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='watched_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} watching {self.event.title}"

class UserMark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marks')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='marks_recorded')
    mark = models.IntegerField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.title}: {self.mark}"
