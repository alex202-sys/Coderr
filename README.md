# Coderr

Coderr is a Django REST Framework backend for a marketplace-style platform with user profiles and offers (including offer tiers such as basic, standard, and premium).

## Tech Stack

- Python
- Django
- Django REST Framework
- Token Authentication (`rest_framework.authtoken`)
- SQLite (default for local development)

## Project Structure

```text
Coderr/
├── Backend/
│   ├── auth_app/
│   │   ├── models.py
│   │   └── api/
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       └── permissions.py
│   ├── kanban_app/
│   │   ├── models.py
│   │   └── api/
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       └── permissions.py
│   ├── core/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── manage.py
│   └── requirements.txt
└── Frontend/
```

## Features

- User registration and login with auth tokens
- Customer and business profile listing
- Profile detail retrieval and owner-only profile updates
- Offer CRUD with nested offer details
- Filtering, search, sorting, and pagination for offers
- Media file support (`/media/`)

## Local Setup (Windows)

1. Clone the repository:
   ```bash
   git clone https://github.com/alex202-sys/Coderr.git
   cd Coderr\Backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` in `Backend\`:
   ```env
   SECRET_KEY=your-django-secret-key
   ```

5. Run migrations and start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

API base URL:
`http://127.0.0.1:8000/api/`

## Authentication

Use token auth in requests:

```http
Authorization: Token <your_token>
```

## Main API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/registration/` | Register a new user |
| POST | `/api/login/` | Login and get token |
| GET | `/api/profiles/customer/` | List customer profiles |
| GET | `/api/profiles/business/` | List business profiles |
| GET | `/api/profile/<id>/` | Get profile detail |
| PATCH/PUT | `/api/profile/<id>/` | Update own profile |
| GET | `/api/offers/` | List offers |
| POST | `/api/offers/` | Create offer (business users) |
| GET | `/api/offers/<id>/` | Get offer detail |
| PATCH/PUT/DELETE | `/api/offers/<id>/` | Update/Delete own offer |

## Offer List Query Parameters

- `creator_id`
- `min_price`
- `max_delivery_time`
- `ordering` (`min_price`, `-min_price`, `updated_at`, `-updated_at`)
- `search` (title/description)
- `page_size`

## Notes

- Default global API permission is `IsAuthenticated`, with endpoint-specific overrides where needed.
- Offer creation requires exactly 3 detail items.






