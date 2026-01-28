import pyotp
import json
import argparse
import logging
from config import USER_DB

def generate_auth_link(email: str, debug: bool) -> None:
    """
    Generate authentication link and save user credentials.
    
    Creates a Google Authenticator secret and saves user credentials to a JSON file.
    Generates a provisioning URI for QR code generation.
    
    Args:
        email (str): User's email address
        debug (bool): if we generate debug otp
        
    Returns:
        None
    """
    otp_secret = pyotp.random_base32()
    
    user = {
    "email": email,
    "otp_secret": otp_secret}

    json_str = json.dumps(user, indent=4)
    with open(USER_DB, "w") as f:
        f.write(json_str)

    totp = pyotp.TOTP(otp_secret)
    appname = 'Brainiac5'
    if debug: 
        appname = "Brainiac5-dev"
    issuer_name = "Seroul Pierre"
    uri = totp.provisioning_uri(name=appname, issuer_name=issuer_name)

    logging.info(f"Pasted the following link in Qr.io to obtain a QR code : {uri}")

def verify_access(email: str, secret_key: str) -> bool:
    with open(USER_DB, "r") as f:
        user = json.load(f)

    totp = pyotp.TOTP(user['otp_secret'])
    if email == user["email"] and totp.verify(secret_key):
        return True
    
    return False
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create user and generate Google Auth')
    parser.add_argument('email', type=str, help='Email of the user')
    parser.add_argument('-d', '--debug', help='generate a Google Auth for debug purpose', action="store_true")

    args = parser.parse_args()

    generate_auth_link(args.email, args.debug)
