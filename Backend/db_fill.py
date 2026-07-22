"""
db_fill.py
----------
Populates the database with realistic seed data that mirrors the
current state of db.sqlite3 (users, profiles, offers, offer details).

Run from the Backend/ directory:
    python db_fill.py

The script is idempotent: existing objects (matched by username / title+user)
are skipped, so it is safe to run multiple times.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User
from auth_app.models import UserProfile
from kanban_app.models import Offer, OfferDetail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_or_create_user(username, email, password, first_name="", last_name="",
                       is_superuser=False, is_staff=False):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_superuser": is_superuser,
            "is_staff": is_staff,
            "is_active": True,
        },
    )
    if created:
        user.set_password(password)
        user.save()
        print(f"  [+] User created:  {username}")
    else:
        print(f"  [=] User exists:   {username}")
    return user


def get_or_create_profile(user, profile_type, location="", tel="",
                          description="", working_hours=""):
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "type": profile_type,
            "location": location,
            "tel": tel,
            "description": description,
            "working_hours": working_hours,
        },
    )
    if created:
        print(f"  [+] Profile created: {user.username} ({profile_type})")
    else:
        print(f"  [=] Profile exists:  {user.username} ({profile.type})")
    return profile


def create_offer_with_details(user, title, description, details):
    """
    details is a list of 3 dicts, each with keys:
        title, offer_type, price, revisions, delivery_time_in_days, features
    """
    existing = Offer.objects.filter(user=user, title=title).first()
    if existing:
        print(f"  [=] Offer exists:  '{title}'")
        return existing

    offer = Offer.objects.create(user=user, title=title, description=description)
    print(f"  [+] Offer created: '{title}'")
    for d in details:
        OfferDetail.objects.create(offer=offer, **d)
    return offer


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

print("\n--- Users ---")

example1 = get_or_create_user(
    username="example_username1",
    email="example1@mail.de",
    password="pw123123",
    first_name="Example",
    last_name="Username1",
)
example2 = get_or_create_user(
    username="example_username2",
    email="example2@mail.de",
    password="pw123123",
    first_name="Example",
    last_name="Username2",
)
example3 = get_or_create_user(
    username="example_username3",
    email="example3@mail.de",
    password="pw123123",
    first_name="Example",
    last_name="Username3",
)
example4 = get_or_create_user(
    username="example_username4",
    email="example4@mail.de",
    password="pw123123",
    first_name="Example",
    last_name="Username4",

)
example5 = get_or_create_user(
    username="example_username5",
    email="example5@mail.de",
    password="pw123123",
    first_name="Example",
    last_name="Username5",
)
example6 = get_or_create_user(
    username="example_username6",
    email="example6@mail.de",
    password="pw123123",
    first_name="Example",
    last_name="Username6",

)
maxim = get_or_create_user(
    username="maxim_mustermann",
    email="maxim@business.de",
    password="pw123123",
    first_name="Maxim",
    last_name="Mustermann",
)
maximm = get_or_create_user(
    username="maximm_username7",
    email="maximm@business.de",
    password="pw123123",
    first_name="MaximM",
    last_name="Username7",
)
admin = get_or_create_user(
    username="aleks_coderr",
    email="aleks@gmail.de",
    password="pw123123",
    first_name="Aleks",
    last_name="Coderr",
    is_superuser=True,
    is_staff=True,
)

# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

print("\n--- Profiles ---")

get_or_create_profile(example1, "customer")
get_or_create_profile(example2, "customer")
get_or_create_profile(example3, "customer")
get_or_create_profile(example4, "customer")
get_or_create_profile(example5, "business")
get_or_create_profile(example6, "business")
get_or_create_profile(maxim,    "business", location="Berlinnn",  tel="9876543212",
                      description="Updated business description1", working_hours="10-19")
get_or_create_profile(maximm,   "business", location="Berlinnn7", tel="98765432123",
                      description="Updated business description1", working_hours="10-19")
get_or_create_profile(admin,    "business", location="Berlinnn",  tel="9876543214",
                      description="Updated business description1", working_hours="10-19")

# ---------------------------------------------------------------------------
# Offers  (created by maximm — the main business test user)
# ---------------------------------------------------------------------------

print("\n--- Offers ---")

STANDARD_DETAILS = [
    {
        "title": "Basic Design",
        "offer_type": "basic",
        "revisions": 2,
        "delivery_time_in_days": 5,
        "price": "102.12",
        "features": ["Logo Design", "Visitenkarte"],
    },
    {
        "title": "Standard Design",
        "offer_type": "standard",
        "revisions": 5,
        "delivery_time_in_days": 7,
        "price": "202.22",
        "features": ["Logo Design", "Visitenkarte", "Briefpapier"],
    },
    {
        "title": "Premium Design",
        "offer_type": "premium",
        "revisions": 10,
        "delivery_time_in_days": 10,
        "price": "505.05",
        "features": ["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
    },
]

for i in range(2, 10):
    create_offer_with_details(
        user=maxim,
        title=f"Grafikdesign-Paket {i}",
        description=f"Ein umfassendes Grafikdesign-Paket für Unternehmen.{i}",
        details=STANDARD_DETAILS,
    )

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n--- Summary ---")
print(f"  Users:         {User.objects.count()}")
print(f"  Profiles:      {UserProfile.objects.count()}")
print(f"  Offers:        {Offer.objects.count()}")
print(f"  OfferDetails:  {OfferDetail.objects.count()}")
print("\nDone.\n")
