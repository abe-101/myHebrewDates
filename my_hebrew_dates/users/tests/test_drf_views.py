from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIRequestFactory

from my_hebrew_dates.users.api.views import UserViewSet

if TYPE_CHECKING:
    from my_hebrew_dates.users.models import User


class TestUserViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_get_queryset(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request  # type: ignore[assignment]

        assert user in view.get_queryset()

    def test_me(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request  # type: ignore[assignment]

        response = view.me(request)

        assert response.data == {
            "username": user.username,
            "url": f"http://testserver/api/users/{user.username}/",
            "name": user.name,
        }
