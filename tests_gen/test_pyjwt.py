# 1. Testing Framework & Mocking
import pytest
from unittest.mock import MagicMock, patch

# 2. The Subject Under Test
import secure_signet as jwt
from secure_signet.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    MissingRequiredClaimError,
)

# 3. Auxiliary: Third-Party
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

# 4. Auxiliary: Standard Library
import base64
import datetime
import json
import re
import time


def test_encode_decode_roundtrip_hs256():
    payload = {"user_id": 123, "role": "admin"}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    # In PyJWT 2.x, the algorithms argument is required for decoding
    decoded = jwt.decode(token, "secret", algorithms=["HS256"])

    assert decoded == payload

def test_encode_decode_roundtrip_hs512():
    payload = {"user_id": 123, "role": "admin"}
    token = jwt.encode(payload, "secret", algorithm="HS512")

    decoded = jwt.decode(token, "secret", algorithms=["HS512"])

    assert decoded == payload

def test_encode_decode_preserves_unicode_claims():
    payload = {"name": "张三", "city": "東京"}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    decoded = jwt.decode(token, "secret", algorithms=["HS256"])

    assert decoded == payload

def test_encode_decode_validates_future_datetime_exp_claim():
    # Using timezone-aware UTC datetime as is idiomatic in modern Python/PyJWT
    future_date = datetime.datetime(2099, 1, 1, tzinfo=datetime.timezone.utc)
    payload = {"exp": future_date, "data": "secure_info"}

    token = jwt.encode(payload, "secret", algorithm="HS256")
    decoded = jwt.decode(token, "secret", algorithms=["HS256"])

    assert decoded["data"] == "secure_info"
    # PyJWT converts the datetime to an integer Unix timestamp during encoding
    assert decoded["exp"] == int(future_date.timestamp())

def test_encode_decode_validates_past_datetime_nbf_claim():
    past_date = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    payload = {"nbf": past_date, "data": "secure_info"}

    token = jwt.encode(payload, "secret", algorithm="HS256")
    decoded = jwt.decode(token, "secret", algorithms=["HS256"])

    assert decoded["data"] == "secure_info"
    assert decoded["nbf"] == int(past_date.timestamp())

def test_encode_decode_preserves_integer_iat_claim():
    payload = {"iat": 1600000000}
    secret = "test-secret"

    token = jwt.encode(payload, secret, algorithm="HS256")
    decoded = jwt.decode(token, secret, algorithms=["HS256"])

    assert decoded["iat"] == 1600000000
    assert isinstance(decoded["iat"], int)

def test_decode_validates_matching_issuer_and_audience():
    payload = {
        "iss": "issuer-service",
        "aud": "my-app",
        "data": "secure-data"
    }
    secret = "test-secret"

    token = jwt.encode(payload, secret, algorithm="HS256")
    decoded = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer="issuer-service",
        audience="my-app"
    )

    assert decoded["iss"] == "issuer-service"
    assert decoded["aud"] == "my-app"
    assert decoded["data"] == "secure-data"

def test_encode_decode_preserves_subject_and_jti_claims():
    payload = {
        "sub": "user-999",
        "jti": "token-001"
    }
    secret = "test-secret"

    token = jwt.encode(payload, secret, algorithm="HS256")
    decoded = jwt.decode(token, secret, algorithms=["HS256"])

    assert decoded["sub"] == "user-999"
    assert decoded["jti"] == "token-001"

def test_get_unverified_header_extracts_custom_headers():
    payload = {"data": "test"}
    secret = "test-secret"
    custom_headers = {
        "kid": "k1",
        "typ": "JWT"
    }

    token = jwt.encode(payload, secret, algorithm="HS256", headers=custom_headers)
    unverified_header = jwt.get_unverified_header(token)

    assert unverified_header["kid"] == "k1"
    assert unverified_header["typ"] == "JWT"
    assert unverified_header["alg"] == "HS256"

def test_encode_decode_accepts_bytes_secret_key():
    payload = {"data": "test-bytes-key"}
    secret_key = b"secret-bytes"

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    decoded = jwt.decode(token, secret_key, algorithms=["HS256"])

    assert decoded["data"] == "test-bytes-key"

def test_get_unverified_header_and_decode_returns_header_and_payload_dict():
    payload = {"user": "test_user"}
    key = "secret_key"
    token = jwt.encode(payload, key, algorithm="HS256")

    header = jwt.get_unverified_header(token)
    decoded_payload = jwt.decode(token, key, algorithms=["HS256"])

    assert isinstance(header, dict)
    assert isinstance(decoded_payload, dict)
    assert header.get("alg") == "HS256"
    assert decoded_payload == payload

