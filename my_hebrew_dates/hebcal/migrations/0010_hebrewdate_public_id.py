import shortuuid.django_fields
from django.db import migrations


def fill_public_ids(apps, schema_editor):
    HebrewDate = apps.get_model("hebcal", "HebrewDate")
    field = HebrewDate._meta.get_field("public_id")
    for hebrew_date in HebrewDate.objects.all():
        hebrew_date.public_id = field._generate_uuid()
        hebrew_date.save(update_fields=["public_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("hebcal", "0009_alter_calendar_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="hebrewdate",
            name="public_id",
            field=shortuuid.django_fields.ShortUUIDField(
                alphabet=None,
                editable=False,
                length=10,
                max_length=10,
                null=True,
                prefix="",
            ),
        ),
        migrations.RunPython(fill_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="hebrewdate",
            name="public_id",
            field=shortuuid.django_fields.ShortUUIDField(
                alphabet=None,
                editable=False,
                length=10,
                max_length=10,
                prefix="",
                unique=True,
            ),
        ),
    ]
