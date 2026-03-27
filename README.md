# 📰 Lorena's Gossip — News Application

A Django-based news application that allows readers to access articles
from independent journalists and publishers, with role-based access
control, a RESTful API with token authentication, newsletter
subscriptions, and automated email notifications.

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- MariaDB 12+
- pip

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/your-username/LorenaNewsApp.git
cd LorenaNewsApp
```

**2. Create and activate virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create `.env` file** in the root directory:
```
DB_ENGINE=django.db.backends.mysql
DB_NAME=lorena_news_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=your_db_port
SECRET_KEY=your-secret-key
DEBUG=True
```

**5. Create the database** in MariaDB:
```sql
CREATE DATABASE lorena_news_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

**6. Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

> User groups and permissions are created automatically during migration.
> No additional setup commands are required.

**7. Create a superuser** (for Django admin access)
```bash
python manage.py createsuperuser
```

**8. Start the server**
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

---

## 🐳 Running with Docker

### Prerequisites
- Docker installed on your machine

### Steps

**1. Create `.env` file** in the root directory (same as above):
```
DB_ENGINE=django.db.backends.mysql
DB_NAME=lorena_news_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port
SECRET_KEY=your-secret-key
DEBUG=True
```

> ⚠️ Never commit your `.env` file to the repository.
> Use `.env.example` as a reference for the required variables.

**2. Build the Docker image**
```bash
docker build -t lorenanewsapp .
```

**3. Run the container**
```bash
docker run -p 8000:8000 --env-file .env lorenanewsapp
```

The application will be available at `http://localhost:8000/`

---

## 👥 User Roles

| Role | Permissions |
|------|------------|
| **Reader** | View articles and newsletters, subscribe to journalists and publishers |
| **Journalist** | Create, view, update, delete articles and newsletters, join publisher teams |
| **Editor** | View, update, delete articles and newsletters, approve articles, join publisher teams |
| **Publisher** | Manage their team of journalists and editors, view all content |

> **Note:** Publisher is a user role, not a separate model.
> Publishers register at `/register/` and select the Publisher role.

> **Note:** Access control is enforced via custom role-based decorators
> that check the user's `role` field directly, ensuring permissions work
> correctly without any manual configuration.

---

## 🌐 Web Routes

### Authentication
| URL | Description | Access |
|-----|-------------|--------|
| `/register/` | Register a new account | Public |
| `/login/` | Login | Public |
| `/logout/` | Logout | Logged in |
| `/username-recovery/` | Recover username via email | Public |
| `/password-reset/` | Request password reset link | Public |
| `/password-change/` | Change password | Logged in |

### Publishers
| URL | Description | Access |
|-----|-------------|--------|
| `/publishers/` | List all publishers | All logged in |
| `/publishers/<id>/` | View publisher profile and team | All logged in |
| `/publishers/<id>/team/` | Manage publisher team | Publisher only |
| `/publishers/<id>/join/` | Join a publisher's team | Journalist, Editor |
| `/publishers/<id>/leave/` | Leave a publisher's team | Journalist, Editor |

### Articles
| URL | Description | Access |
|-----|-------------|--------|
| `/` | Home — list of approved articles | All logged in |
| `/articles/create/` | Write a new article | Journalist |
| `/articles/<id>/` | View article detail | All logged in |
| `/articles/<id>/edit/` | Edit an article | Editor, Journalist |
| `/articles/<id>/delete/` | Delete an article | Editor, Journalist |
| `/articles/pending/` | Review pending articles | Editor |
| `/articles/<id>/approve/` | Approve an article | Editor |

### Newsletters
| URL | Description | Access |
|-----|-------------|--------|
| `/newsletters/` | List all newsletters | All logged in |
| `/newsletters/create/` | Create a newsletter | Journalist |
| `/newsletters/<id>/` | View newsletter detail | All logged in |
| `/newsletters/<id>/edit/` | Edit a newsletter | Editor, Journalist |
| `/newsletters/<id>/delete/` | Delete a newsletter | Editor, Journalist |

---

## 🔌 REST API

### Authentication

All API endpoints require a token in the request header:
```
Authorization: Token <your_token>
```