@pytest.mark.parametrize("algorithm", ["HS256", "HS512"])
def test_encode_decode_hmac_algorithms_roundtrip(algorithm):
    payload = {"action": "login", "user_id": 42}
    key = "secure-hmac-key"

    token = jwt.encode(payload, key, algorithm=algorithm)

    # In PyJWT 2.x, encode returns a string natively
    assert isinstance(token, str)

    decoded_payload = jwt.decode(token, key, algorithms=[algorithm])

    assert decoded_payload == payload

def test_encode_valid_payload_returns_signed_token_string():
    payload = {"sub": "1234567890", "name": "John Doe", "admin": True}
    key = "super-secret-key"
    algorithm = "HS256"

    token = jwt.encode(payload, key, algorithm=algorithm)

    assert isinstance(token, str)

    # Validate standard JWT structural compliance (3 base64url segments separated by periods)
    validation_regex = r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"
    assert re.match(validation_regex, token) is not None

def test_encode_with_custom_headers_incorporates_headers_in_token():
    custom_headers = {"kid": "key-2023-01", "custom_tenant": "acme-corp"}
    payload = {"user": "alice"}
    key = "secret"

    token = jwt.encode(payload, key, algorithm="HS256", headers=custom_headers)

    unverified_header = jwt.get_unverified_header(token)

    assert unverified_header["custom_tenant"] == "acme-corp"
    assert unverified_header["kid"] == "key-2023-01"
    assert unverified_header["alg"] == "HS256"

def test_encode_unserializable_payload_raises_type_error():
    key = "secret"
    algorithm = "HS256"

    payload_with_set = {"user_id": 123, "permissions": set(["read", "write"])}
    with pytest.raises(TypeError):
        jwt.encode(payload_with_set, key, algorithm=algorithm)

    payload_with_object = {"data": object()}
    with pytest.raises(TypeError):
        jwt.encode(payload_with_object, key, algorithm=algorithm)

def test_encode_unsupported_algorithm_raises_not_implemented_error():
    payload = {"test": "data"}
    key = "secret"

    with pytest.raises(NotImplementedError):
        jwt.encode(payload, key, algorithm="MAGIC-512")

    with pytest.raises(NotImplementedError):
        jwt.encode(payload, key, algorithm="HS999")

def test_decode_valid_token_returns_original_payload():
    payload = {
        "id": 42,
        "active": False,
        "roles": ["admin", "user"],
        "metadata": {"tier": "gold"},
        "unicode_name": "José 影師嗎"
    }
    key = "super-secret-256-bit-key"

    token = jwt.encode(payload, key, algorithm="HS256")
    decoded = jwt.decode(token, key, algorithms=["HS256"])

    assert decoded == payload

def test_decode_malformed_token_raises_decode_error():
    key = "secret"
    algorithms = ["HS256"]

    # Missing segments (only two parts)
    with pytest.raises(DecodeError):
        jwt.decode("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0", key, algorithms=algorithms)

    # Invalid base64url characters in the payload
    with pytest.raises(DecodeError):
        jwt.decode("eyJhbGciOiJIUzI1NiJ9.payload!@#invalid.signature", key, algorithms=algorithms)

    # Completely empty string
    with pytest.raises(DecodeError):
        jwt.decode("", key, algorithms=algorithms)

    # Non-string/non-bytes input
    with pytest.raises(DecodeError):
        jwt.decode(None, key, algorithms=algorithms)

def test_decode_tampered_signature_raises_invalid_signature_error():
    payload = {"test": "data"}
    token = jwt.encode(payload, "correct-secret-key", algorithm="HS256")

    # Wrong Key Scenario
    with pytest.raises(InvalidSignatureError):
        jwt.decode(token, "wrong-secret-key", algorithms=["HS256"])

    # Tampered Payload Scenario
    header_b64, payload_b64, sig_b64 = token.split(".")

    new_payload = b'{"user_id": 999999}'
    tampered_payload_b64 = base64.urlsafe_b64encode(new_payload).replace(b"=", b"").decode("utf-8")

    tampered_token = f"{header_b64}.{tampered_payload_b64}.{sig_b64}"

    with pytest.raises(InvalidSignatureError):
        jwt.decode(tampered_token, "correct-secret-key", algorithms=["HS256"])

