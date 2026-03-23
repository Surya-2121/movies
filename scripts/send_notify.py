#!/usr/bin/env python3
"""
Send ticket notification emails to subscribers.

Usage:
  python send_notify.py <movie_key> <booking_url>

Example:
  python send_notify.py peddi https://germany-telugu-movies.com/peddi.html

Requires:
  - Firebase Admin SDK: pip install firebase-admin
  - A Firebase service account key JSON file (set FIREBASE_KEY env var or place as firebase-key.json)

The script reads subscriber emails from Firebase (notify/<movie_key>),
sends each one a notification email via SMTP, and logs results.

Configure SMTP settings below or via environment variables.
"""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import firebase_admin
    from firebase_admin import credentials, db
except ImportError:
    print("Install firebase-admin: pip install firebase-admin")
    sys.exit(1)

# --- Configuration ---
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')  # your-email@gmail.com
SMTP_PASS = os.environ.get('SMTP_PASS', '')  # app password
FROM_EMAIL = os.environ.get('FROM_EMAIL', SMTP_USER)
FROM_NAME = 'Germany Telugu Movies'

FIREBASE_KEY = os.environ.get('FIREBASE_KEY', 'firebase-key.json')
FIREBASE_DB_URL = 'https://gtm-counter-default-rtdb.europe-west1.firebasedatabase.app'

MOVIE_NAMES = {
    'spirit': 'Spirit',
    'peddi': 'Peddi',
    'paradise': 'The Paradise',
    'varanasi': 'Varanasi',
    'vishwambhara': 'Vishwambhara',
    'ustaad': 'Ustaad Bhagat Singh',
}


def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_KEY)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})


def get_subscribers(movie_key):
    ref = db.reference(f'notify/{movie_key}')
    data = ref.get()
    if not data:
        return []
    emails = []
    for entry in data.values():
        if isinstance(entry, dict) and 'email' in entry:
            emails.append(entry['email'])
    return list(set(emails))


def build_email(movie_name, booking_url, to_email):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Tickets are LIVE for {movie_name} in Germany!'
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = to_email

    text = f"""Hi there!

Great news! Tickets for {movie_name} are now available for booking in Germany!

Book your tickets now: {booking_url}

Don't miss out - book early for the best seats!

- Germany Telugu Movies
https://germany-telugu-movies.com
"""

    html = f"""<div style="font-family:Segoe UI,sans-serif;max-width:600px;margin:0 auto;background:#0f0f1a;color:#e0e0e0;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px 32px;border-bottom:3px solid #f0ad4e;text-align:center;">
    <h1 style="color:#f0ad4e;margin:0;font-size:1.5rem;">Germany Telugu Movies</h1>
  </div>
  <div style="padding:32px;">
    <h2 style="color:#fff;margin:0 0 16px;">Tickets are LIVE!</h2>
    <p style="font-size:1.1rem;color:#ccc;line-height:1.6;">
      Great news! Tickets for <strong style="color:#f0ad4e;">{movie_name}</strong> are now available for booking in Germany!
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{booking_url}" style="display:inline-block;background:#f0ad4e;color:#000;padding:14px 40px;border-radius:8px;text-decoration:none;font-weight:700;font-size:1.1rem;">Book Tickets Now</a>
    </div>
    <p style="color:#888;font-size:0.85rem;">Don't miss out - book early for the best seats!</p>
  </div>
  <div style="padding:16px 32px;border-top:1px solid #2a2a4a;text-align:center;font-size:0.8rem;color:#555;">
    Germany Telugu Movies &bull; <a href="https://germany-telugu-movies.com" style="color:#f0ad4e;text-decoration:none;">germany-telugu-movies.com</a>
  </div>
</div>"""

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))
    return msg


def get_registered_users():
    """Get all registered users (from Firebase Auth via users/ node)."""
    ref = db.reference('users')
    data = ref.get()
    if not data:
        return []
    emails = []
    for uid, user in data.items():
        if isinstance(user, dict) and user.get('notifyAll') and 'email' in user:
            emails.append({'email': user['email'], 'name': user.get('name', '')})
    return emails


