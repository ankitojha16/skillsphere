from django.db import migrations
import re

def clean_course_titles(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Category = apps.get_model('courses', 'Category')

    degree_pattern = re.compile(r'\s*\((?:BTech|MTech|BBA|MBA|BCA|BSc|BCom|BA)(?:[/\s\w]*)\)', re.IGNORECASE)

    for cat in Category.objects.all():
        cleaned_cat = degree_pattern.sub('', cat.name).strip()
        if cleaned_cat != cat.name:
            cat.name = cleaned_cat
            cat.save(update_fields=['name'])

    for course in Course.objects.all():
        cleaned_title = degree_pattern.sub('', course.title).strip()
        if cleaned_title != course.title:
            course.title = cleaned_title
            course.save(update_fields=['title'])

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_course_prerequisites_and_more'),
    ]

    operations = [
        migrations.RunPython(clean_course_titles, reverse_code=migrations.RunPython.noop),
    ]
