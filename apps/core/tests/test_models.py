import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )
        assert user.pk is not None
        assert user.email == 'test@example.com'
        assert str(user) == 'testuser'

    def test_user_optional_fields(self):
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            phone='+79991234567',
        )
        assert user.phone == '+79991234567'
        assert user.avatar is None or not user.avatar
