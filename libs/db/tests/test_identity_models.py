"""Tests for Identity domain models: User, Division, OAuthSession."""

from sqlalchemy.orm import Session

from skillhub_db.models.division import Division
from skillhub_db.models.oauth_session import OAuthSession
from skillhub_db.models.user import User


class TestDivision:
    def test_division_slug_is_primary_key(self, db: Session):
        div = Division(slug="eng", name="Engineering")
        db.add(div)
        db.commit()
        assert db.get(Division, "eng") is not None

    def test_division_repr(self):
        div = Division(slug="eng", name="Engineering")
        assert repr(div) == "<Division 'eng'>"


class TestUser:
    def test_user_instantiates_with_required_fields(self, db: Session, division):
        u = User(
            email="alice@acme.com",
            username="alice",
            name="Alice Smith",
            division="engineering-org",
            role="Engineer",
        )
        db.add(u)
        db.commit()
        assert u.id is not None
        assert u.email == "alice@acme.com"
        assert u.is_platform_team is False
        assert u.is_security_team is False

    def test_user_email_unique(self, db: Session, user):
        u2 = User(
            email="test@acme.com",
            username="other",
            name="Other",
            division="engineering-org",
            role="Eng",
        )
        db.add(u2)
        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db.commit()

    def test_user_defaults(self, db: Session, division):
        u = User(
            email="default@acme.com",
            username="default",
            name="Default",
            division="engineering-org",
            role="Eng",
        )
        db.add(u)
        db.commit()
        assert u.is_platform_team is False
        assert u.is_security_team is False
        assert u.oauth_provider is None


class TestOAuthSession:
    def test_oauth_session_has_user_foreign_key(self, db: Session, user):
        session = OAuthSession(
            user_id=user.id,
            provider="microsoft",
            access_token_hash="abc123hash",
        )
        db.add(session)
        db.commit()
        assert session.user_id == user.id

    def test_oauth_session_stores_hash_not_token(self, db: Session, user):
        session = OAuthSession(
            user_id=user.id,
            provider="google",
            access_token_hash="hashed_value",
        )
        db.add(session)
        db.commit()
        # access_token_hash is the stored field, not raw token
        assert session.access_token_hash == "hashed_value"
