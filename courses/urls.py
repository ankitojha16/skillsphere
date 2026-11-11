from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list_view, name='list'),
    path('api/autocomplete/', views.course_search_autocomplete_api, name='search_autocomplete'),
    path('my-learning/', views.my_learning_view, name='my_learning'),
    path('saved/', views.saved_courses_view, name='saved_courses'),
    path('<slug:slug>/bookmark/', views.toggle_course_bookmark_api, name='toggle_bookmark'),
    path('<slug:slug>/review/', views.submit_course_review_view, name='submit_review'),
    path('<slug:slug>/review/delete/', views.delete_course_review_view, name='delete_review'),
    path('<slug:slug>/', views.course_detail_view, name='detail'),
    path('<slug:slug>/enroll/', views.enroll_course_view, name='enroll'),
    path('<slug:slug>/unenroll/', views.unenroll_course_view, name='unenroll'),
    path('<slug:slug>/upgrade-curriculum/', views.upgrade_curriculum_view, name='upgrade_curriculum'),
    
    # 80% Unlocked Course Examinations (Final Quiz & Final Mock)
    path('<slug:slug>/assessments/<str:assessment_type>/', views.assessment_intro_view, name='assessment_intro'),
    path('<slug:slug>/assessments/<str:assessment_type>/take/', views.take_assessment_view, name='take_assessment'),
    path('<slug:slug>/assessments/<str:assessment_type>/take/alt/', views.take_assessment_view, name='assessment_take'),
    path('<slug:slug>/assessments/<str:assessment_type>/submit/', views.submit_assessment_view, name='submit_assessment'),
    path('<slug:slug>/assessments/<str:assessment_type>/submit/alt/', views.submit_assessment_view, name='assessment_submit'),
]
