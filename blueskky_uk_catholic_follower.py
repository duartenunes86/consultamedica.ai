#!/usr/bin/env python3
"""
Bluesky UK Catholic Follower
Monitors the firehose for any post, fetches the author's profile,
and follows them if they are from the UK and mention Catholic/Christianity in their bio.
Waits 60 seconds before following. Max 200 follows/hour.
"""

import sys
import os
import time
import json
import random
from datetime import datetime
from collections import deque
from threading import Lock, Thread

try:
    import websocket
    from atproto import Client
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client", "atproto", "--break-system-packages"])
    import websocket
    from atproto import Client


UK_TERMS = {
    'uk', 'united kingdom', 'england', 'scotland', 'wales', 'northern ireland',
    'london', 'manchester', 'birmingham', 'liverpool', 'glasgow', 'edinburgh',
    'bristol', 'leeds', 'sheffield', 'cardiff', 'belfast', 'newcastle',
    'british', 'britain', 'english', 'scottish', 'welsh', 'yorkshire',
    'lancashire', 'cornwall', 'kent', 'surrey', 'essex', 'sussex',
    'hampshire', 'nottingham', 'leicester', 'oxford', 'cambridge',
    'brighton', 'exeter', 'plymouth', 'derby', 'norfolk', 'suffolk',
    '.co.uk', 'bbc', 'nhs'
}

CATHOLIC_TERMS = {
    'catholic', 'catholicism', 'roman catholic', 'papal', 'vatican',
    'mass', 'rosary', 'pope', 'jesuit', 'dominican', 'franciscan',
    'our lady', 'blessed virgin', 'eucharist', 'confirmation',
    'confession', 'purgatory', 'catechism', 'holy see', 'diocese',
    'parish', 'priest', 'nun', 'monk', 'monastery', 'convent',
    'saint', 'st.', 'patron saint', 'marian', 'fatima', 'lourdes'
}


def is_uk_catholic(bio):
    """Check if bio contains UK and Catholic terms."""
    bio_lower = bio.lower()
    has_uk = any(term in bio_lower for term in UK_TERMS)
    has_catholic = any(term in bio_lower for term in CATHOLIC_TERMS)
    return has_uk and has_catholic


