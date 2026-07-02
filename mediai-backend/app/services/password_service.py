"""Password hashing/verification (Module 4), using bcrypt directly.

Plaintext passwords are never stored or logged - only the bcrypt hash.
"""

import bcrypt


class PasswordService:
    def hash_password(self, plain_password: str) -> str:
        """Hash a plaintext password with a fresh bcrypt salt."""
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify a plaintext password against a stored bcrypt hash."""
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            # Malformed hash (shouldn't happen for hashes we generated ourselves).
            return False
