from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_package_packageitem"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="productcategory",
            name="shop",
        ),
        migrations.RemoveField(
            model_name="product",
            name="shop",
        ),
        migrations.RemoveField(
            model_name="package",
            name="shop",
        ),
    ]
