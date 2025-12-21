"""
Generate RSA key pair and JWKS for Epic FHIR Backend Authentication
"""
import json
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import uuid

def generate_key_pair():
    """Generate RSA key pair"""
    print("Generating RSA key pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    with open('private_key.pem', 'wb') as f:
        f.write(private_pem)
    print("✓ Saved private_key.pem")
    
    # Get public key
    public_key = private_key.public_key()
    
    # Save public key (for reference)
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open('public_key.pem', 'wb') as f:
        f.write(public_pem)
    print("✓ Saved public_key.pem")
    
    return public_key

def public_key_to_jwk(public_key):
    """Convert public key to JWK format"""
    print("\nConverting public key to JWK format...")
    
    # Get public numbers
    public_numbers = public_key.public_numbers()
    
    # Convert to base64url (no padding)
    def int_to_base64url(num):
        num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
        return base64.urlsafe_b64encode(num_bytes).rstrip(b'=').decode('utf-8')
    
    # Generate a key ID
    kid = str(uuid.uuid4())
    
    jwk = {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS384",
        "n": int_to_base64url(public_numbers.n),
        "e": int_to_base64url(public_numbers.e)
    }
    
    return jwk, kid

def create_jwks_file(jwk):
    """Create JWKS file with the JWK"""
    jwks = {
        "keys": [jwk]
    }
    
    with open('jwks.json', 'w') as f:
        json.dump(jwks, f, indent=2)
    print("✓ Saved jwks.json")
    
    return jwks

def main():
    print("=" * 60)
    print("Epic FHIR Backend Authentication - Key Generation")
    print("=" * 60)
    
    # Generate keys
    public_key = generate_key_pair()
    
    # Convert to JWK
    jwk, kid = public_key_to_jwk(public_key)
    
    # Create JWKS file
    jwks = create_jwks_file(jwk)
    
    print("\n" + "=" * 60)
    print("SUCCESS! Files generated:")
    print("=" * 60)
    print("1. private_key.pem - Keep this SECRET, never commit to git")
    print("2. public_key.pem  - For reference only")
    print("3. jwks.json       - Upload this to GitHub Pages")
    print("\nKey ID (kid):", kid)
    print("\nNext steps:")
    print("1. Create a GitHub repo for hosting JWKS")
    print("2. Upload jwks.json to the repo")
    print("3. Enable GitHub Pages")
    print("4. Use the GitHub Pages URL in Epic app registration")
    print("=" * 60)

if __name__ == "__main__":
    main()