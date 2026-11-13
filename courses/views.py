import json
import logging
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core.cache import cache
from .models import (
    Course, Category, Enrollment, CourseModule,
    CourseAssessment, CourseAssessmentQuestion,
    CourseAssessmentAttempt, CourseCompletion,
    CourseBookmark, CourseReview
)
from learning.models import Lesson, LessonProgress, Exercise, LessonBookmark
from goals.models import LearningActivity
from analytics.services import track_event

logger = logging.getLogger('skillsphere.courses')

def course_search_autocomplete_api(request):
    """
    Sub-second search suggestions API with debounced live querying.
    Returns JSON array of top 6 matching courses with metadata.
    """
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    cache_key = f"course_autocomplete_{q.lower()[:32]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached})

    matches = Course.objects.filter(is_published=True).filter(
        Q(title__icontains=q) |
        Q(instructor_name__icontains=q) |
        Q(category__name__icontains=q)
    ).select_related('category')[:6]

    results = []
    for c in matches:
        results.append({
            'title': c.title,
            'slug': c.slug,
            'url': reverse('courses:detail', kwargs={'slug': c.slug}),
            'instructor': c.instructor_name,
            'category': c.category.name if c.category else 'General',
            'difficulty': c.difficulty,
            'thumbnail': c.get_thumbnail_url(),
        })

    cache.set(cache_key, results, 300)
    return JsonResponse({'results': results})

