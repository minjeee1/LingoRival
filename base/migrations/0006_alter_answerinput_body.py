# Generated by Django 4.2.5 on 2023-09-25 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0005_remove_answerinput_evaluation_results_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="answerinput",
            name="body",
            field=models.TextField(blank=True, null=True),
        ),
    ]
