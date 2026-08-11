from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Avg
from .models import (Event, Category, EventRegistration, UserProfile, EventWatch, UserMark,
                     Venue, Resource, Vendor, Budget, Notification, Ticket, AttendanceRecord, ActivityLog)
from .forms import (EventForm, RegistrationForm, UserUpdateForm, UserProfileUpdateForm, UsernameChangeForm,
                    VenueForm, ResourceForm, VendorForm, BudgetForm)
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
import csv
import uuid
import os


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip if ip not in ['127.0.0.1', '::1'] else '192.168.1.104'


def log_activity(user, action, description='', request=None):
    """Helper to create an ActivityLog entry."""
    ip = get_client_ip(request) if request else None
    ActivityLog.objects.create(user=user, action=action, description=description, ip_address=ip)


def notify(user, message, category='system', link=None):
    """Helper to create a Notification entry."""
    Notification.objects.create(user=user, message=message, category=category, link=link)


# ─────────────────────────────────────────────
# PUBLIC PAGES
# ─────────────────────────────────────────────
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    total_events = Event.objects.count()
    completed_events = Event.objects.filter(status='Completed').count()
    total_users = User.objects.filter(is_staff=False).count()
    categories_count = Category.objects.count()
    active_events = Event.objects.filter(status='Active').select_related('category').order_by('-start_date')[:6]
    context = {
        'total_events': total_events,
        'completed_events': completed_events,
        'total_users': total_users,
        'categories_count': categories_count,
        'active_events': active_events,
    }
    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        messages.success(request, f"Thank you, {name}! Your message has been sent successfully.")
        return redirect('contact')
    return render(request, 'contact.html')


def faq(request):
    return render(request, 'faq.html')


def gallery(request):
    return render(request, 'gallery.html')


# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        passw = request.POST.get('password')
        user = authenticate(request, username=username, password=passw)
        if user is not None:
            auth_login(request, user)
            log_activity(user, 'login', f'Logged in from {get_client_ip(request)}', request)
            messages.success(request, f"Login successful! Welcome, {user.first_name or user.username}.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, 'logout', 'User logged out', request)
    auth_logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    events = Event.objects.filter(status='Active')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        country_code = request.POST.get('country_code', '')
        if phone:
            phone = phone.strip()
            if ' ' in phone:
                parts = phone.split()
                phone = parts[-1]
                if not country_code:
                    country_code = parts[0]
            elif phone.startswith('+') and len(phone) > 10:
                country_code = phone[:-10]
                phone = phone[-10:]
        full_name = request.POST.get('name')
        password = request.POST.get('password')

        if not username or not password or not email:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'signup.html', {'events': events})

        clean_phone = ''.join(c for c in phone if c.isdigit()) if phone else ''
        if len(clean_phone) != 10:
            messages.error(request, "Signup failed. Mobile number must contain exactly 10 digits.")
            return render(request, 'signup.html', {'events': events})

        clean_email = email.lower().strip() if email else ''
        if not clean_email.endswith('@gmail.com'):
            messages.error(request, "Signup failed. Email must be a valid @gmail.com address.")
            return render(request, 'signup.html', {'events': events})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'signup.html', {'events': events})

        first_name = full_name
        last_name = ""
        if full_name and " " in full_name:
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1]

        user = User.objects.create_user(
            username=username, email=clean_email, password=password,
            first_name=first_name, last_name=last_name
        )
        full_phone = f"{country_code} {clean_phone}".strip() if country_code else clean_phone
        UserProfile.objects.create(user=user, phone=full_phone)

        event_id = request.POST.get('event_id')
        if event_id:
            event = Event.objects.filter(id=event_id).first()
            if event:
                if event.limit_participants and EventRegistration.objects.filter(event=event).count() >= event.max_participants:
                    messages.warning(request, f"User created, but registration failed as the event is full.")
                else:
                    reg = EventRegistration.objects.create(
                        user=user, event=event,
                        full_name=full_name or username, email=clean_email, phone=full_phone
                    )
                    _generate_ticket(reg)
                    messages.success(request, f"Registered for '{event.title}' successfully!")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            log_activity(user, 'login', 'Account created and logged in', request)
            messages.success(request, "Account created and logged in successfully!")
            return redirect('dashboard')

    return render(request, 'signup.html', {'events': events})


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@login_required(login_url='login')
def dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        total_events = Event.objects.count()
        total_participants = EventRegistration.objects.count()
        upcoming_events = Event.objects.filter(status='Pending').count()
        completed_events = Event.objects.filter(status='Completed').count()
        total_categories = Category.objects.count()
        total_venues = Venue.objects.count()
        total_vendors = Vendor.objects.count()
        total_resources = Resource.objects.count()
        total_members = User.objects.filter(is_staff=False).count()
        active_events_count = Event.objects.filter(status='Active').count()

        # Budget totals
        budgets = Budget.objects.all()
        total_budget_sum = sum(float(b.total_budget) for b in budgets)
        total_sponsorship_sum = sum(float(b.sponsorship_amount) for b in budgets)
        total_expenses_sum = sum(float(b.total_expenses) for b in budgets)
        budget_remaining = total_budget_sum + total_sponsorship_sum - total_expenses_sum

        recent_events = Event.objects.select_related('category').order_by('-created_at')[:5]
        upcoming_event_list = Event.objects.filter(status__in=['Active', 'Pending']).order_by('start_date')[:5]
        recent_members = EventRegistration.objects.select_related('event').order_by('-registration_date')[:5]
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

        # Chart 1: Events by Category
        categories = Category.objects.annotate(count=Count('events'))
        cat_labels = [c.name for c in categories]
        cat_data = [c.count for c in categories]

        # Chart 2: Status Distribution
        statuses = ['Active', 'Completed', 'Pending', 'Cancelled']
        status_counts = [Event.objects.filter(status=s).count() for s in statuses]

        # Chart 3: Members by Department
        dept_map = {}
        for profile in UserProfile.objects.all():
            dept = profile.department or 'IT'
            dept_map[dept] = dept_map.get(dept, 0) + 1
        dept_labels = list(dept_map.keys()) or ['IT', 'Engineering', 'Marketing', 'HR']
        dept_counts = list(dept_map.values()) or [0, 0, 0, 0]

        # Chart 4: Monthly Events
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        monthly_event_counts = {m: 0 for m in month_names}
        for event in Event.objects.all():
            m_name = event.start_date.strftime('%B')
            if m_name in monthly_event_counts:
                monthly_event_counts[m_name] += 1
        active_months = [m for m in month_names if monthly_event_counts[m] > 0] or month_names[:6]
        active_month_data = [monthly_event_counts[m] for m in active_months]

        # Chart 5: Budget Overview
        budget_labels = ['Venue', 'Catering', 'Marketing', 'Equipment', 'Decoration', 'Staff', 'Transport', 'Other', 'Sponsorship']
        budget_data = [
            float(budgets.aggregate(Sum('venue_cost'))['venue_cost__sum'] or 0),
            float(budgets.aggregate(Sum('catering_cost'))['catering_cost__sum'] or 0),
            float(budgets.aggregate(Sum('marketing_cost'))['marketing_cost__sum'] or 0),
            float(budgets.aggregate(Sum('equipment_cost'))['equipment_cost__sum'] or 0),
            float(budgets.aggregate(Sum('decoration_cost'))['decoration_cost__sum'] or 0),
            float(budgets.aggregate(Sum('staff_cost'))['staff_cost__sum'] or 0),
            float(budgets.aggregate(Sum('transport_cost'))['transport_cost__sum'] or 0),
            float(budgets.aggregate(Sum('other_expenses'))['other_expenses__sum'] or 0),
            total_sponsorship_sum,
        ]

        context = {
            'total_events': total_events,
            'total_participants': total_participants,
            'upcoming_events': upcoming_events,
            'completed_events': completed_events,
            'total_categories': total_categories,
            'total_venues': total_venues,
            'total_vendors': total_vendors,
            'total_resources': total_resources,
            'total_members': total_members,
            'active_events_count': active_events_count,
            'budget_remaining': round(budget_remaining, 2),
            'recent_events': recent_events,
            'upcoming_event_list': upcoming_event_list,
            'recent_members': recent_members,
            'unread_notifications': unread_notifications,
            'cat_labels_json': json.dumps(cat_labels),
            'cat_data_json': json.dumps(cat_data),
            'status_labels_json': json.dumps(statuses),
            'status_data_json': json.dumps(status_counts),
            'dept_labels_json': json.dumps(dept_labels),
            'dept_data_json': json.dumps(dept_counts),
            'month_labels_json': json.dumps(active_months),
            'month_data_json': json.dumps(active_month_data),
            'budget_labels_json': json.dumps(budget_labels),
            'budget_data_json': json.dumps(budget_data),
        }
        return render(request, 'Dashboard.html', context)
    else:
        my_registrations = EventRegistration.objects.filter(user=request.user)
        total_registered = my_registrations.count()
        total_watchlist = EventWatch.objects.filter(user=request.user).count()
        completed_registered = my_registrations.filter(event__status='Completed').count()
        user_marks = UserMark.objects.filter(user=request.user)
        avg_mark = round(sum(m.mark for m in user_marks) / user_marks.count(), 1) if user_marks.exists() else 0
        my_upcoming = my_registrations.filter(event__status__in=['Active', 'Pending']).select_related('event')
        registered_event_ids = my_registrations.values_list('event_id', flat=True)
        recommended = Event.objects.filter(status='Active').exclude(id__in=registered_event_ids)[:4]
        context = {
            'total_registered': total_registered,
            'total_watchlist': total_watchlist,
            'completed_registered': completed_registered,
            'avg_mark': avg_mark,
            'my_upcoming': my_upcoming,
            'recommended': recommended,
        }
        return render(request, 'user_dashboard.html', context)