def course_list_view(request):
    # Tier-1 In-memory cache for public category metadata (15 mins TTL)
    categories = cache.get('skillsphere_published_categories')
    if categories is None:
        categories = list(
            Category.objects.annotate(course_count=Count('courses', distinct=True))
            .filter(courses__is_published=True)
            .distinct()
        )
        cache.set('skillsphere_published_categories', categories, 900)

    # Base courses queryset with annotated total_lessons, enrollment_count, and real rating metrics
    courses = Course.objects.filter(is_published=True).select_related('category').annotate(
        enrollment_count=Count('enrollments', distinct=True),
        total_lessons=Count('lessons', distinct=True),
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        reviews_count=Count('reviews', filter=Q(reviews__is_approved=True), distinct=True)
    )

    # Search filter (by title, description, instructor, category topic, objectives)
    q = request.GET.get('q', '').strip()
    if q:
        courses = courses.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(instructor_name__icontains=q) |
            Q(category__name__icontains=q) |
            Q(learning_objectives__icontains=q)
        )

    # Category filter
    selected_category = request.GET.get('category', '').strip()
    if selected_category and selected_category != 'all':
        courses = courses.filter(category__slug=selected_category)

    # Degree filter (BBA, MBA, BTech, MTech, BCA, BSc, BA, BCom)
    selected_degree = request.GET.get('degree', '').strip()
    available_degrees = [
        {'code': 'BBA', 'label': 'BBA'},
        {'code': 'MBA', 'label': 'MBA'},
        {'code': 'BTech', 'label': 'B.Tech'},
        {'code': 'MTech', 'label': 'M.Tech'},
        {'code': 'BCA', 'label': 'BCA'},
        {'code': 'BSc', 'label': 'B.Sc'},
        {'code': 'BCom', 'label': 'B.Com'},
        {'code': 'BA', 'label': 'BA'},
    ]
    if selected_degree and selected_degree.lower() != 'all':
        deg_upper = selected_degree.upper()
        if deg_upper == 'BBA':
            courses = courses.filter(Q(title__icontains='BBA') | Q(description__icontains='BBA') | Q(category__slug='management-business'))
        elif deg_upper == 'MBA':
            courses = courses.filter(Q(title__icontains='MBA') | Q(description__icontains='MBA') | Q(category__slug='management-business'))
        elif deg_upper in ['BTECH', 'B.TECH']:
            courses = courses.filter(Q(title__icontains='BTech') | Q(description__icontains='BTech') | Q(category__slug='engineering-tech'))
        elif deg_upper in ['MTECH', 'M.TECH']:
            courses = courses.filter(Q(title__icontains='MTech') | Q(description__icontains='MTech') | Q(category__slug='engineering-tech'))
        elif deg_upper == 'BCA':
            courses = courses.filter(Q(title__icontains='BCA') | Q(description__icontains='BCA') | Q(category__slug='computer-applications'))
        elif deg_upper in ['BSC', 'B.SC']:
            courses = courses.filter(Q(title__icontains='BSc') | Q(description__icontains='BSc') | Q(category__slug='applied-sciences'))
        elif deg_upper in ['BCOM', 'B.COM']:
            courses = courses.filter(Q(title__icontains='BCom') | Q(description__icontains='BCom') | Q(category__slug='commerce-finance'))
        elif deg_upper == 'BA':
            courses = courses.filter(Q(title__icontains='(BA)') | Q(description__icontains='(BA)') | Q(category__slug='humanities-arts'))
        else:
            courses = courses.filter(
                Q(title__icontains=selected_degree) |
                Q(description__icontains=selected_degree) |
                Q(learning_objectives__icontains=selected_degree)
            )

    # Difficulty filter
    selected_difficulty = request.GET.get('difficulty', '').strip()
    if selected_difficulty and selected_difficulty != 'all':
        courses = courses.filter(difficulty__iexact=selected_difficulty)

    # Sorting (newest, popularity, duration, rating, title)
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'popularity':
        courses = courses.order_by('-enrollment_count', '-created_at')
    elif sort_by == 'duration':
        courses = courses.order_by('estimated_duration', 'title')
    elif sort_by == 'rating':
        courses = courses.order_by('-avg_rating', '-reviews_count', '-created_at')
    elif sort_by == 'title':
        courses = courses.order_by('title')
    else:
        courses = courses.order_by('-created_at')
    import hashlib
    cat_ver = cache.get('skillsphere_catalogue_version', 1)
    q_hash = hashlib.md5(q.lower().encode('utf-8')).hexdigest()[:12] if q else 'none'
    catalogue_cache_key = (
        f"skillsphere_cat_list_v{cat_ver}_"
        f"{selected_category or 'all'}_"
        f"{selected_degree or 'all'}_"
        f"{selected_difficulty or 'all'}_"
        f"{sort_by}_{q_hash}"
    )
    cached_courses = cache.get(catalogue_cache_key)
    if cached_courses is not None:
        courses_list = cached_courses
    else:
        courses_list = list(courses)
        cache.set(catalogue_cache_key, courses_list, 600)  # 10 minutes TTL

    total_courses_count = len(courses_list)

    # Prepare enrolled course IDs and batch fetch progress for authenticated user
    user_enrolled_course_ids = set()
    user_bookmarked_course_ids = set()
    user_progress_map = {}
    if request.user.is_authenticated:
        user_enrolled_course_ids = set(
            Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
        )
        user_bookmarked_course_ids = set(
            CourseBookmark.objects.filter(user=request.user).values_list('course_id', flat=True)
        )
        if user_enrolled_course_ids:
            # Batch fetch completions and lesson progress in 2 fast queries instead of 40+ per-course loops
            completions = {
                c.course_id: c
                for c in CourseCompletion.objects.filter(
                    user=request.user,
                    course_id__in=user_enrolled_course_ids
                )
            }
            lesson_progress_counts = dict(
                LessonProgress.objects.filter(
                    user=request.user,
                    is_completed=True,
                    lesson__course_id__in=user_enrolled_course_ids
                ).values('lesson__course_id').annotate(cnt=Count('id')).values_list('lesson__course_id', 'cnt')
            )
            for c_id in user_enrolled_course_ids:
                comp = completions.get(c_id)
                comp_lessons = lesson_progress_counts.get(c_id, 0)
                if comp:
                    user_progress_map[c_id] = {
                        'percentage': comp.learning_progress,
                        'completed': comp_lessons,
                        'is_completed': comp.is_completed,
                    }
                else:
                    user_progress_map[c_id] = {
                        'percentage': 0,
                        'completed': comp_lessons,
                        'is_completed': False,
                    }

    courses_data = []
    for course in courses_list:
        is_enrolled = course.id in user_enrolled_course_ids
        is_bookmarked = course.id in user_bookmarked_course_ids
        total_lessons = getattr(course, 'total_lessons', None) or course.total_lessons_count

        if is_enrolled and course.id in user_progress_map:
            cached_prog = user_progress_map[course.id]
            pct = cached_prog.get('percentage', 0)
            comp_count = cached_prog.get('completed', 0)
            is_comp = cached_prog.get('is_completed', False)
            if comp_count > 0 and total_lessons > 0:
                calc_pct = min(100, int(round((comp_count / total_lessons) * 100)))
                pct = max(pct, calc_pct)
            if pct >= 100 or (comp_count >= total_lessons and total_lessons > 0):
                pct = 100
                is_comp = True
            prog = {
                'percentage': pct,
                'completed': comp_count,
                'total': total_lessons,
                'is_completed': is_comp,
            }
        else:
            prog = {
                'percentage': 0,
                'completed': 0,
                'total': total_lessons,
                'is_completed': False
            }

        # Strict 4-State Enrollment Logic:
        # 1. Logged-out -> 'logged_out' ("Log In to Enroll")
        # 2. Logged-in not enrolled -> 'not_enrolled' ("Enroll")
        # 3. Enrolled 100% complete -> 'completed' ("Review Course")
        # 4. Enrolled in progress -> 'in_progress' ("Continue Learning")
        if not request.user.is_authenticated:
            enrollment_state = 'logged_out'
        elif not is_enrolled:
            enrollment_state = 'not_enrolled'
        elif prog.get('percentage', 0) == 100 or prog.get('is_completed', False):
            enrollment_state = 'completed'
        else:
            enrollment_state = 'in_progress'

        courses_data.append({
            'course': course,
            'is_enrolled': is_enrolled,
            'is_bookmarked': is_bookmarked,
            'progress': prog,
            'enrollment_state': enrollment_state,
            'avg_rating': getattr(course, 'avg_rating', None),
            'reviews_count': getattr(course, 'reviews_count', 0),
        })

    # Milestone 4.1: High-Performance Catalogue Pagination (16 courses per page)
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(courses_data, 16)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    elided_page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)

    # Preserve all active query parameters across pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_querystring = query_params.urlencode()

    return render(request, 'courses/list.html', {
        'courses_data': page_obj,
        'page_obj': page_obj,
        'elided_page_range': elided_page_range,
        'pagination_querystring': pagination_querystring,
        'categories': categories,
        'selected_category': selected_category,
        'selected_degree': selected_degree,
        'available_degrees': available_degrees,
        'selected_difficulty': selected_difficulty,
        'sort_by': sort_by,
        'q': q,
        'total_courses_count': total_courses_count,
    })


