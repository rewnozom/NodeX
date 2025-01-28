# ai_agent/utils/tokens.py
"""
ai_agent/utils/tokens.py - Token handling utilities
"""

import secrets
import jwt
from typing import Optional, Dict, List

def generate_token(length: int = 32) -> str:
    """Generate a random token of specified length"""
    return secrets.token_urlsafe(length)

def create_jwt_token(payload: Dict[str, any], secret_key: str, algorithm: str = 'HS256') -> str:
    """Create a JWT token with the given payload and secret key"""
    return jwt.encode(payload, secret_key, algorithm=algorithm)

def decode_jwt_token(token: str, secret_key: str, algorithms: List[str] = ['HS256']) -> Dict[str, any]:
    """Decode a JWT token and return the payload"""
    return jwt.decode(token, secret_key, algorithms=algorithms)