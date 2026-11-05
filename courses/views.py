from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Course, Category, Enrollment
from learning.models import Lesson, LessonProgress
from goals.models import LearningActivity

def course_list_view(request):
    categories = Category.objects.annotate(course_count=Count('courses')).filter(courses__is_published=True).distinct()
    courses = Course.objects.filter(is_published=True).select_related('category').annotate(
        enrollment_count=Count('enrollments')
    )

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        courses = courses.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(instructor_name__icontains=q)
        )

    # Category filter
    selected_category = request.GET.get('category', '').strip()
    if selected_category and selected_category != 'all':
        courses = courses.filter(category__slug=selected_category)

    # Difficulty filter
    selected_difficulty = request.GET.get('difficulty', '').strip()
    if selected_difficulty and selected_difficulty != 'all':
        courses = courses.filter(difficulty__iexact=selected_difficulty)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'popularity':
        courses = courses.order_by('-enrollment_count', '-created_at')
    elif sort_by == 'title':
        courses = courses.order_by('title')
    else:  # newest
        courses = courses.order_by('-created_at')

    # Prepare enrolled course IDs for current user
    user_enrolled_course_ids = set()
    user_progress_map = {}
    if request.user.is_authenticated:
        user_enrolled_course_ids = set(
            Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
        )
        for course in courses:
            if course.id in user_enrolled_course_ids:
                user_progress_map[course.id] = course.get_user_progress(request.user)

    courses_data = []
    for course in courses:
        prog = user_progress_map.get(course.id, {'percentage': 0, 'completed': 0, 'total': course.lessons.count()})
        courses_data.append({
            'course': course,
            'is_enrolled': course.id in user_enrolled_course_ids,
            'progress': prog,
        })

    return render(request, 'courses/list.html', {
        'courses_data': courses_data,
        'categories': categories,
        'selected_category': selected_category,
        'selected_difficulty': selected_difficulty,
        'sort_by': sort_by,
        'q': q,
        'total_courses_count': courses.count(),
    })


def course_detail_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    lessons = course.lessons.all().order_by('lesson_order', 'id')
    is_enrolled = False
    progress_info = {'percentage': 0, 'completed': 0, 'total': lessons.count()}
    first_incomplete_lesson = None

    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
        if is_enrolled:
            progress_info = course.get_user_progress(request.user)
            completed_lesson_ids = set(
                LessonProgress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    is_completed=True
                ).values_list('lesson_id', flat=True)
            )
            # Find next incomplete lesson
            for lesson in lessons:
                if lesson.id not in completed_lesson_ids:
                    first_incomplete_lesson = lesson
                    break
            if not first_incomplete_lesson and lessons.exists():
                first_incomplete_lesson = lessons.first()

    return render(request, 'courses/detail.html', {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'progress_info': progress_info,
        'first_incomplete_lesson': first_incomplete_lesson,
        'objectives': course.get_objectives_list(),
    })


@login_required
def enroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if request.method == 'POST':
        enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
        if created:
            LearningActivity.objects.create(
                user=request.user,
                activity_type='ENROLL',
                reference_id=course.id,
                description=f"Enrolled in {course.title}"
            )
            messages.success(request, f"Successfully enrolled in '{course.title}'! Let's get started.")
        else:
            messages.info(request, f"You are already enrolled in '{course.title}'.")

        # Redirect to first lesson if available, otherwise course detail
        first_lesson = course.lessons.order_by('lesson_order').first()
        if first_lesson:
            return redirect('learning:lesson_detail', course_slug=course.slug, lesson_id=first_lesson.id)
        return redirect('courses:detail', slug=course.slug)

    return redirect('courses:detail', slug=course.slug)


@login_required
def unenroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        deleted_count, _ = Enrollment.objects.filter(user=request.user, course=course).delete()
        if deleted_count > 0:
            # Also clean up lesson progress for this course
            LessonProgress.objects.filter(user=request.user, lesson__course=course).delete()
            messages.info(request, f"You have unenrolled from '{course.title}'.")
        return redirect('courses:my_learning')
    return redirect('courses:detail', slug=course.slug)


@login_required
def my_learning_view(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course', 'course__category').order_by('-enrolled_at')
    
    enrolled_items = []
    filter_tab = request.GET.get('tab', 'all')  # all, in_progress, completed

    for enrollment in enrollments:
        course = enrollment.course
        progress = course.get_user_progress(request.user)
        
        # Find next lesson
        completed_ids = set(
            LessonProgress.objects.filter(
                user=request.user,
                lesson__course=course,
                is_completed=True
            ).values_list('lesson_id', flat=True)
        )
        next_lesson = course.lessons.exclude(id__in=completed_ids).order_by('lesson_order').first()
        if not next_lesson:
            next_lesson = course.lessons.order_by('lesson_order').first()

        is_completed = progress['total'] > 0 and progress['percentage'] == 100

        item = {
            'enrollment': enrollment,
            'course': course,
            'progress': progress,
            'next_lesson': next_lesson,
            'is_completed': is_completed,
        }

        if filter_tab == 'completed' and not is_completed:
            continue
        elif filter_tab == 'in_progress' and (is_completed or progress['total'] == 0):
            continue

        enrolled_items.append(item)

    return render(request, 'courses/my_learning.html', {
        'enrolled_items': enrolled_items,
        'active_tab': filter_tab,
        'total_enrolled': enrollments.count(),
    })