def course_detail_view(request, slug):
    syllabus_cache_key = f'skillsphere_course_syllabus_{slug}'
    syllabus = cache.get(syllabus_cache_key)
    if not syllabus:
        course = get_object_or_404(
            Course.objects.filter(is_published=True)
            .select_related('category')
            .annotate(total_lessons=Count('lessons', distinct=True)),
            slug=slug
        )
        lessons = list(course.lessons.all().order_by('lesson_order', 'id'))
        modules = list(course.modules.prefetch_related('lessons').order_by('order'))
        assessments = list(course.course_assessments.filter(is_active=True).order_by('assessment_type'))

        # Pre-calculate lessons with exercises in 1 query to avoid N+1 queries in template
        lesson_ids_with_exercises = set(
            Exercise.objects.filter(lesson__course=course).values_list('lesson_id', flat=True)
        )
        syllabus = {
            'course': course,
            'lessons': lessons,
            'modules': modules,
            'assessments': assessments,
            'lesson_ids_with_exercises': lesson_ids_with_exercises,
            'total_lessons': getattr(course, 'total_lessons', len(lessons)),
            'objectives': course.get_objectives_list(),
        }
        cache.set(syllabus_cache_key, syllabus, 900)

    course = syllabus['course']
    lessons = syllabus['lessons']
    modules = syllabus['modules']
    assessments = syllabus['assessments']
    lesson_ids_with_exercises = syllabus['lesson_ids_with_exercises']
    total_lessons = syllabus['total_lessons']
    objectives = syllabus['objectives']

    is_enrolled = False
    progress_info = {
        'percentage': 0,
        'completed': 0,
        'total': total_lessons,
        'is_unlocked': False,
        'is_completed': False,
        'quiz_passed': False,
        'mock_passed': False
    }
    first_incomplete_lesson = None
    completed_lesson_ids = set()
    is_bookmarked = False
    user_review = None
    can_review = False

    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
        is_bookmarked = CourseBookmark.objects.filter(user=request.user, course=course).exists()
        user_review = CourseReview.objects.filter(user=request.user, course=course).first()

        if is_enrolled:
            Course.invalidate_user_progress_cache(request.user.id, course.id)
            progress_info = course.get_user_progress(request.user, use_cache=False)
            completed_lesson_ids = set(
                LessonProgress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    is_completed=True
                ).values_list('lesson_id', flat=True)
            )
            # User can review if enrolled and has completed >= 50% of the course
            total_course_lessons = len(lessons)
            can_review = (
                (total_course_lessons == 0 and len(completed_lesson_ids) >= 1) or
                (total_course_lessons > 0 and (len(completed_lesson_ids) / total_course_lessons) >= 0.5)
            )

            # Find next incomplete lesson from prefetched list
            for lesson in lessons:
                if lesson.id not in completed_lesson_ids:
                    first_incomplete_lesson = lesson
                    break
            if not first_incomplete_lesson and lessons:
                first_incomplete_lesson = lessons[0]

    # Strict 4-State Enrollment Logic:
    if not request.user.is_authenticated:
        enrollment_state = 'logged_out'
    elif not is_enrolled:
        enrollment_state = 'not_enrolled'
    elif progress_info.get('percentage', 0) == 100 or progress_info.get('is_completed', False):
        enrollment_state = 'completed'
    else:
        enrollment_state = 'in_progress'

    first_lesson = lessons[0] if lessons else None

    # Ratings and reviews
    approved_reviews = list(
        course.reviews.filter(is_approved=True)
        .select_related('user', 'user__profile')
        .order_by('-created_at')[:30]
    )
    avg_rating, reviews_count = course.get_rating_summary()

    # Calculate rating distribution breakdown
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for rev in approved_reviews:
        if rev.rating in rating_counts:
            rating_counts[rev.rating] += 1
    total_revs = len(approved_reviews)
    rating_distribution = [
        {
            'stars': star,
            'count': rating_counts[star],
            'percent': int(round((rating_counts[star] / total_revs) * 100)) if total_revs > 0 else 0
        }
        for star in [5, 4, 3, 2, 1]
    ]

    # Telemetry
    track_event(
        user=request.user,
        event_type='course_viewed',
        metadata={'course_id': course.id, 'course_slug': course.slug, 'course_title': course.title},
        session_key=getattr(request.session, 'session_key', '') or ''
    )

    return render(request, 'courses/detail.html', {
        'course': course,
        'modules': modules,
        'lessons': lessons,
        'first_lesson': first_lesson,
        'assessments': assessments,
        'completed_lesson_ids': completed_lesson_ids,
        'completed_lessons_count': len(completed_lesson_ids),
        'lesson_ids_with_exercises': lesson_ids_with_exercises,
        'is_enrolled': is_enrolled,
        'is_bookmarked': is_bookmarked,
        'enrollment_state': enrollment_state,
        'progress_info': progress_info,
        'first_incomplete_lesson': first_incomplete_lesson,
        'objectives': course.get_objectives_list(),
        'prerequisites': course.get_prerequisites_list(),
        'approved_reviews': approved_reviews,
        'user_review': user_review,
        'can_review': can_review,
        'avg_rating': avg_rating,
        'reviews_count': reviews_count,
        'rating_distribution': rating_distribution,
    })


