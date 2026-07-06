from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='GameRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=8, unique=True)),
                ('player_x_name', models.CharField(blank=True, max_length=80)),
                ('player_o_name', models.CharField(blank=True, max_length=80)),
                ('board', models.JSONField(default=list)),
                ('current_player', models.CharField(default='X', max_length=1)),
                ('winner', models.CharField(blank=True, max_length=10)),
                ('status', models.CharField(default='Aguardando jogadores', max_length=80)),
                ('started', models.BooleanField(default=False)),
                ('rematch_requests', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
