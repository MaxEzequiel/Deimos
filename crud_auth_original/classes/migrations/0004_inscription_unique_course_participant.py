from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("classes", "0003_alter_course_name")]
    operations = [migrations.AddConstraint(model_name="inscription", constraint=models.UniqueConstraint(fields=("course", "participant"), name="unique_course_participant"))]