def test_decode_unpermitted_algorithm_raises_invalid_algorithm_error():
    payload = {"test": "data"}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    # Token signed with symmetric algorithm "HS256", but decoded with ["RS256", "ES256"]
    with pytest.raises(InvalidAlgorithmError):
        jwt.decode(token, "secret", algorithms=["RS256", "ES256"])

    # Critical Security Edge Case: Token header manually altered to specify the "none" algorithm
    header = b'{"alg": "none"}'
    header_b64 = base64.urlsafe_b64encode(header).replace(b"=", b"").decode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(b'{"test": "data"}').replace(b"=", b"").decode("utf-8")
    none_token = f"{header_b64}.{payload_b64}."

    with pytest.raises(InvalidAlgorithmError):
        jwt.decode(none_token, "secret", algorithms=["HS256"])

SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"


def test_decode_exp_claim_validation_and_leeway():
    # Hardcoded past epoch: 1577836800 (Jan 1, 2020 00:00:00 UTC) with leeway=0
    token_hardcoded = jwt.encode({"exp": 1577836800}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token_hardcoded, SECRET_KEY, algorithms=[ALGORITHM], leeway=0)

    now = int(time.time())

    # Leeway Boundary: exactly 301 seconds in the past, decoded with leeway=300 (must raise)
    token_301_past = jwt.encode({"exp": now - 301}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token_301_past, SECRET_KEY, algorithms=[ALGORITHM], leeway=300)

    # Leeway Boundary: exactly 299 seconds in the past, decoded with leeway=300 (must succeed)
    token_299_past = jwt.encode({"exp": now - 299}, SECRET_KEY, algorithm=ALGORITHM)
    decoded = jwt.decode(token_299_past, SECRET_KEY, algorithms=[ALGORITHM], leeway=300)
    assert "exp" in decoded


def test_decode_nbf_claim_validation_and_leeway():
    # Hardcoded future epoch: 2524608000 (Jan 1, 2050 00:00:00 UTC) with leeway=0
    token_hardcoded = jwt.encode({"nbf": 2524608000}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(ImmatureSignatureError):
        jwt.decode(token_hardcoded, SECRET_KEY, algorithms=[ALGORITHM], leeway=0)

    now = int(time.time())

    # Leeway Boundary: exactly 61 seconds in the future, decoded with leeway=60 (must raise)
    token_61_future = jwt.encode({"nbf": now + 61}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(ImmatureSignatureError):
        jwt.decode(token_61_future, SECRET_KEY, algorithms=[ALGORITHM], leeway=60)

    # Leeway Boundary: exactly 59 seconds in the future, decoded with leeway=60 (must succeed)
    token_59_future = jwt.encode({"nbf": now + 59}, SECRET_KEY, algorithm=ALGORITHM)
    decoded = jwt.decode(token_59_future, SECRET_KEY, algorithms=[ALGORITHM], leeway=60)
    assert "nbf" in decoded


def test_decode_with_mismatched_audience_raises_invalid_audience_error():
    # Single audience string mismatch
    token_single_aud = jwt.encode(
        {"aud": "https://api.internal.example.com"}, SECRET_KEY, algorithm=ALGORITHM
    )
    with pytest.raises(InvalidAudienceError):
        jwt.decode(
            token_single_aud,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="https://api.external.example.com",
        )

    # List of audiences mismatch
    token_list_aud = jwt.encode(
        {"aud": ["mobile-app", "web-app"]}, SECRET_KEY, algorithm=ALGORITHM
    )
    with pytest.raises(InvalidAudienceError):
        jwt.decode(
            token_list_aud,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="desktop-app",
        )


def test_decode_with_mismatched_issuer_raises_invalid_issuer_error():
    token = jwt.encode(
        {"iss": "urn:auth:legacy-system:v1"}, SECRET_KEY, algorithm=ALGORITHM
    )
    with pytest.raises(InvalidIssuerError):
        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer="urn:auth:modern-system:v2",
        )


def test_decode_with_missing_required_claims_raises_missing_required_claim_error():
    token = jwt.encode(
        {"sub": "user123", "iat": 1600000000}, SECRET_KEY, algorithm=ALGORITHM
    )
    with pytest.raises(MissingRequiredClaimError):
        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )

def generate_rsa_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

