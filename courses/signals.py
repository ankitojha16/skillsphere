from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.db import transaction
from .models import Course, Category, CourseModule, CourseAssessment
from learning.models import Lesson, Exercise

CACHE_KEYS_TO_CLEAR = [
    'skillsphere_published_categories',
    'skillsphere_course_catalogue_base',
]

def bump_catalogue_cache_version():
    """Bumps the global catalogue cache version to invalidate all parameterized catalogue queries in O(1)."""
    try:
        curr = cache.get('skillsphere_catalogue_version', 1)
        cache.set('skillsphere_catalogue_version', curr + 1, 86400 * 7)
    except Exception:
        import time
        cache.set('skillsphere_catalogue_version', int(time.time()), 86400 * 7)

def on_commit_delete(*keys):
    """
    Schedules cache deletion strictly after the current database transaction commits.
    If no transaction is active (autocommit mode), executes immediately.
    """
    keys_to_delete = [k for k in keys if k]
    if not keys_to_delete:
        return

    def do_delete():
        bump_catalogue_cache_version()
        for k in keys_to_delete:
            cache.delete(k)

    try:
        transaction.on_commit(do_delete)
    except Exception:
        # Fallback if called outside transaction context
        do_delete()

@receiver(pre_save, sender=Course)
def capture_original_course_slug(sender, instance, **kwargs):
    """Captures original slug to invalidate both old and new cache keys if slug changes."""
    if instance.pk:
        try:
            instance._original_slug = Course.objects.filter(pk=instance.pk).values_list('slug', flat=True).first()
        except Exception:
            instance._original_slug = None
    else:
        instance._original_slug = None

@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_cache(sender, **kwargs):
    on_commit_delete('skillsphere_published_categories')

@receiver(post_save, sender=Course)
@receiver(post_delete, sender=Course)
def invalidate_course_cache(sender, instance, **kwargs):
    keys = list(CACHE_KEYS_TO_CLEAR)
    if instance:
        if getattr(instance, '_original_slug', None) and instance._original_slug != instance.slug:
            keys.append(f'skillsphere_course_syllabus_{instance._original_slug}')
        if instance.slug:
            keys.append(f'skillsphere_course_syllabus_{instance.slug}')
    on_commit_delete(*keys)

@receiver(post_save, sender=CourseModule)
@receiver(post_delete, sender=CourseModule)
def invalidate_module_cache(sender, instance, **kwargs):
    keys = ['skillsphere_course_catalogue_base']
    try:
        if instance and instance.course and instance.course.slug:
            keys.append(f'skillsphere_course_syllabus_{instance.course.slug}')
    except Exception:
        pass
    on_commit_delete(*keys)

@receiver(post_save, sender=Lesson)
@receiver(post_delete, sender=Lesson)
def invalidate_lesson_cache(sender, instance, **kwargs):
    keys = ['skillsphere_course_catalogue_base']
    try:
        if instance and instance.course and instance.course.slug:
            keys.append(f'skillsphere_course_syllabus_{instance.course.slug}')
        if instance and instance.id:
            keys.append(f'lesson_notes_pdf_{instance.id}')
    except Exception:
        pass
    on_commit_delete(*keys)

@receiver(post_save, sender=CourseAssessment)
@receiver(post_delete, sender=CourseAssessment)
def invalidate_assessment_cache(sender, instance, **kwargs):
    keys = []
    try:
        if instance and instance.course and instance.course.slug:
            keys.append(f'skillsphere_course_syllabus_{instance.course.slug}')
    except Exception:
        pass
    on_commit_delete(*keys)

@receiver(post_save, sender=Exercise)
@receiver(post_delete, sender=Exercise)
def invalidate_exercise_cache(sender, instance, **kwargs):
    keys = []
    try:
        if instance and instance.lesson and instance.lesson.course and instance.lesson.course.slug:
            keys.append(f'skillsphere_course_syllabus_{instance.lesson.course.slug}')
    except Exception:
        pass
    on_commit_delete(*keys)
