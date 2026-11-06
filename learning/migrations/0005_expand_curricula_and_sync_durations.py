from django.db import migrations
import json

def expand_curricula_and_sync_durations(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    CourseModule = apps.get_model('courses', 'CourseModule')
    CourseAssessment = apps.get_model('courses', 'CourseAssessment')
    CourseAssessmentQuestion = apps.get_model('courses', 'CourseAssessmentQuestion')
    Lesson = apps.get_model('learning', 'Lesson')
    Exercise = apps.get_model('learning', 'Exercise')

    from courses.curriculum_data import COURSES_CURRICULUM

    # Ensure all courses have a realistic, authentic 4 hours duration
    Course.objects.all().update(estimated_duration='4 hours')

    for slug, cdata in COURSES_CURRICULUM.items():
        course = Course.objects.filter(slug=slug).first()
        if not course:
            continue

        # 1. Populate Modules and Lessons
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
                v_url = l_info.get('video_url', '')
                if 'watch?v=' in v_url:
                    vid = v_url.split('watch?v=')[-1].split('&')[0]
                    v_url = f'https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0'
                elif 'youtu.be/' in v_url:
                    vid = v_url.split('youtu.be/')[-1].split('?')[0]
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
                        'video_type': 'optional',
                        'content': l_info['content'].strip(),
                        'key_takeaways': json.dumps(l_info.get('key_takeaways', [])),
                        'common_mistakes': json.dumps(l_info.get('common_mistakes', [])),
                        'external_resources': l_info.get('resources', '').strip(),
                    }
                )

                ex_info = l_info.get('exercise')
                if ex_info:
                    Exercise.objects.update_or_create(
                        lesson=lesson,
                        title=ex_info['title'],
                        defaults={
                            'instructions': ex_info['instructions'],
                            'starter_code': ex_info['starter_code'],
                            'expected_output': ex_info['expected_output'],
                            'hint': ex_info.get('hints', ''),
                            'order': 1
                        }
                    )

        # 2. Populate Assessments
        for a_info in cdata.get('assessments', []):
            assessment, _ = CourseAssessment.objects.update_or_create(
                course=course,
                assessment_type=a_info['type'],
                defaults={
                    'title': a_info.get('title', f"{course.title} - {a_info['type']}"),
                    'description': a_info.get('description', ''),
                    'duration_minutes': a_info.get('duration', 30),
                    'passing_percentage': a_info.get('pass_pct', 70),
                    'is_active': True,
                }
            )

            for q_idx, q_info in enumerate(a_info.get('questions', []), start=1):
                CourseAssessmentQuestion.objects.update_or_create(
                    assessment=assessment,
                    order=q_idx,
                    defaults={
                        'question_text': q_info.get('text', ''),
                        'topic': q_info.get('topic', 'Core Concepts'),
                        'option_a': q_info.get('a', ''),
                        'option_b': q_info.get('b', ''),
                        'option_c': q_info.get('c', ''),
                        'option_d': q_info.get('d', ''),
                        'correct_answer': q_info.get('correct', 'A'),
                        'explanation': q_info.get('explanation', ''),
                    }
                )


def reverse_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0004_populate_all_expanded_curricula'),
        ('courses', '0002_courseassessment_coursemodule_and_more'),
    ]

    operations = [
        migrations.RunPython(expand_curricula_and_sync_durations, reverse_migration),
    ]
