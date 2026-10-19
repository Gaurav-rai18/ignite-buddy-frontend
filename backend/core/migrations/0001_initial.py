from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Broadcast', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('title', models.CharField(max_length=160)), ('message', models.TextField()), ('audience', models.CharField(default='All students', max_length=40)), ('created_at', models.DateTimeField(auto_now_add=True))], options={'ordering': ['-created_at']}),
        migrations.CreateModel(name='ScheduledLink', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('title', models.CharField(max_length=160)), ('onedrive_url', models.URLField(max_length=1000)), ('publish_at', models.DateTimeField()), ('created_at', models.DateTimeField(auto_now_add=True))], options={'ordering': ['publish_at']}),
        migrations.CreateModel(name='SiteSetting', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('key', models.CharField(max_length=80, unique=True)), ('value', models.CharField(default='false', max_length=200)), ('updated_at', models.DateTimeField(auto_now=True))]),
    ]
