from django.db import migrations
import json

def seed_expanded_curriculum_and_normalize_videos(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    CourseModule = apps.get_model('courses', 'CourseModule')
    Lesson = apps.get_model('learning', 'Lesson')
    Exercise = apps.get_model('learning', 'Exercise')

    # 1. Normalize all existing lesson video URLs
    for lesson in Lesson.objects.all():
        url = (lesson.video_url or '').strip()
        if not url:
            continue
        new_url = url
        if 'watch?v=' in url:
            vid = url.split('watch?v=')[-1].split('&')[0]
            new_url = f'https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0'
        elif 'youtu.be/' in url:
            vid = url.split('youtu.be/')[-1].split('?')[0]
            new_url = f'https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0'
        elif 'youtube.com/embed/' in url and 'enablejsapi=1' not in url:
            delim = '&' if '?' in url else '?'
            new_url = f'{url}{delim}enablejsapi=1&rel=0'

        if new_url != url:
            lesson.video_url = new_url
            lesson.save(update_fields=['video_url'])

    # 2. Seed all curriculum data from COURSES_CURRICULUM
    from courses.curriculum_data import COURSES_CURRICULUM
    for slug, cdata in COURSES_CURRICULUM.items():
        course = Course.objects.filter(slug=slug).first()
        if not course:
            continue

        for m_info in cdata.get('modules', []):
            module, _ = CourseModule.objects.update_or_create(
                course=course,
                order=m_info['order'],
                defaults={
                    'title': m_info['title'],
                    'description': m_info.get('description', '')
                }
            )

            for l_info in m_info.get('lessons', []):
                # Ensure embed URL format
                v_url = l_info.get('video_url', '')
                if 'watch?v=' in v_url:
                    vid = v_url.split('watch?v=')[-1].split('&')[0]
                    v_url = f'https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0'

                lesson, _ = Lesson.objects.update_or_create(
                    course=course,
                    lesson_order=l_info['order'],
                    defaults={
                        'module': module,
                        'chapter_name': l_info.get('chapter', module.title),
                        'title': l_info['title'],
                        'estimated_minutes': l_info.get('minutes', 20),
                        'video_url': v_url,
                        'video_duration_seconds': l_info.get('video_duration', 600),
                        'video_type': 'youtube',
                        'content': l_info['content'].strip(),
                        'key_takeaways': json.dumps(l_info.get('key_takeaways', [])),
                        'common_mistakes': json.dumps(l_info.get('common_mistakes', [])),
                        'external_resources': l_info.get('resources', '').strip()
                    }
                )

                if 'exercise' in l_info:
                    ex_info = l_info['exercise']
                    Exercise.objects.update_or_create(
                        lesson=lesson,
                        title=ex_info['title'],
                        defaults={
                            'instructions': ex_info['instructions'],
                            'starter_code': ex_info['starter_code'],
                            'expected_output': ex_info['expected_output'],
                            'hint': ex_info.get('hints', '')
                        }
                    )

def reverse_sync(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0002_assignment_exercise_lesson_common_mistakes_and_more'),
        ('courses', '0002_courseassessment_coursemodule_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_expanded_curriculum_and_normalize_videos, reverse_sync),
    ]
