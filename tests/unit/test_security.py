"""
Unit tests for security module (password hashing).
"""

from app.core.security import hash_password, verify_password, validate_password_strength


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a valid hash."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_hashes(self):
        """Test that same password generates different hashes (salt)."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Due to salt, hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False


class TestPasswordValidation:
    """Test password strength validation."""

    def test_validate_password_valid(self):
        """Test validation of strong password."""
        is_valid, error = validate_password_strength("SecurePass123")
        assert is_valid is True
        assert error == ""

        is_valid, error = validate_password_strength("MyP@ssw0rd!")
        assert is_valid is True
        assert error == ""

    def test_validate_password_too_short(self):
        """Test validation rejects too short password."""
        is_valid, error = validate_password_strength("Short1")
        assert is_valid is False
        assert "at least 8 characters" in error

    def test_validate_password_no_digit(self):
        """Test validation rejects password without digit."""
        is_valid, error = validate_password_strength("NoDigitsHere")
        assert is_valid is False
        assert "at least one digit" in error

    def test_validate_password_no_uppercase(self):
        """Test validation rejects password without uppercase letter."""
        is_valid, error = validate_password_strength("lowercase123")
        assert is_valid is False
        assert "uppercase" in error

    def test_validate_password_no_lowercase(self):
        """Test validation rejects password without lowercase letter."""
        is_valid, error = validate_password_strength("UPPERCASE123")
        assert is_valid is False
        assert "lowercase" in error

    def test_validate_password_empty(self):
        """Test validation rejects empty password."""
        is_valid, error = validate_password_strength("")
        assert is_valid is False
        assert "at least 8 characters" in error

    def test_validate_password_whitespace_only(self):
        """Test validation rejects whitespace-only password."""
        is_valid, error = validate_password_strength("        ")
        assert is_valid is False
        # Whitespace doesn't contain letters or digits
        assert error != ""
