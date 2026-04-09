import pyotp
import argparse
import logging
import os
import sqlite3
from config import set_env_var
from data_handler import init_database

logger = logging.getLogger("uvicorn.error")


def generate_otp_secret() -> str:
    """Generate a random base32 OTP secret."""
    return pyotp.random_base32()


def get_provisioning_uri(email: str, secret: str, debug: bool = False) -> str:
    """Build a TOTP provisioning URI for QR-code generation.

    Args:
        email (str): User's email address (used as the account name).
        secret (str): Base32 OTP secret.
        debug (bool): Whether to use the dev app name.

    Returns:
        str: TOTP provisioning URI.
    """
    totp = pyotp.TOTP(secret)
    issuer_name = "Seroul Pierre"
    return totp.provisioning_uri(name=email, issuer_name=issuer_name)


def generate_auth_link(email: str, debug: bool) -> None:
    """
    Generate authentication link and save user credentials.

    Creates a Google Authenticator secret and saves user credentials to the SQLite database.
    Generates a provisioning URI for QR code generation.

    Args:
        email (str): User's email address
        debug (bool): if we generate debug otp

    Returns:
        None
    """
    otp_secret = generate_otp_secret()

    # Save user to SQLite database
    conn = sqlite3.connect(os.getenv('NAME_DB'))
    cursor = conn.cursor()
    try:
        # Extract username from email (part before @)
        username = email.split('@')[0]
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (username, email, otp_secret)
        )
        conn.commit()
        logger.info(f"User '{email}' added successfully to database.")
    except sqlite3.IntegrityError:
        logger.info(f"Error: User '{email}' already exists.")
    finally:
        conn.close()

    uri = get_provisioning_uri(email, otp_secret, debug)
    print(f"Pasted the following link in Qr.io to obtain a QR code : {uri}")


def verify_access(email: str, secret_key: str) -> bool:
    conn = sqlite3.connect(os.getenv('NAME_DB'))
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT hashed_password FROM users WHERE email = ?",
            (email,)
        )
        result = cursor.fetchone()

        if result:
            otp_secret = result[0]
            totp = pyotp.TOTP(otp_secret)
            if totp.verify(secret_key):
                return True

        return False
    finally:
        conn.close()


if __name__ == "__main__":
    set_env_var()
    init_database()
    parser = argparse.ArgumentParser(description='Create user and generate Google Auth')
    parser.add_argument('email', type=str, help='Email of the user')
    parser.add_argument('-d', '--debug', help='generate a Google Auth for debug purpose', action="store_true")

    args = parser.parse_args()

    generate_auth_link(args.email, args.debug)
