# 🚢 HarborHop

A comprehensive harbor and port management system built with Django for efficient vessel tracking, booking management, and harbor operations.

[![Django](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-blue.svg)](https://supabase.com/)
[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-purple.svg)](https://render.com/)

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [System Requirements](#-system-requirements)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Database Setup](#-database-setup)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- 🔐 **User Authentication** - Secure login and user management
- 🚢 **Vessel Management** - Track and manage vessel information
- 📅 **Booking System** - Handle harbor bookings and reservations
- 📊 **Dashboard** - Real-time overview of harbor operations
- 🗄️ **Database Integration** - PostgreSQL with Supabase
- 🎨 **Responsive Design** - Mobile-friendly interface
- 🔒 **CSRF Protection** - Built-in security features

## 🛠️ Tech Stack

**Backend:**
- Django 5.2.6
- Python 3.13
- PostgreSQL (Supabase)

**Frontend:**
- HTML/CSS/JavaScript
- Django Templates

**Deployment:**
- Railway (Production)
- Gunicorn (WSGI Server)
- WhiteNoise (Static Files)

**Database:**
- PostgreSQL via Supabase
- SQLite (Local Development)

## 📦 System Requirements

Before you begin, ensure your system meets the following requirements:

- **Python 3.10 or newer** installed
- **pip** (Python package installer)
- **Virtual environment support** (venv)
- **Git** (optional, for cloning repository)
- **PostgreSQL** (via Supabase for production) or **SQLite** (for local development)

## 📁 Project Structure

Your project should be organized as follows:

```
HarborHop/
├── env/                    # Virtual environment
├── harbor_mgmt/           # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   ├── static/            # Static files (CSS, JS, images)
│   └── templates/         # HTML templates
├── HarborHop/             # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI configuration
├── templates/             # Global templates
├── staticfiles/           # Collected static files (production)
├── db.sqlite3             # SQLite database (local dev)
├── manage.py              # Django management script
├── .env                   # Environment variables (create this)
├── .gitignore             # Git ignore file
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/daas-me/HarborHop.git
cd HarborHop
```

Or download and extract the ZIP file, then navigate to the project folder:

```bash
cd C:\Users\YourUsername\Downloads\HarborHop
```

### Step 2: Create Virtual Environment

Create a virtual environment to isolate project dependencies:

```bash
python -m venv env
```

### Step 3: Activate Virtual Environment

**Windows (Command Prompt/PowerShell):**
```bash
env\Scripts\activate
```

**Mac / Linux:**
```bash
source env/bin/activate
```

You should see `(env)` prefix in your terminal, indicating the virtual environment is active.

### Step 4: Install Dependencies

Install all required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install django psycopg2-binary dj-database-url python-dotenv gunicorn whitenoise
```

### Step 5: Verify Installation

Check that Django is installed correctly:

```bash
python -m django --version
```

You should see version `5.2.6` or similar.

## 🗄️ Database Setup

### Option 1: Using Supabase PostgreSQL (Recommended for Production)

#### 1. Get Supabase Connection String

1. Log in to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **Database**
4. Scroll to **Connection String** section
5. Copy the **Session Pooler** connection string (for better performance)

The format should look like:
```
postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

#### 2. Create Environment File

In your project root directory (same level as `manage.py`), create a file named `.env`:

```bash
# Windows
type nul > .env

# Mac/Linux
touch .env
```

#### 3. Add Database URL

Open `.env` and paste your connection string:

```env
DATABASE_URL=postgresql://postgres.username:password@aws-0-region.pooler.supabase.com:6543/postgres
```

**Important Notes:**
- Replace `username`, `password`, and `region` with your actual Supabase credentials
- Make sure quotes are straight (not curly)
- Do NOT commit this file to Git (it's in `.gitignore`)

### Option 2: Using SQLite (Local Development)

If you don't have a Supabase account or want to test locally:

1. **Skip** creating the `.env` file
2. The application will automatically use SQLite (`db.sqlite3`)
3. Perfect for local testing and development

## ⚙️ Configuration

The `settings.py` is already configured to handle both PostgreSQL and SQLite:

```python
import os
import dj_database_url
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Production: Use PostgreSQL from Supabase/Railway
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Add SSL requirement for PostgreSQL
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require'
    }
else:
    # Local development: Use SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

This configuration automatically:
- Uses **PostgreSQL** when `DATABASE_URL` is present (production)
- Falls back to **SQLite** for local development
- Handles SSL requirements for Supabase

## 🏃 Running the Application

### Step 1: Apply Database Migrations

Create all necessary database tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Create Superuser (Optional)

Create an admin account to access the Django admin panel:

```bash
python manage.py createsuperuser
```

Follow the prompts:
- **Username:** Choose a username
- **Email:** Enter your email (optional)
- **Password:** Enter a secure password (you won't see it as you type)

### Step 3: Collect Static Files

Gather all static files for production:

```bash
python manage.py collectstatic --noinput
```

### Step 4: Start Development Server

Run the Django development server:

```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

### Step 5: Access the Application

Open your browser and visit:

- **Homepage:** http://127.0.0.1:8000/
- **Login Page:** http://127.0.0.1:8000/login/
- **Admin Panel:** http://127.0.0.1:8000/admin/

Use the superuser credentials you created to log in to the admin panel.

## 🚀 Deployment

### Deploying to Railway

#### 1. Prerequisites
- A [Railway](https://railway.app) account
- Your code pushed to GitHub

#### 2. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `HarborHop` repository

#### 3. Add PostgreSQL Database

1. In your Railway project, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway automatically creates a `DATABASE_URL` environment variable

#### 4. Configure Environment Variables

Go to your Django service → **"Variables"** tab and add:

```env
SECRET_KEY=your-production-secret-key-here
DEBUG=False
```

**Note:** If using Supabase instead of Railway's PostgreSQL:
1. Add your Supabase connection string as `DATABASE_URL`
2. This will override Railway's PostgreSQL

#### 5. Set Custom Start Command

Go to **"Settings"** → **"Deploy"** section and set:

```bash
python manage.py migrate --noinput && gunicorn HarborHop.wsgi:application
```

This ensures migrations run before the server starts.

#### 6. Deploy

Railway will automatically deploy your application. Your app will be available at:
```
https://your-app-name.up.railway.app
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution:**
```bash
pip install psycopg2-binary
```

Make sure you're using `psycopg2-binary` in `requirements.txt`, not `psycopg2`.

#### Issue: `no such table: auth_user`

**Solution:** Run migrations:
```bash
python manage.py migrate
```

#### Issue: Database Connection Error

**Solution:** Check your `.env` file:
- Ensure `DATABASE_URL` is correctly formatted
- Verify your Supabase password is correct
- Check that there are no extra spaces or quotes

#### Issue: Static Files Not Loading

**Solution:**
```bash
python manage.py collectstatic --noinput
```

#### Issue: `ImproperlyConfigured: Error loading psycopg2 module`

**Solution:** This happens on Railway. Use `psycopg2-binary` instead:
```
# requirements.txt
psycopg2-binary==2.9.11
```

#### Issue: Virtual Environment Not Activating

**Windows PowerShell Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

### Getting Help

If you encounter other issues:
1. Check the [Django documentation](https://docs.djangoproject.com/)
2. Review the [Supabase docs](https://supabase.com/docs)
3. Open an issue on [GitHub](https://github.com/daas-me/HarborHop/issues)

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b setup/harborhop/your-feature-name
   ```
3. **Make your changes**
4. **Commit using the standard format:**
   ```bash
   git commit -m "setup(harborhop): description of changes"
   ```
5. **Push to your fork:**
   ```bash
   git push origin setup/harborhop/your-feature-name
   ```
6. **Open a Pull Request**

### Commit Convention

Use this format for all commits:

```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- setup: Configuration changes
- docs: Documentation updates
- style: Code style changes
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance tasks

Examples:
✅ feat(booking): add vessel reservation system
✅ fix(auth): resolve login redirect issue
✅ setup(harborhop): configure database connection
✅ docs: update installation guide
```

### Branch Naming

Follow this pattern:
```
setup/harborhop/<feature-name>

Examples:
- setup/harborhop/fix-database-connection
- setup/harborhop/add-vessel-tracking
- setup/harborhop/update-authentication
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **daas-me** - [GitHub Profile](https://github.com/daas-me)

## 🙏 Acknowledgments

- Django Community
- Supabase Team
- Railway Platform
- All contributors who help improve this project

---

**Live Demo:** [https://harborhop-production.up.railway.app](https://harborhop-production.up.railway.app)

**Issues & Support:** [GitHub Issues](https://github.com/daas-me/HarborHop/issues)

**Documentation:** [Installation Guide PDF](docs/HarborHop_Installation_Guide_v2.pdf)

Made with ❤️ for efficient harbor management