@login_required
def enroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if request.method == 'POST':
        try:
            enrollment, created = Enrollment.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={'curriculum_version': course.curriculum_version}
            )
        except Enrollment.MultipleObjectsReturned:
            enrollments = Enrollment.objects.filter(user=request.user, course=course).order_by('id')
            enrollment = enrollments.first()
            enrollments.exclude(id=enrollment.id).delete()
            created = False
        except Exception as e:
            logger.error(f"Error enrolling user {request.user.id} in course {slug}: {e}", exc_info=True)
            messages.error(request, f"Unable to process enrollment right now. Please try again.")
            return redirect('courses:detail', slug=course.slug)

        if created:
            try:
                LearningActivity.objects.create(
                    user=request.user,
                    activity_type='ENROLL',
                    reference_id=course.id,
                    description=f"Enrolled in {course.title}"
                )
            except Exception as e:
                logger.warning(f"Failed to record learning activity on enrollment: {e}")

            # Telemetry
            track_event(
                user=request.user,
                event_type='course_enrolled',
                metadata={'course_id': course.id, 'course_slug': course.slug, 'course_title': course.title},
                event_key=f"enroll_{request.user.id}_{course.id}"
            )

            messages.success(request, f"Successfully enrolled in '{course.title}'! Let's get started.")
        else:
            messages.info(request, f"You are already enrolled in '{course.title}'.")

        # Invalidate cache defensively
        try:
            Course.invalidate_user_progress_cache(request.user.id, course.id)
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")

        # Redirect to first lesson if available, otherwise course detail
        try:
            first_lesson = course.lessons.order_by('lesson_order').first()
            if first_lesson:
                return redirect('learning:lesson_detail', course_slug=course.slug, lesson_id=first_lesson.id)
        except Exception as e:
            logger.error(f"Failed to resolve first lesson for {slug}: {e}", exc_info=True)

        return redirect('courses:detail', slug=course.slug)

    return redirect('courses:detail', slug=course.slug)


