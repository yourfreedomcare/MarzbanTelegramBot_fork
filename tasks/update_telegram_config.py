import os
import requests
import datetime
from time import sleep
from sqlalchemy.sql import text
from database.base import Session  # ✅ Importing existing DB session instance

# 🔹 Marzban API Configuration
MARZBAN_API_HOST = os.getenv("MARZBAN_API_HOST")
MARZBAN_ADMIN_USERNAME = os.getenv("MARZBAN_ADMIN_USERNAME")
MARZBAN_ADMIN_PASSWORD = os.getenv("MARZBAN_ADMIN_PASSWORD")

# 🔹 Global Token Storage
ACCESS_TOKEN = None


def get_access_token():
    """🔐 Fetch a new access token and store it globally """
    global ACCESS_TOKEN
    url = f"{MARZBAN_API_HOST}/api/admin/token"
    data = {
        "username": MARZBAN_ADMIN_USERNAME,
        "password": MARZBAN_ADMIN_PASSWORD,
        "grant_type": "password"
    }
    response = requests.post(url, data=data)

    if response.status_code == 200:
        ACCESS_TOKEN = response.json().get("access_token")
        print("✅ New Token Acquired and Stored Globally")
        return ACCESS_TOKEN
    else:
        print(f"❌ Token Fetch Failed: {response.text}")
        return None


def fetch_marzban_users():
    """📡 Fetch users, handling token expiration"""
    global ACCESS_TOKEN

    if not ACCESS_TOKEN:
        ACCESS_TOKEN = get_access_token()
        if not ACCESS_TOKEN:
            print("❌ Failed to get token, skipping API call")
            return None

    url = f"{MARZBAN_API_HOST}/api/users"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["users"]
    elif response.status_code == 401:  # 🔄 Token Expired
        print("🔄 Token Expired, Fetching New Token...")
        ACCESS_TOKEN = get_access_token()  # Store new token globally
        if not ACCESS_TOKEN:
            return None  # ❌ Token lene mein masla aya
        return fetch_marzban_users()  # 🔄 Retry with new token
    else:
        print(f"❌ API Request Failed: {response.text}")
        return None


def update_telegram_config():
    """🔄 Update database: Delete old & insert new links"""
    users = fetch_marzban_users()
    if not users:
        print("⚠️ No users found, skipping update.")
        return

    session = Session()  # ✅ Using existing DB instance from base.py
    try:
        for user in users:
            telegram_id = user["username"]  # 🔑 Assuming username = Telegram ID
            vless_links = user.get("links", [])
            current_time = datetime.datetime.now()  # ✅ Get current timestamp

            # ✅ Check if user exists in telegram_users
            user_exists = session.execute(
                text("SELECT COUNT(*) FROM telegram_users WHERE telegram_user_id = :telegram_id"),
                {"telegram_id": telegram_id}
            ).scalar()

            if not user_exists:
                print(f"⚠️ Skipping {telegram_id}, user does not exist in telegram_users")
                continue  # 🔄 Skip this user

            # 🛑 Delete old links
            session.execute(
                text("DELETE FROM telegram_users_configurations WHERE telegram_user_id = :telegram_id"),
                {"telegram_id": telegram_id}
            )

            # ✅ Insert new links with timestamps
            for vless_link in vless_links:
                session.execute(
                    text("""
                        INSERT INTO telegram_users_configurations 
                        (telegram_user_id, vless_link, created_at, updated_at) 
                        VALUES (:telegram_id, :vless_link, :created_at, :updated_at)
                    """),
                    {
                        "telegram_id": telegram_id,
                        "vless_link": vless_link,
                        "created_at": current_time,
                        "updated_at": current_time
                    }
                )

        session.commit()
        print(f"✅ Updated {len(users)} users in telegram_users_configurations")
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating database: {e}")
    finally:
        session.close()  # ✅ Ensure session is properly closed


if __name__ == "__main__":
    while True:
        print("⏳ Updating Telegram Configurations...")
        update_telegram_config()
        print("✅ Update Complete. Sleeping for 1 minute...")
        sleep(60)  # 🔄 1 Minute Delay
