#!/usr/bin/env python3
"""
AUTHOR 
Papabear

Instagram post downloader (Instaloader) dengan delay/randomized sleep dan retry.
Tujuan: mengurangi kemungkinan rate-limit / deteksi bot oleh Instagram.

Catatan:
- Disarankan membuat session sekali via CLI:
    instaloader --login=YOUR_USERNAME
  agar SESSION-USERNAME dibuat. Script akan coba load session terlebih dahulu.
- Jika muncul "suspicious login attempt" saat login pertama kali, approve login via HP/browser.
"""

import instaloader
import getpass
import sys
import os
import re
import time
import random
import socket

# ---------------- utilities ----------------
def sanitize_filename(name: str) -> str:
    """Buat nama folder/file aman (cross-platform)."""
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip()

def check_dns(host="www.instagram.com", timeout=5):
    """Cek resolusi DNS dasar. Kegagalan biasanya berarti DNS/network issue."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(host)
        return True
    except Exception as e:
        print(f"❌ DNS/Network check failed: {e}")
        return False

def get_credentials():
    """Minta username/password; fallback ke input() jika getpass tidak supported."""
    username = input("Enter your Instagram username: ").strip()
    try:
        password = getpass.getpass("Enter your Instagram password: ").strip()
    except Exception:
        password = input("Enter your Instagram password (visible): ").strip()
    return username, password

# ---------------- login/session ----------------
def login_with_session(loader, username=None, allow_interactive=True):
    """
    Coba load session file; jika tidak ada, login interaktif lalu save session.
    Returns the username used for session (may be provided or from credentials).
    """
    if username:
        try:
            loader.load_session_from_file(username)
            print("✅ Loaded session from file.")
            return username
        except FileNotFoundError:
            print("⚠️ Session file not found for user:", username)

    if not allow_interactive:
        raise RuntimeError("No session available and interactive login disabled.")

    # Interactive login flow
    user, passwd = get_credentials()
    # random short pause before login to reduce identical-pattern requests
    time.sleep(random.uniform(1.5, 4.0))
    try:
        loader.context.log("Attempting login...")
        loader.login(user, passwd)
        # save session for reuse
        try:
            loader.save_session_to_file()
            print("✅ Login successful and session saved.")
        except Exception:
            print("⚠️ Login successful but could not save session file.")
        return user
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        # 2FA path: ask code, then call two-factor login method
        print("⚠️ Two-factor authentication required.")
        code = input("Enter 2FA code (from your authenticator/SMS): ").strip()
        try:
            # try loader.two_factor_login (Instaloader supports this)
            loader.two_factor_login(code)
            try:
                loader.save_session_to_file()
            except Exception:
                pass
            print("✅ 2FA login successful and session saved.")
            return user
        except Exception as e:
            raise RuntimeError(f"2FA login failed: {e}")
    except instaloader.exceptions.LoginException as e:
        raise RuntimeError(f"Login failed: {e}")
    except instaloader.exceptions.ConnectionException as e:
        raise RuntimeError(f"Connection error during login: {e}")

# ---------------- downloading with delays & retries ----------------
def download_posts_with_delays(loader, profile, min_delay=3.0, max_delay=8.0,
                               per_post_retries=3, backoff_base=2.0):
    """
    Download all posts from profile with randomized delays and per-post retry/backoff.
    - min_delay, max_delay: seconds to sleep between downloads (random uniform)
    - per_post_retries: number of retries for each post upon transient errors
    - backoff_base: exponential backoff base multiplier
    """
    safe_name = sanitize_filename(profile.username)
    os.makedirs(safe_name, exist_ok=True)

    total = 0
    print(f"📥 Starting download for @{profile.username} into folder '{safe_name}'")
    posts_iter = profile.get_posts()

    for post in posts_iter:
        attempt = 0
        while attempt <= per_post_retries:
            try:
                loader.download_post(post, target=safe_name)
                total += 1
                # successful download -> break retry loop
                break
            except KeyboardInterrupt:
                print("\n⛔ Interrupted by user. Exiting.")
                return total
            except instaloader.exceptions.ConnectionException as e:
                attempt += 1
                wait = (backoff_base ** attempt) + random.uniform(0.5, 2.0)
                print(f"⚠️ Connection error while downloading a post: {e}. "
                      f"Retry {attempt}/{per_post_retries} after {wait:.1f}s")
                time.sleep(wait)
                continue
            except Exception as e:
                # Other errors: show detail and skip this post after retries exhausted
                attempt += 1
                wait = (backoff_base ** attempt) + random.uniform(0.5, 2.0)
                print(f"⚠️ Error downloading post (attempt {attempt}/{per_post_retries}): {e}. "
                      f"Retry after {wait:.1f}s")
                time.sleep(wait)
                continue

        # After per-post tries finished, sleep before next post to mimic human behavior
        sleep_time = random.uniform(min_delay, max_delay)
        # add tiny additional jitter
        sleep_time += random.uniform(0.0, 1.2)
        print(f"⏱ Sleeping {sleep_time:.1f}s before next post...")
        time.sleep(sleep_time)

    print(f"✅ Finished. Total posts downloaded: {total}")
    return total

# ---------------- main ----------------
def main():
    # quick DNS/network check
    if not check_dns():
        print("Please check your internet connection / DNS (try 8.8.8.8 or 1.1.1.1). Exiting.")
        sys.exit(1)

    loader = instaloader.Instaloader(download_comments=False, save_metadata=False)
    # Optionally set some instaloader settings to be less aggressive
    loader.context.sleep = 0  # we manage sleep ourselves

    # Ask target
    target_profile = input("Enter the Instagram username to download posts from: ").strip()
    if not target_profile:
        print("No username provided. Exiting.")
        sys.exit(1)

    # Try to use existing session if available. Ask user for preferred session username (optional).
    session_user = input("If you have a saved Instaloader session username, enter it (or press Enter to skip): ").strip() or None

    # login/session handling
    try:
        used_user = login_with_session(loader, username=session_user, allow_interactive=True)
    except RuntimeError as e:
        print(f"❌ Login/session error: {e}")
        # if login failed, still try proceed as anonymous (but likely will hit private/profile limits)
        proceed = input("Continue without login? (yes/no): ").strip().lower()
        if proceed != "yes":
            sys.exit(1)
        else:
            used_user = None

    # small random pause before profile query to avoid identical-pattern requests
    time.sleep(random.uniform(1.0, 3.0))

    try:
        profile = instaloader.Profile.from_username(loader.context, target_profile)
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"❌ The profile '{target_profile}' does not exist.")
        sys.exit(1)
    except instaloader.exceptions.QueryReturnedNotFoundException:
        print("❌ Query returned not found. Instagram may have changed the API or blocked the request.")
        sys.exit(1)
    except instaloader.exceptions.ConnectionException as e:
        print(f"❌ Connection error when fetching profile: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error when fetching profile: {e}")
        sys.exit(1)

    # if private and not logged-in or not following, warn and exit
    try:
        if profile.is_private:
            # loader.test_login() returns True if session loaded and valid
            if not loader.test_login():
                print(f"❌ The profile '{target_profile}' is private. You must be logged in and follow them.")
                sys.exit(1)
    except Exception:
        # ignore potential test_login issues and continue (will likely fail later)
        pass

    # Use conservative delays by default. You can tune min_delay/max_delay.
    MIN_DELAY = 4.0   # minimum seconds between downloads
    MAX_DELAY = 9.0   # maximum seconds between downloads
    PER_POST_RETRIES = 3

    try:
        download_posts_with_delays(
            loader,
            profile,
            min_delay=MIN_DELAY,
            max_delay=MAX_DELAY,
            per_post_retries=PER_POST_RETRIES,
            backoff_base=2.0
        )
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user. Exiting.")
    except Exception as e:
        print(f"❌ Unexpected error during download: {e}")

if __name__ == "__main__":
    main()
