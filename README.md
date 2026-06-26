# Coderr

Coderr is a Django REST Framework backend for a marketplace platform with authentication, profiles, offers, orders, reviews, and aggregated base information endpoints.

## Tech Stack

- Python
- Django
- Django REST Framework
- Token Authentication (`rest_framework.authtoken`)
- SQLite (local default)

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
│   │   ├── api/
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── permissions.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_offer.py
│   │       ├── test_offer_filter.py
│   │       ├── test_offer_patch.py
│   │       ├── test_offer_delete.py
│   │       ├── test_orders.py
│   │       ├── test_review.py
│   │       └── test_base_info.py
│   ├── core/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── manage.py
│   └── requirements.txt
└── Frontend/ # The project consists only of the backend API component only, without a frontend.
```

## Main API Endpoints

| Area | Endpoints |
| --- | --- |
| Auth | `POST /api/registration/`, `POST /api/login/` |
| Profiles | `GET /api/profiles/customer/`, `GET /api/profiles/business/`, `GET/PATCH /api/profile/<id>/` |
| Offers | `GET/POST /api/offers/`, `GET/PATCH/DELETE /api/offers/<id>/`, `GET /api/offerdetails/<id>/` |
| Orders | `GET/POST /api/orders/`, `PATCH/DELETE /api/orders/<id>/`, `GET /api/order-count/<business_user_id>/`, `GET /api/completed-order-count/<business_user_id>/` |
| Reviews | `GET/POST /api/reviews/`, `PATCH/DELETE /api/reviews/<id>/` |
| Base Info | `GET /api/base-info/` |

## Offer List Query Parameters

- `creator_id`
- `min_price`
- `max_delivery_time`
- `ordering` (`min_price`, `-min_price`, `updated_at`, `-updated_at`)
- `search`
- `page_size`

## Local Setup (Windows)

```bash
git clone https://github.com/alex202-sys/Coderr.git
cd Coderr\Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `Backend\.env`:

```env
cp .env.template .env
```

Open your newly created `.env` file and define your development variables cleanly without quotes or extra spacing:

```python
SECRET_KEY=your-django-secret-key
```

Run:

```bash
python manage.py migrate
python manage.py runserver
```

The local service endpoint will spawn cleanly on http://127.0.0.1:8000/api/



## Testing

Run all tests:

```bash
python manage.py test kanban_app
```

Run specific modules:

```bash
python manage.py test kanban_app.tests.test_offer
python manage.py test kanban_app.tests.test_offer_filter
python manage.py test kanban_app.tests.test_offer_patch
python manage.py test kanban_app.tests.test_offer_delete
python manage.py test kanban_app.tests.test_orders
python manage.py test kanban_app.tests.test_review
python manage.py test kanban_app.tests.test_base_info
```
