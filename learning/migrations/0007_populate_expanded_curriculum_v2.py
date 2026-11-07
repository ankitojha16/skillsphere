from django.db import migrations
import json

def populate_expanded_curriculum_v2(apps, schema_editor):
    Category = apps.get_model('courses', 'Category')
    Course = apps.get_model('courses', 'Course')
    CourseModule = apps.get_model('courses', 'CourseModule')
    CourseAssessment = apps.get_model('courses', 'CourseAssessment')
    CourseAssessmentQuestion = apps.get_model('courses', 'CourseAssessmentQuestion')
    Lesson = apps.get_model('learning', 'Lesson')
    Exercise = apps.get_model('learning', 'Exercise')

    from courses.curriculum_data import COURSES_CURRICULUM
    from courses.curriculum_expansion_full import NEW_COURSES_DATA

    # In clean test runner databases, let tests define their own category fixtures
    if not Category.objects.exists():
        return

    # Categories mapping
    categories_map = {cat.slug: cat for cat in Category.objects.all()}
    fallback_cat = categories_map.get('programming') or Category.objects.first()

    # Ensure 4 new courses exist
    for c_info in NEW_COURSES_DATA:
        cat = categories_map.get(c_info['category']) or fallback_cat
        Course.objects.update_or_create(
            slug=c_info['slug'],
            defaults={
                'title': c_info['title'],
                'category': cat,
                'difficulty': c_info['difficulty'],
                'instructor_name': c_info['instructor_name'],
                'instructor_title': c_info['instructor_title'],
                'estimated_duration': c_info['estimated_duration'],
                'thumbnail_url': c_info['thumbnail_url'],
                'description': c_info['description'],
                'short_description': c_info['short_description'],
                'learning_objectives': c_info['learning_objectives'],
                'is_published': True,
                'curriculum_version': 2,
                'legacy_total_lessons': 4,
            }
        )

    # Update existing courses to curriculum_version=2 and legacy_total_lessons=4
    Course.objects.all().update(curriculum_version=2, legacy_total_lessons=4)

    # Populate 16 lessons, 4 modules, exercises, and assessments for all 12 courses
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

                l_order = l_info['order']
                lesson_curr_version = 1 if l_order <= 4 else 2

                lesson, _ = Lesson.objects.update_or_create(
                    course=course,
                    lesson_order=l_order,
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
                        'curriculum_version': lesson_curr_version,
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
        assessments_data = cdata.get('assessments', [])
        if isinstance(assessments_data, dict):
            temp = []
            for a_type, a_val in assessments_data.items():
                val = dict(a_val)
                val['type'] = a_type
                temp.append(val)
            assessments_data = temp

        for a_info in assessments_data:
            assessment, _ = CourseAssessment.objects.update_or_create(
                course=course,
                assessment_type=a_info.get('type') or a_info.get('assessment_type'),
                defaults={
                    'title': a_info.get('title', f"{course.title} - {a_info.get('type')}"),
                    'description': a_info.get('description', ''),
                    'duration_minutes': a_info.get('duration_minutes') or a_info.get('duration', 30),
                    'passing_percentage': a_info.get('passing_percentage') or a_info.get('pass_pct', 70),
                    'is_active': True,
                }
            )

            for q_idx, q_info in enumerate(a_info.get('questions', []), start=1):
                CourseAssessmentQuestion.objects.update_or_create(
                    assessment=assessment,
                    order=q_idx,
                    defaults={
                        'question_text': q_info.get('question_text') or q_info.get('text', ''),
                        'topic': q_info.get('topic', 'Core Concepts'),
                        'option_a': q_info.get('option_a') or q_info.get('a', ''),
                        'option_b': q_info.get('option_b') or q_info.get('b', ''),
                        'option_c': q_info.get('option_c') or q_info.get('c', ''),
                        'option_d': q_info.get('option_d') or q_info.get('d', ''),
                        'correct_answer': q_info.get('correct_answer') or q_info.get('correct', 'A'),
                        'explanation': q_info.get('explanation', ''),
                    }
                )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_course_curriculum_version_and_more'),
        ('learning', '0006_lesson_curriculum_version'),
    ]

    operations = [
        migrations.RunPython(populate_expanded_curriculum_v2, reverse_code=noop_reverse),
    ]
