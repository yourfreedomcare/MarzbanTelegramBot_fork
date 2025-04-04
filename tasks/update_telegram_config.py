import os
import requests
import datetime
import sqlite3
from time import sleep
from sqlalchemy.sql import text
from database.base import Session, engine  # ✅ Importing existing DB session instance
import mysql.connector


# 🔹 Marzban API Configuration
MARZBAN_API_HOST = os.getenv("MARZBAN_API_HOST")
MARZBAN_ADMIN_USERNAME = os.getenv("MARZBAN_ADMIN_USERNAME")
MARZBAN_ADMIN_PASSWORD = os.getenv("MARZBAN_ADMIN_PASSWORD")

# 🔹 Global Token Storage
ACCESS_TOKEN = None


def get_access_token():
    """🔐 Fetch a new access token and store it globally"""
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



def fetch_marzban_hosts():

    # Path to your SQLite database
    db_path = 'marzban_db.sqlite3'

    # Create a connection to the SQLite database
    conn = sqlite3.connect(db_path)

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # Query to fetch all rows from the 'hosts' table
    cursor.execute("SELECT * FROM hosts")

    # Fetch all rows from the result of the query
    return cursor.fetchall()


if __name__ == "__main__":

    # Execute query in the mysql DB to check all hosts records.

#    with engine.connect() as connection:
#        tg_bot_hosts = connection.execute(text("SELECT * FROM hosts"))  # Replace with your actual query/table

    insert_query = """
        INSERT INTO hosts (
            id, remark, address, port, inbound_tag, sni, host, security, alpn, fingerprint,
            allowinsecure, is_disabled, path, mux_enable, fragment_setting, random_user_agent,
            noise_setting, use_sni_as_host
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    print("BEGINS WITH THE SCRIPT")

    while True:

        marzban_hosts = fetch_marzban_hosts()

        connection = mysql.connector.connect(
            host="mysql",
            user="marzuser",
            password="marzpassword",
            database="marzban",
        )
        cursor = connection.cursor()

        sleep(20)

        cursor.execute("SELECT * FROM hosts")
        telegram_existing_hosts = cursor.fetchall()

        if marzban_hosts != telegram_existing_hosts:
            print(f"\n\n\nDELETING PREVIOUS HOSTS FROM TELE_BOT", flush=True)
            cursor.execute("Delete from hosts")
            print(f"HOSTS DELETED\n\n", flush=True)

            for host in marzban_hosts:
                cursor.execute(insert_query, host)
                print(f"HOST ADDED: {host}", flush=True)

            connection.commit()

            print("⏳ Updating Telegram Configurations...")
            update_telegram_config()
            print("✅ Update Complete. Sleeping for 1 minute...")
            print("CHANGES COMMITTED ✅\n\n\n", flush=True)

        else:
            print("\n\n\n✅ No changes detected.", flush=True)
            print(marzban_hosts)
            print(telegram_existing_hosts)
            print("\n\n\n✅ No changes detected.", flush=True)

