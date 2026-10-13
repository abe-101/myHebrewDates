# ruff: noqa: FBT001
from factory import Faker
from factory import post_generation
from factory.django import DjangoModelFactory

from my_hebrew_dates.users.models import User


class UserFactory(DjangoModelFactory[User]):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(
        user: User,  # noqa: N805
        create: bool,
        extracted: str | None,
        **kwargs,
    ):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        user.set_password(password)
        if create:
            user.save()

    class Meta:
        model = User
        django_get_or_create = ["username"]
        skip_postgeneration_save = True
