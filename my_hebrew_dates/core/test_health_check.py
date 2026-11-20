from http import HTTPStatus

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_check_is_public_and_healthy(client):
    response = client.get(reverse("health_check"))

    assert response.status_code == HTTPStatus.OK
