# Generated by Django 5.1.6 on 2025-02-25 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bidding", "0002_auction_winner"),
    ]

    operations = [
        migrations.AddField(
            model_name="auction",
            name="closed",
            field=models.BooleanField(default=False),
        ),
    ]