def build_welcome_email(name, to_email):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Welcome to Germany Telugu Movies!'
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = to_email

    greeting = f'Hi {name}!' if name else 'Hi there!'

    text = f"""{greeting}

Welcome to Germany Telugu Movies!

Thank you for creating an account. You will now be notified via email whenever tickets go on sale for upcoming Telugu movie premieres in Germany.

Stay tuned - we'll let you know as soon as the next movie tickets are live!

Visit us: https://germany-telugu-movies.com

- Germany Telugu Movies
"""

    html = f"""<div style="font-family:Segoe UI,sans-serif;max-width:600px;margin:0 auto;background:#0f0f1a;color:#e0e0e0;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:28px 32px;border-bottom:3px solid #f0ad4e;text-align:center;">
    <h1 style="color:#f0ad4e;margin:0;font-size:1.5rem;">Germany Telugu Movies</h1>
  </div>
  <div style="padding:32px;">
    <h2 style="color:#fff;margin:0 0 16px;">Welcome! &#127916;</h2>
    <p style="font-size:1.1rem;color:#ccc;line-height:1.6;">
      {greeting} Thank you for joining <strong style="color:#f0ad4e;">Germany Telugu Movies</strong>!
    </p>
    <p style="font-size:1rem;color:#ccc;line-height:1.6;">
      You will now be <strong>notified via email</strong> whenever tickets go on sale for upcoming Telugu movie premieres in Germany.
    </p>
    <div style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px;padding:20px;margin:24px 0;text-align:center;">
      <p style="color:#4caf50;font-size:1rem;margin:0 0 4px;">&#128276; Notifications Enabled</p>
      <p style="color:#888;font-size:0.85rem;margin:0;">We'll email you when the next movie tickets go live!</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="https://germany-telugu-movies.com" style="display:inline-block;background:#f0ad4e;color:#000;padding:14px 40px;border-radius:8px;text-decoration:none;font-weight:700;font-size:1rem;">Visit Website</a>
    </div>
  </div>
  <div style="padding:16px 32px;border-top:1px solid #2a2a4a;text-align:center;font-size:0.8rem;color:#555;">
    Germany Telugu Movies &bull; <a href="https://germany-telugu-movies.com" style="color:#f0ad4e;text-decoration:none;">germany-telugu-movies.com</a>
  </div>
</div>"""

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))
    return msg


def send_emails(movie_key, booking_url):
    movie_name = MOVIE_NAMES.get(movie_key, movie_key.title())

    if not SMTP_USER or not SMTP_PASS:
        print("ERROR: Set SMTP_USER and SMTP_PASS environment variables.")
        print("  For Gmail, use an App Password: https://myaccount.google.com/apppasswords")
        sys.exit(1)

    init_firebase()

    # Get per-movie subscribers
    subscribers = get_subscribers(movie_key)
    # Also get all registered users who opted for notifications
    registered = get_registered_users()
    reg_emails = [u['email'] for u in registered]
    # Merge and deduplicate
    all_emails = list(set(subscribers + reg_emails))

    if not all_emails:
        print(f"No subscribers found for '{movie_key}'.")
        return

    print(f"Found {len(all_emails)} recipient(s) for {movie_name} ({len(subscribers)} per-movie + {len(reg_emails)} registered users).")
    print(f"Sending notification emails...")

    sent = 0
    failed = 0

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)

        for email in all_emails:
            try:
                msg = build_email(movie_name, booking_url, email)
                server.sendmail(FROM_EMAIL, email, msg.as_string())
                print(f"  Sent: {email}")
                sent += 1
            except Exception as e:
                print(f"  FAILED: {email} - {e}")
                failed += 1

    print(f"\nDone! Sent: {sent}, Failed: {failed}")


def send_welcome(email, name=''):
    """Send a welcome email to a newly registered user."""
    if not SMTP_USER or not SMTP_PASS:
        print("ERROR: Set SMTP_USER and SMTP_PASS environment variables.")
        sys.exit(1)

    print(f"Sending welcome email to {email}...")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        msg = build_welcome_email(name, email)
        server.sendmail(FROM_EMAIL, email, msg.as_string())

    print("Welcome email sent!")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python send_notify.py <movie_key> <booking_url>  - Send ticket notifications")
        print("  python send_notify.py welcome <email> [name]     - Send welcome email")
        print("  python send_notify.py welcome-all                - Send welcome to all registered users")
        print("\nExamples:")
        print("  python send_notify.py peddi https://germany-telugu-movies.com/peddi.html")
        print("  python send_notify.py welcome user@example.com John")
        print("  python send_notify.py welcome-all")
        sys.exit(1)

    if sys.argv[1] == 'welcome' and len(sys.argv) >= 3:
        name = sys.argv[3] if len(sys.argv) > 3 else ''
        send_welcome(sys.argv[2], name)
    elif sys.argv[1] == 'welcome-all':
        init_firebase()
        users = get_registered_users()
        if not users:
            print("No registered users found.")
        else:
            print(f"Sending welcome emails to {len(users)} user(s)...")
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                for u in users:
                    try:
                        msg = build_welcome_email(u['name'], u['email'])
                        server.sendmail(FROM_EMAIL, u['email'], msg.as_string())
                        print(f"  Sent: {u['email']}")
                    except Exception as e:
                        print(f"  FAILED: {u['email']} - {e}")
    elif len(sys.argv) >= 3:
        send_emails(sys.argv[1], sys.argv[2])
    else:
        print("Invalid arguments. Run without args for usage.")
