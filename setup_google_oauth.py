#!/usr/bin/env python
"""
Setup script for Google OAuth in Django Allauth
This properly configures Google OAuth to avoid MultipleObjectsReturned errors
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crackers_ecommerce.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

print("=" * 70)
print("GOOGLE OAUTH SETUP FOR DJANGO ALLAUTH")
print("=" * 70)

# Step 1: Ensure we have the correct site
try:
    site = Site.objects.get(pk=1)
except Site.DoesNotExist:
    site = Site.objects.create(pk=1, domain='localhost:8000', name='Kannan Crackers')

print(f"\n✓ Site configured: {site.domain} ({site.name})")

# Step 2: Delete ALL existing Google OAuth apps (to prevent MultipleObjectsReturned)
existing = SocialApp.objects.filter(provider='google')
if existing.exists():
    count = existing.count()
    existing.delete()
    print(f"✓ Cleaned up {count} existing Google OAuth app(s)")

# Step 3: Create a single Google OAuth app
# This will use the credentials from Django admin or environment variables
google_app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={
        'name': 'Google',
        'client_id': 'YOUR_GOOGLE_CLIENT_ID',
        'secret': 'YOUR_GOOGLE_CLIENT_SECRET',
    }
)

# Ensure this site is associated with the app
if not google_app.sites.filter(pk=1).exists():
    google_app.sites.add(site)
    print(f"✓ Associated site with Google OAuth app")

if created:
    print(f"✓ Created new Google OAuth app")
else:
    print(f"✓ Using existing Google OAuth app")

print(f"\nGoogle OAuth App Configuration:")
print(f"  Provider: google")
print(f"  Name: {google_app.name}")
print(f"  Client ID: {google_app.client_id}")
print(f"  Secret: {'*' * 20}")
print(f"  Associated Sites: {list(google_app.sites.all().values_list('domain', flat=True))}")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("""
1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select an existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials (Web application)
5. Add these Authorized redirect URIs:
   - http://localhost:8000/accounts/google/login/callback/
   - http://127.0.0.1:8000/accounts/google/login/callback/
   - http://your-domain.com/accounts/google/login/callback/ (for production)
   - https://your-domain.com/accounts/google/login/callback/ (for production)

6. Copy the Client ID and Client Secret
7. Go to Django Admin: http://localhost:8000/admin/
8. Navigate to: Social applications
9. Edit the Google OAuth app
10. Paste your Client ID and Secret
11. Make sure ONLY your site is selected
12. Save and test!
""")
print("=" * 70)