class UKCatholicFollower:
    def __init__(self, handle, password):
        self.handle = handle
        self.password = password
        self.client = None
        self.running = True
        self.lock = Lock()

        self.followed_users = set()
        self.checked_authors = set()

        self.stats = {
            'posts_seen': 0,
            'profiles_checked': 0,
            'matches_found': 0,
            'follows_made': 0,
            'errors': 0,
            'start_time': time.time()
        }

        # Rate limiting: max 200/hour = 1 every 18 seconds
        self.min_follow_interval = 18
        self.last_follow_time = 0

        # Queue: (author_did, scheduled_time)
        self.pending_follows = deque()
        self.follow_thread = Thread(target=self._follow_worker, daemon=True)
        self.profile_thread = Thread(target=self._profile_checker, daemon=True)

        # Queue of author_dids to check profiles for
        self.authors_to_check = deque()

    def authenticate(self):
        try:
            self.client = Client()
            self.client.login(self.handle, self.password)
            print(f"✅ Authenticated as {self.handle}\n")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("💡 Use an App Password from Settings → App Passwords")
            return False

    def process_message(self, message_data):
        try:
            data = json.loads(message_data)

            if data.get('kind') != 'commit':
                return

            commit = data.get('commit', {})
            if commit.get('collection') != 'app.bsky.feed.post':
                return
            if commit.get('operation') != 'create':
                return

            author_did = data.get('did')
            if not author_did:
                return

            self.stats['posts_seen'] += 1

            if self.stats['posts_seen'] % 500 == 0:
                runtime = time.time() - self.stats['start_time']
                rate = self.stats['posts_seen'] / runtime if runtime > 0 else 0
                print(f"\r⏳ Posts: {self.stats['posts_seen']:,} | "
                      f"Rate: {rate:.0f}/sec | "
                      f"Checked: {self.stats['profiles_checked']} | "
                      f"Matches: {self.stats['matches_found']} | "
                      f"Follows: {self.stats['follows_made']}",
                      end='', flush=True)

            with self.lock:
                if author_did in self.checked_authors or author_did in self.followed_users:
                    return
                self.checked_authors.add(author_did)

            self.authors_to_check.append(author_did)

        except Exception:
            pass

    def _profile_checker(self):
        """Background thread that fetches profiles and filters UK Catholics."""
        while self.running:
            if not self.authors_to_check:
                time.sleep(0.1)
                continue

            author_did = self.authors_to_check.popleft()

            try:
                profile = self.client.get_profile(author_did)
                bio = profile.description or ''
                self.stats['profiles_checked'] += 1

                if not bio:
                    continue

                if is_uk_catholic(bio):
                    self.stats['matches_found'] += 1
                    scheduled_time = time.time() + 60
                    self.pending_follows.append((author_did, profile.handle, profile.display_name or profile.handle, scheduled_time))

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n\n🎯 UK CATHOLIC FOUND | {timestamp}")
                    print(f"   👤 {profile.display_name or profile.handle} (@{profile.handle})")
                    print(f"   📝 Bio: {bio[:120].replace(chr(10), ' ')}")
                    print(f"   ⏳ Following in 60s...")

            except Exception:
                pass

            # Small delay to avoid hammering the profile API
            time.sleep(0.05)

    def _follow_worker(self):
        """Background thread: follows matched users after 60s delay, max 200/hour."""
        while self.running:
            now = time.time()
            if self.pending_follows and self.pending_follows[0][3] <= now:
                # Enforce rate limit
                time_since_last = now - self.last_follow_time
                if time_since_last < self.min_follow_interval:
                    time.sleep(self.min_follow_interval - time_since_last)

                author_did, handle, display_name, _ = self.pending_follows.popleft()
                self._follow_user(author_did, handle, display_name)
                self.last_follow_time = time.time()
            else:
                time.sleep(1)

    def _follow_user(self, author_did, handle, display_name):
        try:
            self.client.follow(author_did)
            self.followed_users.add(author_did)
            self.stats['follows_made'] += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"\n{'='*80}")
            print(f"✅ FOLLOWED #{self.stats['follows_made']} | {timestamp}")
            print(f"👤 {display_name} (@{handle})")
            print(f"📊 Follows: {self.stats['follows_made']} | Matches found: {self.stats['matches_found']}")
            print(f"{'='*80}\n")

        except Exception as e:
            error_msg = str(e).lower()
            if "already follow" in error_msg or "duplicate" in error_msg:
                pass
            elif "accounttakedown" in error_msg or "taken down" in error_msg:
                pass
            else:
                print(f"\n⚠️  Error following @{handle}: {e}")
                self.stats['errors'] += 1

    def print_summary(self):
        runtime = time.time() - self.stats['start_time']
        print(f"\n\n{'='*80}")
        print(f"📊 SUMMARY")
        print(f"{'='*80}")
        print(f"⏱️  Runtime: {int(runtime // 60)}m {int(runtime % 60)}s")
        print(f"📥 Posts seen: {self.stats['posts_seen']:,}")
        print(f"🔍 Profiles checked: {self.stats['profiles_checked']:,}")
        print(f"🎯 UK Catholics found: {self.stats['matches_found']}")
        print(f"✅ Follows made: {self.stats['follows_made']}")
        print(f"⚠️  Errors: {self.stats['errors']}")
        print(f"{'='*80}\n")

    def connect_to_firehose(self):
        url = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

        def on_message(ws, message):
            self.process_message(message)

        def on_error(ws, error):
            if self.running:
                print(f"\n⚠️  Connection error: {error}")

        def on_close(ws, close_status_code, close_msg):
            if self.running:
                print("\n🔌 Reconnecting...")
                time.sleep(5)
                if self.running:
                    self.connect_to_firehose()

        def on_open(ws):
            print("✅ Connected to Bluesky firehose")
            print("🔍 Scanning all posts for UK Catholic authors...\n")

        ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        try:
            ws.run_forever()
        except KeyboardInterrupt:
            self.running = False

    def start(self):
        if not self.authenticate():
            return

        print(f"{'='*80}")
        print(f"🇬🇧 BLUESKY UK CATHOLIC FOLLOWER")
        print(f"{'='*80}")
        print(f"Scans all posts → checks author bio → follows if UK + Catholic")
        print(f"Delay: 60s before following | Rate: max 200/hour")
        print(f"{'='*80}\n")

        self.profile_thread.start()
        self.follow_thread.start()

        try:
            self.connect_to_firehose()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
            self.running = False
            self.print_summary()
            print("✅ Stopped")


def main():
    print("="*80)
    print("🇬🇧 BLUESKY UK CATHOLIC FOLLOWER")
    print("="*80)

    # Read credentials from environment variables (for Render deployment)
    handle = os.environ.get("BLUESKY_HANDLE", "").strip()
    password = os.environ.get("BLUESKY_PASSWORD", "").strip()

    # Fall back to interactive input if not set (for local use)
    if not handle:
        handle = input("Bluesky handle (e.g., username.bsky.social): ").strip()
    if not password:
        password = input("App password: ").strip()

    if not handle or not password:
        print("❌ Handle and password required. Exiting.")
        sys.exit(1)

    follower = UKCatholicFollower(handle, password)
    follower.start()


if __name__ == "__main__":
    main()