@login_required
def upgrade_curriculum_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if request.method == 'POST':
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        if enrollment and enrollment.curriculum_version < course.curriculum_version:
            enrollment.curriculum_version = course.curriculum_version
            enrollment.save(update_fields=['curriculum_version'])
            messages.success(request, f"Successfully upgraded your curriculum for '{course.title}' to Version {course.curriculum_version}!")
        else:
            messages.info(request, "You are already on the latest curriculum version.")
    return redirect('courses:detail', slug=course.slug)


@login_required
def unenroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        try:
            deleted_count, _ = Enrollment.objects.filter(user=request.user, course=course).delete()
            if deleted_count > 0:
                # Also clean up lesson progress for this course
                try:
                    LessonProgress.objects.filter(user=request.user, lesson__course=course).delete()
                except Exception as e:
                    logger.warning(f"Error cleaning LessonProgress on unenroll: {e}")
                messages.info(request, f"You have unenrolled from '{course.title}'.")
            try:
                Course.invalidate_user_progress_cache(request.user.id, course.id)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error unenrolling user {request.user.id} from {slug}: {e}", exc_info=True)
            messages.error(request, "Unable to unenroll right now. Please try again.")
        return redirect('courses:my_learning')
    return redirect('courses:detail', slug=course.slug)


@login_required
def my_learning_view(request):
    filter_tab = request.GET.get('tab', 'all')  # all, in_progress, completed, saved

    enrollments = list(
        Enrollment.objects.filter(user=request.user)
        .select_related('course', 'course__category')
        .order_by('-enrolled_at')
    )
    total_enrolled = len(enrollments)
    enrolled_items = []

    # Saved Bookmarks (Courses + Lessons)
    saved_courses_qs = CourseBookmark.objects.filter(user=request.user).select_related('course', 'course__category').order_by('-created_at')
    saved_lessons_qs = LessonBookmark.objects.filter(user=request.user).select_related('lesson', 'lesson__course').order_by('-created_at')
    total_saved = saved_courses_qs.count() + saved_lessons_qs.count()
    saved_courses_data = []
    saved_lessons = []

    course_ids = [e.course_id for e in enrollments]

    if filter_tab == 'saved':
        user_enrolled_set = set(course_ids)
        saved_lessons = list(saved_lessons_qs)
        for bm in saved_courses_qs:
            c = bm.course
            is_enr = c.id in user_enrolled_set
            prog = c.get_user_progress(request.user) if is_enr else None
            saved_courses_data.append({
                'bookmark': bm,
                'course': c,
                'is_enrolled': is_enr,
                'progress': prog,
            })
    elif enrollments:
        # Batch completions
        completions = {
            c.course_id: c
            for c in CourseCompletion.objects.filter(user=request.user, course_id__in=course_ids)
        }
        # Batch completed lesson IDs
        completed_lesson_ids = set(
            LessonProgress.objects.filter(
                user=request.user,
                is_completed=True,
                lesson__course_id__in=course_ids
            ).values_list('lesson_id', flat=True)
        )
        # Batch lessons ordered
        lessons_by_course = {}
        for l in Lesson.objects.filter(course_id__in=course_ids).order_by('lesson_order', 'id'):
            lessons_by_course.setdefault(l.course_id, []).append(l)

        for enrollment in enrollments:
            course = enrollment.course
            course_lessons = lessons_by_course.get(course.id, [])
            prog = course.get_user_progress(request.user)

            # Find next incomplete lesson
            next_lesson = None
            for l in course_lessons:
                if l.id not in completed_lesson_ids:
                    next_lesson = l
                    break
            if not next_lesson and course_lessons:
                next_lesson = course_lessons[0]

            item = {
                'enrollment': enrollment,
                'course': course,
                'progress': prog,
                'next_lesson': next_lesson,
                'is_completed': prog['is_completed'],
            }

            if filter_tab == 'completed' and not prog['is_completed']:
                continue
            elif filter_tab == 'in_progress' and (prog['is_completed'] or prog['total'] == 0):
                continue

            enrolled_items.append(item)

    return render(request, 'courses/my_learning.html', {
        'enrolled_items': enrolled_items,
        'active_tab': filter_tab,
        'total_enrolled': total_enrolled,
        'total_saved': total_saved,
        'saved_courses_data': saved_courses_data,
        'saved_lessons': saved_lessons,
    })


