from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, ProfileSetupForm
from .models import StudentProfile
from goals.models import LearningActivity

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']

            # Use email as username or sanitized base
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            names = full_name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Signal auto-creates StudentProfile, but let's ensure full_name is populated
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            profile.full_name = full_name
            profile.save()

            # Log registration activity
            LearningActivity.objects.create(
                user=user,
                activity_type='ENROLL',
                description=f"Joined SkillSphere! Welcome, {full_name}."
            )

            # Log user in
            login(request, user)
            messages.success(request, f"Welcome to SkillSphere, {full_name}! Let's set up your learning preferences.")
            return redirect('accounts:profile_setup')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            # Look up username by email
            user_obj = User.objects.filter(email__iexact=email).first()
            user = None
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)  # Browser close session
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                messages.success(request, f"Welcome back, {user.profile.full_name or user.username}!")
                next_url = request.GET.get('next')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('dashboard:index')
            else:
                messages.error(request, "Invalid email address or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def profile_setup_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Profile preferences saved successfully! Ready to start learning.")
                return redirect('dashboard:index')
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception("Profile setup save failed: %s", e)
                messages.warning(request, "Your profile was saved, but the avatar image could not be processed. You can update it anytime in settings.")
                return redirect('dashboard:index')
    else:
        form = ProfileSetupForm(instance=profile)

    interest_options = StudentProfile.AVAILABLE_INTERESTS
    selected_interests = profile.get_interests_list()

    return render(request, 'accounts/profile_setup.html', {
        'form': form,
        'profile': profile,
        'interest_options': interest_options,
        'selected_interests': selected_interests,
    })


@login_required
def profile_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    interests_display = []
    interests_map = dict(StudentProfile.AVAILABLE_INTERESTS)
    for i in profile.get_interests_list():
        interests_display.append(interests_map.get(i, i))

    enrolled_count = request.user.enrollments.count()
    completed_goals_count = request.user.goals.filter(is_completed=True).count()
    total_goals_count = request.user.goals.count()

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'interests_display': interests_display,
        'enrolled_count': enrolled_count,
        'completed_goals_count': completed_goals_count,
        'total_goals_count': total_goals_count,
    })


@login_required
def profile_edit_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Your profile details have been updated.")
                return redirect('accounts:profile')
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception("Profile update save failed: %s", e)
                messages.error(request, "Could not process avatar image. Please try an external image URL instead.")
    else:
        form = ProfileSetupForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'profile': profile,
        'interest_options': StudentProfile.AVAILABLE_INTERESTS,
        'selected_interests': profile.get_interests_list(),
    })
