[11/21/2026 10:32 PM] J: from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
import logging

from .models import (
Course,
Enrollment,
Question,
Choice,
Submission
)

logger = logging.getLogger(name)

def registration_request(request):
context = {}

if request.method == 'GET':
    return render(
        request,
        'onlinecourse/user_registration_bootstrap.html',
        context
    )

elif request.method == 'POST':
    username = request.POST['username']
    password = request.POST['psw']
    first_name = request.POST['firstname']
    last_name = request.POST['lastname']

    user_exist = False

    try:
        User.objects.get(username=username)
        user_exist = True
    except User.DoesNotExist:
        logger.info("New user")

    if not user_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        login(request, user)
        return redirect("onlinecourse:index")

    else:
        context['message'] = "User already exists."
        return render(
            request,
            'onlinecourse/user_registration_bootstrap.html',
            context
        )
def login_request(request):
context = {}

if request.method == "POST":
    username = request.POST['username']
    password = request.POST['psw']

    user = authenticate(
        username=username,
        password=password
    )

    if user is not None:
        login(request, user)
        return redirect('onlinecourse:index')

    else:
        context['message'] = "Invalid username or password."
        return render(
            request,
            'onlinecourse/user_login_bootstrap.html',
            context
        )

else:
    return render(
        request,
        'onlinecourse/user_login_bootstrap.html',
        context
    )
def logout_request(request):
logout(request)
return redirect('onlinecourse:index')

def check_if_enrolled(user, course):
is_enrolled = False

if user.id is not None:
    num_results = Enrollment.objects.filter(
        user=user,
        course=course
    ).count()

    if num_results > 0:
        is_enrolled = True

return is_enrolled
class CourseListView(generic.ListView):
template_name = 'onlinecourse/course_list_bootstrap.html'
context_object_name = 'course_list'

def get_queryset(self):
    user = self.request.user
    courses = Course.objects.order_by(
        '-total_enrollment'
    )[:10]

    for course in courses:
        if user.is_authenticated:
            course.is_enrolled = check_if_enrolled(
                user,
                course
            )

    return courses
class CourseDetailView(generic.DetailView):
model = Course
template_name = 'onlinecourse/course_detail_bootstrap.html'

def enroll(request, course_id):
course = get_object_or_404(Course, pk=course_id)
user = request.user

is_enrolled = check_if_enrolled(user, course)

if not is_enrolled and user.is_authenticated:
    Enrollment.objects.create(
        user=user,
        course=course,
        mode='honor'
    )

    course.total_enrollment += 1
    course.save()

return HttpResponseRedirect(
    reverse(
        viewname='onlinecourse:course_details',
        args=(course.id,)
    )
)
def extract_answers(request):
submitted_answers = []

for key in request.POST:
    if key.startswith('choice'):
        value = request.POST[key]
        choice_id = int(value)
        submitted_answers.append(choice_id)

return submitted_answers
def submit(request, course_id):
course = get_object_or_404(Course, pk=course_id)

enrollment = get_object_or_404(
    Enrollment,
    user=request.user,
    course=course
)

submission = Submission.objects.create(
    enrollment=enrollment
)

selected_choices = extract_answers(request)

for choice_id in selected_choices:
    choice = get_object_or_404(
        Choice,
[11/21/2026 10:32 PM] J: pk=choice_id
    )
    submission.choices.add(choice)

return redirect(
    'onlinecourse:show_exam_result',
    course_id=course.id,
    submission_id=submission.id
)
def show_exam_result(request, course_id, submission_id):
course = get_object_or_404(
Course,
pk=course_id
)

submission = get_object_or_404(
    Submission,
    pk=submission_id,
    enrollment__course=course
)

questions = Question.objects.filter(course=course)

selected_choices = submission.choices.all()

selected_ids = [
    choice.id for choice in selected_choices
]

total_score = 0
total_grade = 0
question_results = []

for question in questions:
    choices = question.choice_set.all()

    total_grade += question.grade

    selected_choice = selected_choices.filter(
        question=question
    ).first()

    is_correct = question.is_get_score(selected_ids)

    if is_correct:
        total_score += question.grade

    question_results.append({
        'question': question,
        'choices': choices,
        'selected_choice': selected_choice,
        'is_correct': is_correct,
    })

submission.total_score = total_score
submission.save()

grade = (
    int((total_score / total_grade) * 100)
    if total_grade > 0
    else 0
)

context = {
    'course': course,
    'submission': submission,
    'question_results': question_results,
    'selected_ids': selected_ids,
    'total_score': total_score,
    'total_grade': total_grade,
    'grade': grade,
}

return render(
    request,
    'onlinecourse/exam_result_bootstrap.html',
    context
)