@login_required
def saved_courses_view(request):
    return redirect(f"{reverse('courses:my_learning')}?tab=saved")


@login_required
def toggle_course_bookmark_api(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    bookmark, created = CourseBookmark.objects.get_or_create(user=request.user, course=course)
    if not created:
        bookmark.delete()
        is_bookmarked = False
        message = f"Removed '{course.title}' from your saved courses."
    else:
        is_bookmarked = True
        message = f"Saved '{course.title}' to your bookmarks."

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.content_type == 'application/json' or
        'application/json' in request.headers.get('Accept', '')
    )
    if is_ajax:
        return JsonResponse({
            'success': True,
            'is_bookmarked': is_bookmarked,
            'message': message,
            'course_id': course.id,
            'course_slug': course.slug,
        })

    messages.success(request, message)
    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER')
    return redirect(next_url or 'courses:detail', slug=course.slug)


@login_required
def submit_course_review_view(request, slug):
    if request.method != 'POST':
        return redirect('courses:detail', slug=slug)

    course = get_object_or_404(Course, slug=slug, is_published=True)

    # Strict Eligibility check: enrolled + completed >= 50% of the course
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    completed_lessons_count = LessonProgress.objects.filter(
        user=request.user, lesson__course=course, is_completed=True
    ).count()
    total_course_lessons = course.lessons.count()
    is_eligible = is_enrolled and (
        (total_course_lessons == 0 and completed_lessons_count >= 1) or
        (total_course_lessons > 0 and (completed_lessons_count / total_course_lessons) >= 0.5)
    )

    if not is_eligible:
        messages.error(request, "You must be enrolled and complete at least 50% of the course before submitting a review.")
        return redirect('courses:detail', slug=slug)

    try:
        rating = int(request.POST.get('rating', 0))
    except (ValueError, TypeError):
        rating = 0

    if rating < 1 or rating > 5:
        messages.error(request, "Please select a valid rating between 1 and 5 stars.")
        return redirect('courses:detail', slug=slug)

    comment = request.POST.get('comment', '').strip()[:1000]

    review, created = CourseReview.objects.update_or_create(
        user=request.user,
        course=course,
        defaults={
            'rating': rating,
            'comment': comment,
            'is_approved': True,
        }
    )
    if created:
        messages.success(request, "Thank you! Your verified student review has been published.")
    else:
        messages.success(request, "Your review has been updated.")

    return redirect('courses:detail', slug=slug)


@login_required
def delete_course_review_view(request, slug):
    if request.method != 'POST':
        return redirect('courses:detail', slug=slug)
    course = get_object_or_404(Course, slug=slug, is_published=True)
    deleted, _ = CourseReview.objects.filter(user=request.user, course=course).delete()
    if deleted:
        messages.success(request, "Your review has been removed.")
    return redirect('courses:detail', slug=slug)


