from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('gallery/', views.gallery, name='gallery'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Events
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('event-list/', views.event_list, name='event_list'),
    path('event-detail/<int:event_id>/', views.event_detail, name='event_detail'),
    path('update-event-status/<int:event_id>/', views.update_event_status, name='update_event_status'),
    path('complete-event-list/', views.complete_event_list, name='complete_event_list'),
    path('complete-event-user-list/', views.complete_event_user_list, name='complete_event_user_list'),

    # Categories
    path('create-event-category/', views.create_event_category, name='create_event_category'),
    path('edit-event-category/<int:category_id>/', views.edit_event_category, name='edit_event_category'),
    path('event-category/', views.event_category, name='event_category'),
    path('event-category-delete/<int:category_id>/', views.event_category_delete, name='event_category_delete'),

    # Members
    path('add-event-member/', views.add_event_member, name='add_event_member'),
    path('remove-event-member/<int:member_id>/', views.remove_event_member, name='remove_event_member'),
    path('joinevent-list/', views.joinevent_list, name='joinevent_list'),
    path('absense-user-list/', views.absense_user_list, name='absense_user_list'),

    # Watchlist
    path('add-event-user-watch/', views.add_event_user_watch, name='add_event_user_watch'),
    path('add-watchlist-direct/<int:event_id>/', views.add_watchlist_direct, name='add_watchlist_direct'),
    path('remove-event-user-watch/<int:watch_id>/', views.remove_event_user_watch, name='remove_event_user_watch'),
    path('event-user-watch-list/', views.event_user_watch_list, name='event_user_watch_list'),

    # Marks
    path('create-user-mark/', views.create_user_mark, name='create_user_mark'),
    path('user-mark-list/', views.user_mark_list, name='user_mark_list'),

    # Venue Management (Module 3)
    path('venues/', views.venue_list, name='venue_list'),
    path('venues/add/', views.venue_add, name='venue_add'),
    path('venues/<int:venue_id>/edit/', views.venue_edit, name='venue_edit'),
    path('venues/<int:venue_id>/delete/', views.venue_delete, name='venue_delete'),
    path('venues/<int:venue_id>/', views.venue_detail, name='venue_detail'),

    # Resource Management (Module 4)
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/add/', views.resource_add, name='resource_add'),
    path('resources/<int:resource_id>/edit/', views.resource_edit, name='resource_edit'),
    path('resources/<int:resource_id>/delete/', views.resource_delete, name='resource_delete'),

    # Vendor Management (Module 5)
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/add/', views.vendor_add, name='vendor_add'),
    path('vendors/<int:vendor_id>/edit/', views.vendor_edit, name='vendor_edit'),
    path('vendors/<int:vendor_id>/delete/', views.vendor_delete, name='vendor_delete'),
    path('vendors/<int:vendor_id>/', views.vendor_detail, name='vendor_detail'),

    # Budget Management (Module 6)
    path('budget/', views.budget_list, name='budget_list'),
    path('budget/add/', views.budget_add, name='budget_add'),
    path('budget/<int:budget_id>/edit/', views.budget_edit, name='budget_edit'),
    path('budget/<int:budget_id>/delete/', views.budget_delete, name='budget_delete'),

    # Tickets (Module 9)
    path('ticket/<int:registration_id>/', views.view_ticket, name='view_ticket'),
    path('ticket/generate/<int:registration_id>/', views.generate_ticket_for_member, name='generate_ticket'),

    # Attendance (Module 8)
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/<int:registration_id>/mark/', views.mark_attendance, name='mark_attendance'),

    # Calendar (Module 10)
    path('calendar/', views.calendar_view, name='calendar'),

    # Notifications (Module 11)
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notif_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:notif_id>/delete/', views.notification_delete, name='notification_delete'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/clear/', views.notification_clear_all, name='notification_clear_all'),

    # Reports (Module 12)
    path('reports/', views.reports_view, name='reports'),
    path('reports/export-csv/', views.export_csv, name='export_csv'),

    # Analytics (Module 13)
    path('analytics/', views.analytics_view, name='analytics'),

    # Profile (Module 15+)
    path('profile/', views.profile_view, name='profile'),
]