# ─────────────────────────────────────────────
# EVENTS
# ─────────────────────────────────────────────
@login_required(login_url='login')
def event_list(request):
    events = Event.objects.select_related('category').all()

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')

    if q:
        events = events.filter(Q(title__icontains=q) | Q(venue__icontains=q) | Q(description__icontains=q))
    if status_filter:
        events = events.filter(status=status_filter)
    if category_filter:
        events = events.filter(category__id=category_filter)

    events = events.order_by('-start_date')

    paginator = Paginator(events, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    registered_event_ids = []
    watched_event_ids = []
    if not request.user.is_staff:
        registered_event_ids = list(EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True))
        watched_event_ids = list(EventWatch.objects.filter(user=request.user).values_list('event_id', flat=True))

    return render(request, 'event_list.html', {
        'events': page_obj,
        'page_obj': page_obj,
        'registered_event_ids': registered_event_ids,
        'watched_event_ids': watched_event_ids,
        'categories': Category.objects.all(),
        'q': q,
        'status_filter': status_filter,
        'category_filter': category_filter,
    })


@login_required(login_url='login')
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registrations = event.registrations.select_related('user').all()
    resources = event.resources.all()
    vendors = event.vendors.all()
    budget = Budget.objects.filter(event=event).first()
    is_registered = False
    user_ticket = None
    if not request.user.is_staff:
        reg = EventRegistration.objects.filter(event=event, user=request.user).first()
        if reg:
            is_registered = True
            user_ticket = Ticket.objects.filter(registration=reg).first()
    return render(request, 'event_detail.html', {
        'event': event,
        'registrations': registrations,
        'resources': resources,
        'vendors': vendors,
        'budget': budget,
        'is_registered': is_registered,
        'user_ticket': user_ticket,
    })