#### Get a token
```
POST /api/login/
```
**Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```
**Response:**
```json
{
    "token": "abc123...",
    "user_id": 1,
    "username": "your_username",
    "role": "journalist"
}
```

#### Logout
```
POST /api/logout/
```

---

### Publisher Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/publishers/` | List all publishers | All |
| GET | `/api/publishers/<id>/` | Get publisher profile | All |
| GET | `/api/publishers/<id>/team/` | Get publisher's team | All |
| POST | `/api/publishers/<id>/team/` | Update publisher's team | Publisher only |
| POST | `/api/publishers/<id>/join/` | Join publisher's team | Journalist, Editor |
| POST | `/api/publishers/<id>/leave/` | Leave publisher's team | Journalist, Editor |

**Update team body (POST `/api/publishers/<id>/team/`):**
```json
{
    "journalist_ids": [1, 2],
    "editor_ids": [3]
}
```

---

### Article Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/articles/` | List all approved articles | All |
| POST | `/api/articles/` | Create a new article | Journalist |
| GET | `/api/articles/<id>/` | Get a single article | All |
| PUT | `/api/articles/<id>/` | Update an article | Editor, Journalist |
| DELETE | `/api/articles/<id>/` | Delete an article | Editor, Journalist |
| GET | `/api/articles/subscribed/` | Get subscribed articles | All |
| POST | `/api/articles/<id>/approve/` | Approve an article | Editor |
| POST | `/api/approved/` | Log approved article (signal) | Internal |

---

### Newsletter Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/newsletters/` | List all newsletters | All |
| POST | `/api/newsletters/` | Create a newsletter | Journalist |

---

## ✅ Running Tests

```bash
# Run all tests
python manage.py test LorenasGossip --verbosity=2

# Run a specific test class
python manage.py test LorenasGossip.tests.PublisherTests --verbosity=2
python manage.py test LorenasGossip.tests.AuthenticationTests --verbosity=2
python manage.py test LorenasGossip.tests.SignalTests --verbosity=2
```

**Test classes:**

| Class | What it tests |
|-------|--------------|
| `AuthenticationTests` | Login valid/invalid, token returned, unauthenticated access |
| `RoleBasedAccessTests` | Journalist creates, Editor approves/deletes, Reader blocked |
| `PublisherTests` | Publisher team management, join/leave, permissions |
| `SubscriptionTests` | Reader subscribed articles filtering |
| `NewsletterTests` | Journalist creates newsletters, Reader blocked |
| `SignalTests` | Signal fires on approval, email sent, API post triggered |

---

## 🛠️ Tech Stack

- **Backend:** Django 5+, Django REST Framework
- **Database:** MariaDB
- **Authentication:** DRF Token Authentication
- **Email:** Django console email backend (development)
- **Signals:** Django post_save signals
- **Frontend:** Bootstrap 5.3

---

## 📁 Project Structure

```
LorenaNewsApp/
├── LorenaNewsApp/              # Project settings
│   ├── settings.py
│   └── urls.py
├── LorenasGossip/              # Main application
│   ├── models.py               # CustomUser, Article, Newsletter
│   ├── views.py                # Web views
│   ├── api_views.py            # REST API views
│   ├── serializers.py          # DRF serializers
│   ├── permissions.py          # Custom role permissions (DRF)
│   ├── decorators.py           # Custom role decorators (web views)
│   ├── signals.py              # Post-save signals
│   ├── forms.py                # Django forms with validation
│   ├── urls.py                 # Web URL patterns
│   ├── api_urls.py             # API URL patterns
│   └── migrations/
│       └── 0003_create_groups.py  # Auto-creates groups on migrate
├── templates/
│   ├── base.html
│   ├── auth/                   # Login, register, password templates
│   ├── articles/               # Article templates
│   ├── newsletters/            # Newsletter templates
│   └── publishers/             # Publisher templates
├── docs/                       # Sphinx documentation
├── Dockerfile                  # Docker configuration
├── .env                        # Environment variables (not committed)
├── .env.example                # Environment template
├── requirements.txt
└── manage.py
```
