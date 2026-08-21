# 🎫 EventSphere — Event Registration & Management Platform

EventSphere is a centralized web-based **Event Registration and Management Platform** designed to digitize and streamline the complete event lifecycle.

The platform provides separate experiences for **Administrators/Organizers** and **Participants/Students**, allowing events to be created, scheduled, managed, registered, and monitored through a single system.

---

## 🚀 Project Overview

EventSphere provides an integrated platform for managing the complete event lifecycle, starting from event creation and scheduling to participant registration, digital ticket generation, QR-based check-in, resource allocation, vendor management, budget tracking, reporting, and AI-powered assistance.

### 👨‍💼 Organizer / Administrator

Administrators can manage:

- Event & Schedule Management
- Event Categories
- Participant / Member Management
- Venue Management
- Resource Allocation
- Sponsor Management
- Vendor Management
- Contract Management
- Budget & Expense Management
- QR Check-in
- Reports & Analytics
- Profile & Security
- AI-powered administrative insights

### 👨‍🎓 Participant / Student

Participants can:

- Discover available events
- Filter events
- Register for events
- View registered events
- Generate digital tickets
- Download PDF tickets
- Use QR-based check-in
- Manage their profile
- Use the AI Assistant

---

# 🎯 Objectives

The main objectives of EventOS are:

- Digitize the complete event management process
- Reduce manual event administration
- Simplify participant registration
- Automate ticket generation
- Provide QR-based event check-in
- Manage venues and resources efficiently
- Manage vendors and sponsors
- Track event budgets and expenses
- Provide reports and analytics
- Improve security and role-based access
- Provide AI-powered assistance and insights

---

# 🛠️ Technology Stack

## Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap 5

## Backend

- Python
- Django 6.0.7
- Django REST Framework

## Database

- SQLite
- Django ORM

## AI Integration

- Google Gemini API
- Hybrid AI architecture
- Fallback-based AI handling

## Background Services

- Celery
- Redis

## Reporting & Data

- ReportLab
- OpenPyXL
- CSV Export
- PDF Generation

## Development Tools

- Git
- GitHub
- Visual Studio Code

---

# 🏗️ System Architecture

EventOS follows a Django-based web application architecture.

```text
                    ┌─────────────────────────┐
                    │     User / Browser      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Django Views       │
                    │     & URL Routing       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Business Logic      │
                    │     Django Models       │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
        │   SQLite    │  │ REST APIs    │  │ AI Services │
        │  Database   │  │    / JSON    │  │   Gemini    │
        └─────────────┘  └──────────────┘  └─────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Reports / Tickets / QR  │
                    │ Notifications / Exports │
                    └─────────────────────────┘
```

---

# ⚙️ Getting Started — How to Run EventSphere

## 1. Prerequisites

Make sure you have the following installed before starting:

- Python 3.11+ (Django 6.0.7 requires a recent Python version)
- pip (Python package manager)
- Git
- Redis (required for Celery background tasks)
- A Google Gemini API key (for the AI Assistant features)

## 2. Clone the Repository

```bash
git clone https://github.com/<your-username>/eventSphere.git
cd eventos
```

## 3. Create and Activate a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file doesn't exist yet, install the core packages manually:

```bash
pip install django==6.0.7 djangorestframework celery redis reportlab openpyxl google-generativeai python-decouple
```

## 5. Configure Environment Variables

Create a `.env` file in the project root and add:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
GEMINI_API_KEY=your-google-gemini-api-key
REDIS_URL=redis://localhost:6379/0
```

## 6. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 7. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

## 8. Start Redis Server

Redis must be running for Celery-based background tasks (notifications, report generation, etc.):

```bash
# Windows (via WSL or Redis for Windows)
redis-server

# macOS / Linux
redis-server
```

## 9. Start the Celery Worker

In a **separate terminal**, with the virtual environment activated:

```bash
celery -A eventos worker --loglevel=info
```

## 10. Run the Django Development Server

In another terminal:

```bash
python manage.py runserver
```

The application will now be available at:

```
http://127.0.0.1:8000/
```

- Admin/Organizer panel: `http://127.0.0.1:8000/admin/`
- Participant portal: `http://127.0.0.1:8000/`

## 11. Collect Static Files (for production/deployment)

```bash
python manage.py collectstatic
```

---

### Quick Start Summary

| Step | Command |
|------|---------|
| Activate venv | `venv\Scripts\activate` (Windows) / `source venv/bin/activate` (Linux/Mac) |
| Install deps | `pip install -r requirements.txt` |
| Migrate DB | `python manage.py migrate` |
| Create admin | `python manage.py createsuperuser` |
| Start Redis | `redis-server` |
| Start Celery | `celery -A eventos worker --loglevel=info` |
| Run server | `python manage.py runserver` |
