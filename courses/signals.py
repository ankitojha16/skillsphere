from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course, Category, CourseModule
from learning.models import Lesson

CACHE_KEYS_TO_CLEAR = [
    'skillsphere_published_categories',
    'skillsphere_course_catalogue_base',
]

@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_cache(sender, **kwargs):
    cache.delete('skillsphere_published_categories')

@receiver(post_save, sender=Course)
@receiver(post_delete, sender=Course)
def invalidate_course_cache(sender, instance, **kwargs):
    for k in CACHE_KEYS_TO_CLEAR:
        cache.delete(k)
    if instance and instance.slug:
        cache.delete(f'skillsphere_course_syllabus_{instance.slug}')

@receiver(post_save, sender=CourseModule)
@receiver(post_delete, sender=CourseModule)
def invalidate_module_cache(sender, instance, **kwargs):
    if instance and instance.course and instance.course.slug:
        cache.delete(f'skillsphere_course_syllabus_{instance.course.slug}')

@receiver(post_save, sender=Lesson)
@receiver(post_delete, sender=Lesson)
def invalidate_lesson_cache(sender, instance, **kwargs):
    if instance and instance.course and instance.course.slug:
        cache.delete(f'skillsphere_course_syllabus_{instance.course.slug}')
    cache.delete('skillsphere_course_catalogue_base')
