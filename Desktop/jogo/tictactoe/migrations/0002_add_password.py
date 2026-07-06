from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tictactoe', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameroom',
            name='password',
            field=models.CharField(blank=True, max_length=128, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gameroom',
            name='winning_line',
            field=models.JSONField(blank=True, default=list),
            preserve_default=False,
        ),
    ]