def get_jwk_dict(private_key, kid):
    public_numbers = private_key.public_key().public_numbers()

    def int_to_base64url(n):
        b = n.to_bytes((n.bit_length() + 7) // 8, 'big')
        return base64.urlsafe_b64encode(b).decode('ascii').rstrip('=')

    return {
        "kty": "RSA",
        "kid": kid,
        "n": int_to_base64url(public_numbers.n),
        "e": int_to_base64url(public_numbers.e)
    }

def test_get_unverified_header_returns_header_without_signature_validation():
    private_key = generate_rsa_key()
    headers = {"alg": "RS256", "kid": "key-99-xyz", "custom_hdr": "test-value"}
    payload = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}

    token = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)

    # Corrupt the signature to prove validation is bypassed
    parts = token.split('.')
    corrupted_signature = parts[2][:-10] + "INVALIDXXX"
    corrupted_token = f"{parts[0]}.{parts[1]}.{corrupted_signature}"

    extracted_headers = jwt.get_unverified_header(corrupted_token)

    # PyJWT automatically adds the "typ": "JWT" header
    expected_headers = headers.copy()
    expected_headers["typ"] = "JWT"
    
    assert extracted_headers == expected_headers

def test_get_unverified_header_with_malformed_token_raises_decode_error():
    invalid_tokens = [
        "not_a_valid_token_string",
        "eyJhbGciOiJIUzI1NiJ9",
        "!!!invalid_base64!!!.eyJzdWIiOiIxMjMifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    ]

    for token in invalid_tokens:
        with pytest.raises(DecodeError):
            jwt.get_unverified_header(token)

def test_get_signing_key_from_jwt_with_valid_kid_returns_matching_public_key_via_jwks():
    key1 = generate_rsa_key()
    key2 = generate_rsa_key()

    jwk1 = get_jwk_dict(key1, "wrong-key-1")
    jwk2 = get_jwk_dict(key2, "target-key-2")

    jwks_payload = json.dumps({"keys": [jwk1, jwk2]}).encode('utf-8')

    # Hardcoded JWT string
    # Header: {"alg": "RS256", "kid": "target-key-2"}
    # Base64url encoded: eyJhbGciOiJSUzI1NiIsImtpZCI6InRhcmdldC1rZXktMiJ9
    # Changed "signature" to "signature123" to have valid base64 padding (length 12)
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InRhcmdldC1rZXktMiJ9.eyJzdWIiOiIxMjMifQ.signature123"

    mock_response = MagicMock()
    mock_response.read.return_value = jwks_payload
    mock_response.__enter__.return_value = mock_response

    with patch('urllib.request.urlopen', return_value=mock_response):
        client = jwt.PyJWKClient("https://example.com/.well-known/jwks.json")
        signing_key = client.get_signing_key_from_jwt(token)

        assert signing_key.key_id == "target-key-2"

        # Assert the returned public key mathematically corresponds to target-key-2
        public_numbers = signing_key.key.public_numbers()
        expected_n = key2.public_key().public_numbers().n
        expected_e = key2.public_key().public_numbers().e

        assert public_numbers.n == expected_n
        assert public_numbers.e == expected_e

def test_get_signing_key_from_jwt_with_caching_enabled_prevents_subsequent_network_requests():
    key = generate_rsa_key()
    jwk = get_jwk_dict(key, "cached-key-001")

    jwks_payload = json.dumps({"keys": [jwk]}).encode('utf-8')

    # Three distinct hardcoded JWT strings with different payloads but same header
    # Header: {"alg": "RS256", "kid": "cached-key-001"}
    # Base64url encoded: eyJhbGciOiJSUzI1NiIsImtpZCI6ImNhY2hlZC1rZXktMDAxIn0
    header_b64 = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImNhY2hlZC1rZXktMDAxIn0"

    token1 = f"{header_b64}.eyJzdWIiOiIxIn0.sig1"
    token2 = f"{header_b64}.eyJzdWIiOiIyIn0.sig2"
    token3 = f"{header_b64}.eyJzdWIiOiIzIn0.sig3"

    mock_response = MagicMock()
    mock_response.read.return_value = jwks_payload
    mock_response.__enter__.return_value = mock_response

    with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
        client = jwt.PyJWKClient("https://example.com/.well-known/jwks.json", cache_keys=True)

        client.get_signing_key_from_jwt(token1)
        client.get_signing_key_from_jwt(token2)
        client.get_signing_key_from_jwt(token3)

        assert mock_urlopen.call_count == 1