@login_required
def assessment_intro_view(request, slug, assessment_type):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    assessment = get_object_or_404(course.course_assessments, assessment_type=assessment_type, is_active=True)

    progress = course.get_user_progress(request.user)
    is_unlocked = progress['is_unlocked']

    attempts = list(assessment.attempts.filter(user=request.user).order_by('-started_at'))
    best_attempt = max(attempts, key=lambda a: a.percentage) if attempts else None
    has_passed = any(a.is_passed for a in attempts)

    return render(request, 'courses/assessment_intro.html', {
        'course': course,
        'assessment': assessment,
        'progress': progress,
        'is_unlocked': is_unlocked,
        'attempts': attempts,
        'best_attempt': best_attempt,
        'has_passed': has_passed,
        'question_count': assessment.questions.count(),
    })


@login_required
def take_assessment_view(request, slug, assessment_type):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    assessment = get_object_or_404(course.course_assessments, assessment_type=assessment_type, is_active=True)
    # Enforce course enrollment for optional assessment
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "Please enroll in the course before taking this assessment.")
        return redirect('courses:detail', slug=course.slug)

    questions = list(assessment.questions.all().order_by('order', 'id'))
    if not questions:
        messages.warning(request, "Assessment question bank is currently being prepared.")
        return redirect('courses:detail', slug=course.slug)

    attempt_number = assessment.attempts.filter(user=request.user).count() + 1

    return render(request, 'courses/assessment_take.html', {
        'course': course,
        'assessment': assessment,
        'questions': questions,
        'total_questions': len(questions),
        'duration_seconds': assessment.duration_minutes * 60,
        'attempt_number': attempt_number,
    })


@login_required
def submit_assessment_view(request, slug, assessment_type):
    if request.method != 'POST':
        return redirect('courses:assessment_intro', slug=slug, assessment_type=assessment_type)

    course = get_object_or_404(Course, slug=slug, is_published=True)
    assessment = get_object_or_404(course.course_assessments, assessment_type=assessment_type, is_active=True)

    # Server-side enrollment verification
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "Enrollment required to take assessments.")
        return redirect('courses:detail', slug=course.slug)

    questions = list(assessment.questions.all().order_by('order', 'id'))
    total_q = len(questions)

    score = 0
    topic_breakdown = {}
    answers_record = {}

    for q in questions:
        field_name = f"question_{q.id}"
        selected = request.POST.get(field_name, '').strip().upper()
        is_correct = (selected == q.correct_answer)
        if is_correct:
            score += 1

        topic = q.topic or "Core"
        if topic not in topic_breakdown:
            topic_breakdown[topic] = {'total': 0, 'correct': 0}
        topic_breakdown[topic]['total'] += 1
        if is_correct:
            topic_breakdown[topic]['correct'] += 1

        answers_record[str(q.id)] = {
            'selected': selected,
            'correct': q.correct_answer,
            'is_correct': is_correct,
            'explanation': q.explanation
        }

    percentage = int(round((score / total_q) * 100)) if total_q > 0 else 0
    is_passed = percentage >= assessment.passing_percentage

    attempt_count = assessment.attempts.filter(user=request.user).count() + 1
    attempt = CourseAssessmentAttempt.objects.create(
        user=request.user,
        assessment=assessment,
        score=score,
        total_questions=total_q,
        percentage=percentage,
        is_passed=is_passed,
        attempt_number=attempt_count,
        answers_json=json.dumps(answers_record),
        completed_at=timezone.now()
    )

    if is_passed:
        from gamification.services import award_user_xp
        xp_amount = 100 if assessment_type == 'final_quiz' else 150
        award_user_xp(request.user, xp_amount, f"Passed {assessment.title} ({percentage}%)")

    # Refresh course completion state
    prog = course.get_user_progress(request.user)

    return render(request, 'courses/assessment_result.html', {
        'course': course,
        'assessment': assessment,
        'attempt': attempt,
        'is_passed': is_passed,
        'percentage': percentage,
        'score': score,
        'total_questions': total_q,
        'topic_breakdown': topic_breakdown,
        'answers_record': answers_record,
        'course_progress': prog,
    })