@login_required(login_url='login')
def create_event(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    categories = Category.objects.all()
    venues = Venue.objects.all()
    if request.method == 'POST':
        title = request.POST.get('event_name')
        category_id = request.POST.get('category')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        venue = request.POST.get('venue')
        description = request.POST.get('description')
        status = request.POST.get('status', 'Active')
        start_time = request.POST.get('start_time') or None
        end_time = request.POST.get('end_time') or None
        location = request.POST.get('location', '')
        speaker_name = request.POST.get('speaker_name', '')
        organizer = request.POST.get('organizer', '')
        max_participants = request.POST.get('max_participants', 15)
        registration_deadline = request.POST.get('registration_deadline') or None
        sponsors = request.POST.get('sponsors', '')
        venue_ref_id = request.POST.get('venue_ref') or None
        banner = request.FILES.get('banner')
        limit_participants = request.POST.get('limit_participants') == 'on'

        category = Category.objects.filter(id=category_id).first() if category_id and category_id.isdigit() else None
        venue_ref = Venue.objects.filter(id=venue_ref_id).first() if venue_ref_id else None

        if title and start_date and end_date and venue:
            event = Event.objects.create(
                title=title, category=category, start_date=start_date,
                end_date=end_date, start_time=start_time, end_time=end_time,
                venue=venue, location=location, description=description or '',
                speaker_name=speaker_name, organizer=organizer,
                max_participants=int(max_participants), registration_deadline=registration_deadline,
                sponsors=sponsors, status=status, venue_ref=venue_ref,
                limit_participants=limit_participants
            )
            if banner:
                event.banner = banner
                event.save()
            log_activity(request.user, 'event_create', f'Created event: {title}', request)
            notify(request.user, f"New event '{title}' has been created.", 'event', f'/event-detail/{event.id}/')
            messages.success(request, f"Event '{title}' created successfully!")
            return redirect('event_list')
    return render(request, 'create_event.html', {'categories': categories, 'venues': venues})


@login_required(login_url='login')
def edit_event(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    event = get_object_or_404(Event, id=event_id)
    categories = Category.objects.all()
    venues = Venue.objects.all()
    if request.method == 'POST':
        event.title = request.POST.get('event_name', event.title)
        category_id = request.POST.get('category')
        if category_id and category_id.isdigit():
            event.category = Category.objects.filter(id=category_id).first()
        venue_ref_id = request.POST.get('venue_ref')
        if venue_ref_id:
            event.venue_ref = Venue.objects.filter(id=venue_ref_id).first()
        event.start_date = request.POST.get('start_date', event.start_date)
        event.end_date = request.POST.get('end_date', event.end_date)
        event.start_time = request.POST.get('start_time') or event.start_time
        event.end_time = request.POST.get('end_time') or event.end_time
        event.venue = request.POST.get('venue', event.venue)
        event.location = request.POST.get('location', event.location)
        event.description = request.POST.get('description', event.description)
        event.speaker_name = request.POST.get('speaker_name', event.speaker_name)
        event.organizer = request.POST.get('organizer', event.organizer)
        event.sponsors = request.POST.get('sponsors', event.sponsors)
        max_p = request.POST.get('max_participants')
        if max_p:
            event.max_participants = int(max_p)
        deadline = request.POST.get('registration_deadline')
        if deadline:
            event.registration_deadline = deadline
        event.limit_participants = request.POST.get('limit_participants') == 'on'
        event.status = request.POST.get('status', event.status)
        if 'banner' in request.FILES:
            event.banner = request.FILES['banner']
        event.save()
        log_activity(request.user, 'event_update', f'Updated event: {event.title}', request)
        messages.success(request, f"Event '{event.title}' updated successfully!")
        return redirect('event_list')
    return render(request, 'edit_event.html', {'event': event, 'categories': categories, 'venues': venues})


@login_required(login_url='login')
def delete_event(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        title = event.title
        event.delete()
        log_activity(request.user, 'event_delete', f'Deleted event: {title}', request)
        messages.success(request, f"Event '{title}' deleted successfully!")
        return redirect('event_list')
    return render(request, 'delete_event.html', {'event': event})


@login_required(login_url='login')
def update_event_status(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.status = request.POST.get('status', event.status)
        event.save()
        messages.success(request, f"Event '{event.title}' status updated to {event.status}.")
        return redirect('event_list')
    return render(request, 'update_event_status.html', {'event': event})


@login_required(login_url='login')
def complete_event_list(request):
    events = Event.objects.filter(status='Completed')
    return render(request, 'complete_event_list.html', {'events': events})


@login_required(login_url='login')
def complete_event_user_list(request):
    if request.user.is_staff:
        completed_users = EventRegistration.objects.filter(event__status='Completed').select_related('event')
    else:
        completed_users = EventRegistration.objects.filter(user=request.user, event__status='Completed').select_related('event')
    return render(request, 'complete_event_user_list.html', {'completed_users': completed_users})


# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────
@login_required(login_url='login')
def event_category(request):
    categories = Category.objects.all()
    return render(request, 'event_category.html', {'categories': categories})


@login_required(login_url='login')
def create_event_category(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name:
            Category.objects.create(name=name, description=description)
            log_activity(request.user, 'category_create', f'Created category: {name}', request)
            messages.success(request, f"Category '{name}' created successfully!")
            return redirect('event_category')
    return render(request, 'create_event_category.html')


@login_required(login_url='login')
def edit_event_category(request, category_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name', category.name)
        category.description = request.POST.get('description', category.description)
        category.save()
        messages.success(request, f"Category '{category.name}' updated successfully!")
        return redirect('event_category')
    return render(request, 'edit_event_category.html', {'category': category})


@login_required(login_url='login')
def event_category_delete(request, category_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted successfully!")
        return redirect('event_category')
    return render(request, 'event_category_delete.html', {'category': category})


# ─────────────────────────────────────────────
# MEMBERS
# ─────────────────────────────────────────────
@login_required(login_url='login')
def add_event_member(request):
    events = Event.objects.all()
    initial_name = ""
    initial_email = ""
    initial_phone = ""
    if not request.user.is_staff:
        initial_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        initial_email = request.user.email
        if hasattr(request.user, 'profile'):
            initial_phone = request.user.profile.phone or ''

    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        country_code = request.POST.get('country_code', '')
        if phone:
            phone = phone.strip()
            if ' ' in phone:
                parts = phone.split()
                phone = parts[-1]
                if not country_code:
                    country_code = parts[0]
            elif phone.startswith('+') and len(phone) > 10:
                country_code = phone[:-10]
                phone = phone[-10:]
        event = Event.objects.filter(id=event_id).first()
        if event and full_name and email:
            clean_phone = ''.join(c for c in phone if c.isdigit()) if phone else ''
            clean_email = email.lower().strip() if email else ''
            user_to_link = User.objects.filter(email=clean_email).first()
            if len(clean_phone) != 10:
                messages.error(request, "Registration failed. Mobile number must contain exactly 10 digits.")
            elif not clean_email.endswith('@gmail.com'):
                messages.error(request, "Registration failed. Email must be a valid @gmail.com address.")
            elif EventRegistration.objects.filter(event=event, email=clean_email).exists():
                messages.warning(request, "This email is already registered for this event.")
            elif event.limit_participants and EventRegistration.objects.filter(event=event).count() >= event.max_participants:
                messages.error(request, f"Registration failed. '{event.title}' has reached its maximum capacity.")
            else:
                full_phone = f"{country_code} {clean_phone}".strip() if country_code else clean_phone
                reg = EventRegistration.objects.create(
                    user=user_to_link, event=event,
                    full_name=full_name, email=clean_email, phone=full_phone
                )
                _generate_ticket(reg)
                log_activity(request.user, 'member_add', f'Added {full_name} to {event.title}', request)
                notify(request.user, f"Member '{full_name}' added to '{event.title}'.", 'member', f'/event-detail/{event.id}/')
                messages.success(request, f"Member '{full_name}' added to '{event.title}'.")
            return redirect('joinevent_list')

    return render(request, 'add_event_member.html', {
        'events': events,
        'initial_name': initial_name,
        'initial_email': initial_email,
        'initial_phone': initial_phone
    })


@login_required(login_url='login')
def remove_event_member(request, member_id):
    if request.user.is_staff:
        member = get_object_or_404(EventRegistration, id=member_id)
    else:
        member = get_object_or_404(EventRegistration, id=member_id, user=request.user)
    if request.method == 'POST':
        name = member.full_name
        member.delete()
        messages.success(request, f"Registration for '{name}' removed successfully.")
        return redirect('joinevent_list')
    return render(request, 'remove_event_member.html', {'member': member})


@login_required(login_url='login')
def joinevent_list(request):
    members = EventRegistration.objects.select_related('event', 'user').all()
    q = request.GET.get('q', '').strip()
    event_filter = request.GET.get('event', '')
    status_filter = request.GET.get('status', '')

    if q:
        members = members.filter(Q(full_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
    if event_filter:
        members = members.filter(event__id=event_filter)

    members = members.order_by('-registration_date')
    paginator = Paginator(members, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'joinevent_list.html', {
        'joined_members': page_obj,
        'page_obj': page_obj,
        'events': Event.objects.all(),
        'q': q,
        'event_filter': event_filter,
    })


@login_required(login_url='login')
def absense_user_list(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    registered_user_ids = EventRegistration.objects.exclude(user__isnull=True).values_list('user_id', flat=True)
    absent_users = User.objects.filter(is_staff=False).exclude(id__in=registered_user_ids)
    return render(request, 'absense_user_list.html', {'absent_users': absent_users})


# ─────────────────────────────────────────────
# WATCHLIST
# ─────────────────────────────────────────────
@login_required(login_url='login')
def add_event_user_watch(request):
    events = Event.objects.all()
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        watch, created = EventWatch.objects.get_or_create(user=request.user, event=event)
        if created:
            messages.success(request, f"'{event.title}' added to watchlist!")
        else:
            messages.info(request, f"'{event.title}' is already in your watchlist.")
        return redirect('event_user_watch_list')
    return render(request, 'add_event_user_watch.html', {'events': events})


@login_required(login_url='login')
def add_watchlist_direct(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    watch, created = EventWatch.objects.get_or_create(user=request.user, event=event)
    if created:
        messages.success(request, f"'{event.title}' added to watchlist!")
    else:
        messages.info(request, f"'{event.title}' is already in your watchlist.")
    return redirect('event_user_watch_list')


@login_required(login_url='login')
def remove_event_user_watch(request, watch_id):
    if request.user.is_staff:
        watch = get_object_or_404(EventWatch, id=watch_id)
    else:
        watch = get_object_or_404(EventWatch, id=watch_id, user=request.user)
    if request.method == 'POST':
        watch.delete()
        messages.success(request, "Watchlist item removed successfully!")
        return redirect('event_user_watch_list')
    return render(request, 'remove_event_user_watch.html', {'watch_id': watch_id})


@login_required(login_url='login')
def event_user_watch_list(request):
    if request.user.is_staff:
        watch_list = EventWatch.objects.select_related('user', 'event').all()
    else:
        watch_list = EventWatch.objects.filter(user=request.user).select_related('event')
    return render(request, 'event_user_watch_list.html', {'watch_list': watch_list})


# ─────────────────────────────────────────────
# MARKS
# ─────────────────────────────────────────────
@login_required(login_url='login')
def create_user_mark(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    events = Event.objects.all()
    users = User.objects.filter(is_staff=False)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        event_id = request.POST.get('event_id')
        mark_val = request.POST.get('mark')
        remarks = request.POST.get('remarks', '')
        user = get_object_or_404(User, id=user_id)
        event = get_object_or_404(Event, id=event_id)
        UserMark.objects.create(user=user, event=event, mark=mark_val, remarks=remarks)
        messages.success(request, f"User mark saved for {user.username}!")
        return redirect('user_mark_list')
    return render(request, 'create_user_mark.html', {'events': events, 'users': users})


@login_required(login_url='login')
def user_mark_list(request):
    if request.user.is_staff:
        mark_list = UserMark.objects.select_related('user', 'event').all()
    else:
        mark_list = UserMark.objects.filter(user=request.user).select_related('event')
    return render(request, 'user_mark_list.html', {'mark_list': mark_list})


# ─────────────────────────────────────────────
# VENUE MANAGEMENT (MODULE 3)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def venue_list(request):
    venues = Venue.objects.all()
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    if q:
        venues = venues.filter(Q(name__icontains=q) | Q(location__icontains=q) | Q(contact_person__icontains=q))
    if status_filter:
        venues = venues.filter(status=status_filter)
    venues = venues.order_by('-created_at')
    paginator = Paginator(venues, 9)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'venue_list.html', {'venues': page_obj, 'page_obj': page_obj, 'q': q, 'status_filter': status_filter})


@login_required(login_url='login')
def venue_add(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('venue_list')
    form = VenueForm()
    if request.method == 'POST':
        form = VenueForm(request.POST, request.FILES)
        if form.is_valid():
            venue = form.save()
            messages.success(request, f"Venue '{venue.name}' added successfully!")
            return redirect('venue_list')
    return render(request, 'venue_form.html', {'form': form, 'title': 'Add Venue'})


@login_required(login_url='login')
def venue_edit(request, venue_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('venue_list')
    venue = get_object_or_404(Venue, id=venue_id)
    form = VenueForm(instance=venue)
    if request.method == 'POST':
        form = VenueForm(request.POST, request.FILES, instance=venue)
        if form.is_valid():
            form.save()
            messages.success(request, f"Venue '{venue.name}' updated successfully!")
            return redirect('venue_list')
    return render(request, 'venue_form.html', {'form': form, 'title': 'Edit Venue', 'venue': venue})


@login_required(login_url='login')
def venue_delete(request, venue_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('venue_list')
    venue = get_object_or_404(Venue, id=venue_id)
    if request.method == 'POST':
        name = venue.name
        venue.delete()
        messages.success(request, f"Venue '{name}' deleted successfully!")
        return redirect('venue_list')
    return render(request, 'venue_confirm_delete.html', {'venue': venue})


@login_required(login_url='login')
def venue_detail(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)
    events = Event.objects.filter(venue_ref=venue)
    return render(request, 'venue_detail.html', {'venue': venue, 'events': events})


# ─────────────────────────────────────────────
# RESOURCE MANAGEMENT (MODULE 4)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def resource_list(request):
    resources = Resource.objects.select_related('assigned_event').all()
    q = request.GET.get('q', '').strip()
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    if q:
        resources = resources.filter(Q(name__icontains=q))
    if type_filter:
        resources = resources.filter(resource_type=type_filter)
    if status_filter:
        resources = resources.filter(status=status_filter)
    resources = resources.order_by('-created_at')
    paginator = Paginator(resources, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'resource_list.html', {
        'resources': page_obj, 'page_obj': page_obj,
        'q': q, 'type_filter': type_filter, 'status_filter': status_filter,
        'resource_types': Resource.RESOURCE_TYPES,
    })


@login_required(login_url='login')
def resource_add(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('resource_list')
    form = ResourceForm()
    if request.method == 'POST':
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save()
            messages.success(request, f"Resource '{resource.name}' added successfully!")
            return redirect('resource_list')
    return render(request, 'resource_form.html', {'form': form, 'title': 'Add Resource'})


@login_required(login_url='login')
def resource_edit(request, resource_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('resource_list')
    resource = get_object_or_404(Resource, id=resource_id)
    form = ResourceForm(instance=resource)
    if request.method == 'POST':
        form = ResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f"Resource '{resource.name}' updated!")
            return redirect('resource_list')
    return render(request, 'resource_form.html', {'form': form, 'title': 'Edit Resource', 'resource': resource})


@login_required(login_url='login')
def resource_delete(request, resource_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('resource_list')
    resource = get_object_or_404(Resource, id=resource_id)
    if request.method == 'POST':
        name = resource.name
        resource.delete()
        messages.success(request, f"Resource '{name}' deleted!")
        return redirect('resource_list')
    return render(request, 'resource_confirm_delete.html', {'resource': resource})


# ─────────────────────────────────────────────
# VENDOR MANAGEMENT (MODULE 5)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def vendor_list(request):
    vendors = Vendor.objects.select_related('assigned_event').all()
    q = request.GET.get('q', '').strip()
    contract_filter = request.GET.get('contract', '')
    payment_filter = request.GET.get('payment', '')
    if q:
        vendors = vendors.filter(Q(name__icontains=q) | Q(company_name__icontains=q) | Q(service_type__icontains=q))
    if contract_filter:
        vendors = vendors.filter(contract_status=contract_filter)
    if payment_filter:
        vendors = vendors.filter(payment_status=payment_filter)
    vendors = vendors.order_by('-created_at')
    paginator = Paginator(vendors, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'vendor_list.html', {
        'vendors': page_obj, 'page_obj': page_obj,
        'q': q, 'contract_filter': contract_filter, 'payment_filter': payment_filter,
    })


@login_required(login_url='login')
def vendor_add(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('vendor_list')
    form = VendorForm()
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save()
            messages.success(request, f"Vendor '{vendor.name}' added successfully!")
            return redirect('vendor_list')
    return render(request, 'vendor_form.html', {'form': form, 'title': 'Add Vendor'})


@login_required(login_url='login')
def vendor_edit(request, vendor_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('vendor_list')
    vendor = get_object_or_404(Vendor, id=vendor_id)
    form = VendorForm(instance=vendor)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vendor '{vendor.name}' updated!")
            return redirect('vendor_list')
    return render(request, 'vendor_form.html', {'form': form, 'title': 'Edit Vendor', 'vendor': vendor})


@login_required(login_url='login')
def vendor_delete(request, vendor_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('vendor_list')
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        name = vendor.name
        vendor.delete()
        messages.success(request, f"Vendor '{name}' deleted!")
        return redirect('vendor_list')
    return render(request, 'vendor_confirm_delete.html', {'vendor': vendor})


@login_required(login_url='login')
def vendor_detail(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    return render(request, 'vendor_detail.html', {'vendor': vendor})


# ─────────────────────────────────────────────
# BUDGET MANAGEMENT (MODULE 6)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def budget_list(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    budgets = Budget.objects.select_related('event').all().order_by('-created_at')
    total_budget = sum(float(b.total_budget) for b in budgets)
    total_sponsorship = sum(float(b.sponsorship_amount) for b in budgets)
    total_expenses = sum(float(b.total_expenses) for b in budgets)
    total_remaining = total_budget + total_sponsorship - total_expenses

    # Chart data
    budget_labels = ['Venue', 'Catering', 'Marketing', 'Equipment', 'Decoration', 'Staff', 'Transport', 'Other', 'Sponsorship']
    budget_data = [
        float(Budget.objects.aggregate(Sum('venue_cost'))['venue_cost__sum'] or 0),
        float(Budget.objects.aggregate(Sum('catering_cost'))['catering_cost__sum'] or 0),
        float(Budget.objects.aggregate(Sum('marketing_cost'))['marketing_cost__sum'] or 0),
        float(Budget.objects.aggregate(Sum('equipment_cost'))['equipment_cost__sum'] or 0),
        float(Budget.objects.aggregate(Sum('decoration_cost'))['decoration_cost__sum'] or 0),
        float(Budget.objects.aggregate(Sum('staff_cost'))['staff_cost__sum'] or 0),
        float(Budget.objects.aggregate(Sum('transport_cost'))['transport_cost__sum'] or 0),
        float(Budget.objects.aggregate(Sum('other_expenses'))['other_expenses__sum'] or 0),
        total_sponsorship,
    ]

    return render(request, 'budget_list.html', {
        'budgets': budgets,
        'total_budget': total_budget,
        'total_sponsorship': total_sponsorship,
        'total_expenses': total_expenses,
        'total_remaining': total_remaining,
        'budget_labels_json': json.dumps(budget_labels),
        'budget_data_json': json.dumps(budget_data),
    })


@login_required(login_url='login')
def budget_add(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('budget_list')
    form = BudgetForm()
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save()
            messages.success(request, f"Budget for '{budget.event.title}' saved!")
            return redirect('budget_list')
    return render(request, 'budget_form.html', {'form': form, 'title': 'Add Budget'})


@login_required(login_url='login')
def budget_edit(request, budget_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('budget_list')
    budget = get_object_or_404(Budget, id=budget_id)
    form = BudgetForm(instance=budget)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, f"Budget for '{budget.event.title}' updated!")
            return redirect('budget_list')
    return render(request, 'budget_form.html', {'form': form, 'title': 'Edit Budget', 'budget': budget})


@login_required(login_url='login')
def budget_delete(request, budget_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('budget_list')
    budget = get_object_or_404(Budget, id=budget_id)
    if request.method == 'POST':
        event_title = budget.event.title
        budget.delete()
        messages.success(request, f"Budget for '{event_title}' deleted!")
        return redirect('budget_list')
    return render(request, 'budget_confirm_delete.html', {'budget': budget})


# ─────────────────────────────────────────────
# TICKETS & QR (MODULE 8, 9)
# ─────────────────────────────────────────────
def _generate_ticket(registration):
    """Internal helper to create a Ticket record with a unique ticket number."""
    if not Ticket.objects.filter(registration=registration).exists():
        ticket_number = f"TKT-{registration.event.id:04d}-{registration.id:06d}"
        ticket = Ticket.objects.create(registration=registration, ticket_number=ticket_number)
        # Generate QR code
        try:
            import qrcode
            import io
            from django.core.files.base import ContentFile
            qr_data = f"TICKET:{ticket_number}|EVENT:{registration.event.title}|MEMBER:{registration.full_name}|EMAIL:{registration.email}"
            qr = qrcode.make(qr_data)
            buffer = io.BytesIO()
            qr.save(buffer, format='PNG')
            ticket.qr_code.save(f"{ticket_number}.png", ContentFile(buffer.getvalue()), save=True)
        except ImportError:
            pass  # qrcode not installed; ticket saved without QR image


@login_required(login_url='login')
def view_ticket(request, registration_id):
    if request.user.is_staff:
        reg = get_object_or_404(EventRegistration, id=registration_id)
    else:
        reg = get_object_or_404(EventRegistration, id=registration_id, user=request.user)
    ticket = Ticket.objects.filter(registration=reg).first()
    if not ticket:
        _generate_ticket(reg)
        ticket = Ticket.objects.filter(registration=reg).first()
    return render(request, 'ticket.html', {'ticket': ticket, 'registration': reg})


@login_required(login_url='login')
def generate_ticket_for_member(request, registration_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('joinevent_list')
    reg = get_object_or_404(EventRegistration, id=registration_id)
    _generate_ticket(reg)
    log_activity(request.user, 'ticket_generate', f'Generated ticket for {reg.full_name}', request)
    messages.success(request, f"Ticket generated for '{reg.full_name}'!")
    return redirect('view_ticket', registration_id=registration_id)


# ─────────────────────────────────────────────
# ATTENDANCE (MODULE 8)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def attendance_list(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    event_id = request.GET.get('event', '')
    attendances = AttendanceRecord.objects.select_related('registration__event', 'registration__user').all()
    if event_id:
        attendances = attendances.filter(registration__event__id=event_id)
    attendances = attendances.order_by('-created_at')
    return render(request, 'attendance_list.html', {
        'attendances': attendances,
        'events': Event.objects.all(),
        'event_filter': event_id,
    })


@login_required(login_url='login')
def mark_attendance(request, registration_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    reg = get_object_or_404(EventRegistration, id=registration_id)
    attendance, created = AttendanceRecord.objects.get_or_create(registration=reg, defaults={'marked_by': request.user})
    if request.method == 'POST':
        status = request.POST.get('status', 'Present')
        attendance.status = status
        attendance.marked_by = request.user
        if status == 'Present' and not attendance.check_in_time:
            attendance.check_in_time = timezone.now()
        attendance.save()
        log_activity(request.user, 'attendance_mark', f'Marked {reg.full_name} as {status}', request)
        messages.success(request, f"Attendance for '{reg.full_name}' marked as {status}.")
        return redirect('attendance_list')
    return render(request, 'mark_attendance.html', {'reg': reg, 'attendance': attendance})


# ─────────────────────────────────────────────
# CALENDAR (MODULE 10)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def calendar_view(request):
    events = Event.objects.all()
    event_data = []
    status_colors = {
        'Active': '#10b981',
        'Completed': '#3b82f6',
        'Pending': '#f59e0b',
        'Cancelled': '#ef4444',
    }
    for ev in events:
        event_data.append({
            'id': ev.id,
            'title': ev.title,
            'start': ev.start_date.isoformat(),
            'end': ev.end_date.isoformat(),
            'color': status_colors.get(ev.status, '#6366f1'),
            'url': f'/event-detail/{ev.id}/',
            'extendedProps': {'status': ev.status, 'venue': ev.venue},
        })
    return render(request, 'calendar.html', {'events_json': json.dumps(event_data)})


# ─────────────────────────────────────────────
# NOTIFICATIONS (MODULE 11)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def notification_list(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifs.filter(is_read=False).count()
    paginator = Paginator(notifs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'notifications.html', {'notifications': page_obj, 'page_obj': page_obj, 'unread_count': unread_count})


@login_required(login_url='login')
def notification_mark_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notification_list')


@login_required(login_url='login')
def notification_delete(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.delete()
    messages.success(request, "Notification deleted.")
    return redirect('notification_list')


@login_required(login_url='login')
def notification_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notification_list')


@login_required(login_url='login')
def notification_clear_all(request):
    Notification.objects.filter(user=request.user).delete()
    messages.success(request, "All notifications cleared.")
    return redirect('notification_list')


# ─────────────────────────────────────────────
# REPORTS (MODULE 12)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def reports_view(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    report_type = request.GET.get('type', 'events')
    event_filter = request.GET.get('event', '')
    status_filter = request.GET.get('status', '')

    events = Event.objects.select_related('category').all()
    members = EventRegistration.objects.select_related('event', 'user').all()
    attendances = AttendanceRecord.objects.select_related('registration__event').all()

    if status_filter:
        events = events.filter(status=status_filter)
    if event_filter:
        members = members.filter(event__id=event_filter)
        attendances = attendances.filter(registration__event__id=event_filter)

    context = {
        'report_type': report_type,
        'events': events.order_by('-start_date'),
        'members': members.order_by('-registration_date'),
        'attendances': attendances,
        'all_events': Event.objects.all(),
        'status_filter': status_filter,
        'event_filter': event_filter,
        'total_events': events.count(),
        'total_members': members.count(),
        'present_count': attendances.filter(status='Present').count(),
        'absent_count': attendances.filter(status='Absent').count(),
    }
    return render(request, 'reports.html', context)


@login_required(login_url='login')
def export_csv(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
    report_type = request.GET.get('type', 'events')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    writer = csv.writer(response)

    if report_type == 'events':
        writer.writerow(['ID', 'Title', 'Category', 'Status', 'Start Date', 'End Date', 'Venue', 'Participants'])
        for ev in Event.objects.select_related('category').all():
            writer.writerow([ev.id, ev.title, ev.category.name if ev.category else '', ev.status,
                             ev.start_date, ev.end_date, ev.venue, ev.registrations.count()])
    elif report_type == 'members':
        writer.writerow(['ID', 'Full Name', 'Email', 'Phone', 'Event', 'Registration Date'])
        for reg in EventRegistration.objects.select_related('event').all():
            writer.writerow([reg.id, reg.full_name, reg.email, reg.phone,
                             reg.event.title, reg.registration_date.strftime('%d/%m/%Y %H:%M')])
    elif report_type == 'attendance':
        writer.writerow(['Member', 'Event', 'Status', 'Check-in Time'])
        for att in AttendanceRecord.objects.select_related('registration__event').all():
            writer.writerow([att.registration.full_name, att.registration.event.title,
                             att.status, att.check_in_time or 'N/A'])

    log_activity(request.user, 'report_generate', f'Exported {report_type} CSV report', request)
    return response


# ─────────────────────────────────────────────
# ANALYTICS (MODULE 13)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def analytics_view(request):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    # Events by month
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_counts = [0] * 12
    for ev in Event.objects.all():
        monthly_counts[ev.start_date.month - 1] += 1

    # Events by category
    categories = Category.objects.annotate(count=Count('events'))
    cat_labels = [c.name for c in categories]
    cat_data = [c.count for c in categories]

    # Attendance rate
    total_att = AttendanceRecord.objects.count()
    present_att = AttendanceRecord.objects.filter(status='Present').count()
    attendance_rate = round((present_att / total_att * 100) if total_att > 0 else 0, 1)

    # Members by department
    dept_map = {}
    for p in UserProfile.objects.all():
        dept = p.department or 'IT'
        dept_map[dept] = dept_map.get(dept, 0) + 1
    dept_labels = list(dept_map.keys()) or ['IT']
    dept_data = list(dept_map.values()) or [0]

    # Venue usage
    venue_usage = Event.objects.values('venue').annotate(count=Count('id')).order_by('-count')[:10]
    venue_labels = [v['venue'] for v in venue_usage]
    venue_data = [v['count'] for v in venue_usage]

    # Budget overview
    budgets = Budget.objects.all()
    total_b = sum(float(b.total_budget) for b in budgets)
    total_sp = sum(float(b.sponsorship_amount) for b in budgets)
    total_e = sum(float(b.total_expenses) for b in budgets)
    budget_remaining = total_b + total_sp - total_e

    context = {
        'month_labels_json': json.dumps(month_names),
        'month_data_json': json.dumps(monthly_counts),
        'cat_labels_json': json.dumps(cat_labels),
        'cat_data_json': json.dumps(cat_data),
        'dept_labels_json': json.dumps(dept_labels),
        'dept_data_json': json.dumps(dept_data),
        'venue_labels_json': json.dumps(venue_labels),
        'venue_data_json': json.dumps(venue_data),
        'attendance_rate': attendance_rate,
        'total_events': Event.objects.count(),
        'total_members': EventRegistration.objects.count(),
        'total_venues': Venue.objects.count(),
        'total_budget': total_b,
        'total_expenses': total_e,
        'budget_remaining': budget_remaining,
    }
    return render(request, 'analytics.html', context)


# ─────────────────────────────────────────────
# PROFILE (MODULE 15-23)
# ─────────────────────────────────────────────
@login_required(login_url='login')
def profile_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    user_form = UserUpdateForm(instance=user)
    profile_form = UserProfileUpdateForm(instance=profile)
    password_form = PasswordChangeForm(user)
    username_form = UsernameChangeForm(instance=user)
    active_tab = request.GET.get('tab', 'account')

    user_ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_personal' or action == 'update_account':
            active_tab = 'account'
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile)
            new_username = request.POST.get('username')
            if new_username and new_username != user.username:
                if User.objects.filter(username__iexact=new_username).exclude(pk=user.pk).exists():
                    messages.error(request, "This username is already taken.")
                else:
                    user.username = new_username
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                log_activity(user, 'profile_update', 'Updated account details', request)
                messages.success(request, "Account details updated successfully!")
                return redirect('/profile/?tab=account')
            else:
                messages.error(request, "Please correct the errors in the Account Settings section.")

        elif action == 'change_password':
            active_tab = 'security'
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                log_activity(user, 'password_change', 'Password updated successfully', request)
                messages.success(request, "Your password has been updated successfully!")
                return redirect('/profile/?tab=security')
            else:
                messages.error(request, "Please satisfy all password requirements.")

        elif action == 'update_notifications':
            active_tab = 'notifications'
            profile.event_updates = request.POST.get('event_updates') == 'on'
            profile.new_member_notifications = request.POST.get('new_member_notifications') == 'on'
            profile.report_notifications = request.POST.get('report_notifications') == 'on'
            profile.contact_messages = request.POST.get('contact_messages') == 'on'
            profile.email_notifications = request.POST.get('email_notifications') == 'on'
            profile.save()
            messages.success(request, "Notification settings updated!")
            return redirect('/profile/?tab=notifications')

        elif action == 'update_appearance':
            active_tab = 'appearance'
            theme_preference = request.POST.get('theme_preference', 'slate')
            profile.theme_preference = theme_preference
            profile.save()
            messages.success(request, "Appearance theme updated!")
            return redirect('/profile/?tab=appearance')

        elif action == 'update_privacy':
            active_tab = 'privacy'
            profile.show_email = request.POST.get('show_email') == 'on'
            profile.show_phone = request.POST.get('show_phone') == 'on'
            profile.profile_visibility = request.POST.get('profile_visibility', 'Public')
            profile.allow_contact_requests = request.POST.get('allow_contact_requests') == 'on'
            profile.save()
            messages.success(request, "Privacy settings updated!")
            return redirect('/profile/?tab=privacy')

        elif action == 'update_preferences':
            active_tab = 'preferences'
            profile.language = request.POST.get('language', 'en')
            profile.timezone = request.POST.get('timezone', 'Asia/Kolkata')
            profile.date_format = request.POST.get('date_format', 'DD/MM/YYYY')
            profile.time_format = request.POST.get('time_format', '12h')
            profile.dashboard_layout = request.POST.get('dashboard_layout', 'Grid')
            profile.save()
            messages.success(request, "Preferences updated!")
            return redirect('/profile/?tab=preferences')

        elif action == 'update_security_notifications':
            active_tab = 'security'
            profile.email_login_alerts = request.POST.get('email_login_alerts') == 'on'
            profile.password_change_alerts = request.POST.get('password_change_alerts') == 'on'
            profile.security_notifications = request.POST.get('security_notifications') == 'on'
            profile.save()
            messages.success(request, "Security notifications updated!")
            return redirect('/profile/?tab=security')

        elif action == 'change_username':
            active_tab = 'account'
            username_form = UsernameChangeForm(request.POST, instance=user)
            if username_form.is_valid():
                username_form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Username changed successfully!")
                return redirect('/profile/?tab=account')
            else:
                messages.error(request, "Please correct the username error.")

        elif action == 'change_email':
            active_tab = 'account'
            new_email = request.POST.get('email', '').lower().strip()
            if not new_email:
                messages.error(request, "Email address cannot be empty.")
            elif not new_email.endswith('@gmail.com'):
                messages.error(request, "Email must be a valid @gmail.com address.")
            else:
                user.email = new_email
                user.save()
                messages.success(request, "Email address updated!")
                return redirect('/profile/?tab=account')

        elif action == 'change_profile_picture':
            active_tab = 'account'
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
                profile.save()
                messages.success(request, "Profile picture updated!")
                return redirect('/profile/?tab=account')
            else:
                messages.error(request, "Please select a photo to upload.")

        elif action == 'reset_settings':
            active_tab = 'danger'
            profile.theme_preference = 'slate'
            profile.language = 'en'
            profile.timezone = 'Asia/Kolkata'
            profile.date_format = 'DD/MM/YYYY'
            profile.time_format = '12h'
            profile.dashboard_layout = 'Grid'
            profile.show_email = True
            profile.show_phone = False
            profile.profile_visibility = 'Public'
            profile.allow_contact_requests = True
            profile.event_updates = True
            profile.new_member_notifications = True
            profile.report_notifications = True
            profile.contact_messages = True
            profile.email_notifications = True
            profile.email_login_alerts = True
            profile.password_change_alerts = True
            profile.security_notifications = True
            profile.save()
            messages.info(request, "All settings have been reset to default values.")
            return redirect('/profile/?tab=danger')

        elif action == 'delete_account':
            if not user.is_staff:
                messages.error(request, "Permission denied. Only Administrators can delete accounts.")
                return redirect('/profile/?tab=danger')
            else:
                auth_logout(request)
                user.delete()
                messages.success(request, "Account deleted successfully.")
                return redirect('index')

    # Real activity logs from DB, fall back to static samples
    real_logs = ActivityLog.objects.filter(user=user).order_by('-created_at')[:10]
    if real_logs.exists():
        activity_logs = [
            {
                'date': log.created_at.strftime('%d %b %Y, %I:%M %p'),
                'action': log.get_action_display(),
                'icon': 'fa-history',
                'badge': log.action.replace('_', ' ').title(),
                'desc': log.description,
            }
            for log in real_logs
        ]
    else:
        activity_logs = [
            {'date': '31 Jul 2026, 8:15 PM', 'action': 'Password Changed', 'icon': 'fa-key', 'badge': 'Security', 'desc': 'Account password was updated.'},
            {'date': '30 Jul 2026, 4:30 PM', 'action': 'Profile Updated', 'icon': 'fa-user-edit', 'badge': 'Profile', 'desc': 'Personal information updated.'},
            {'date': '29 Jul 2026, 10:12 AM', 'action': 'Logged In', 'icon': 'fa-sign-in-alt', 'badge': 'Login', 'desc': f'Logged in from {user_ip}.'},
        ]

    return render(request, 'profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'username_form': username_form,
        'profile': profile,
        'active_tab': active_tab,
        'user_ip': user_ip,
        'user_agent': user_agent,
        'activity_logs': activity_logs,
    })
