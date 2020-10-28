from django.shortcuts import render
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from .models import AdvUser, SubRubric, Lesson, Comment, GroupStudents, \
    CourseProject, Crew,Rubric
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib import messages

from django.views.generic.base import TemplateView
from django.core.signing import BadSignature
from .forms import *
from quiz.models import Quiz,Question
from django.http.request import HttpRequest

# Create your views here.

class RegisterUserView(CreateView):
    model = AdvUser
    template_name = 'registration/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main')

class RegisterDoneView(TemplateView):
    template_name = 'registration/register_done.html'

class LWMLoginView(LoginView):
    template_name = 'registration/login.html'

class LWMLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'registration/logout.html'


class LWMPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin,
                            PasswordChangeView):
    template_name = 'registration/password_change.html'
    success_url = reverse_lazy('main')
    success_message = 'Пароль пользователя изменен'

class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'registration/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main')
    success_message = 'Личные данные пользователя изменены'

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'registration/delete_user.html'
    success_url = reverse_lazy('main')

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.SUCCESS,
                             'Пользователь удален')
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

@login_required
def main(request):
    lessons = Lesson.objects.all()
    rubrics = SuperRubric.objects.all()
    subrubric = SubRubric.objects.all()
    context = {'lessons': lessons,'rubric': rubrics,'subrubric':subrubric}
    return render(request, 'main.html', context)

def by_rubric(request, pk):
    superrubric = SuperRubric.objects.get(pk = pk)
    rubrics = SuperRubric.objects.all()
    context = {'rubric': rubrics,'superrubric':superrubric}
    return render(request, 'main/by_rubric.html', context)
@login_required
def project(request, pk):
    rubrics = SuperRubric.objects.all()
    project = CourseProject.objects.get(rubric__courseproject=pk)
    crews = Crew.objects.filter(course=pk)
    context = {'project': project, 'crews': crews,'rubric':rubrics}
    return render(request, 'main/project.html', context)

@login_required
def profile(request):
    rubrics = SuperRubric.objects.all()
    lessons = Lesson.objects.filter(author=request.user.pk)
    context = {'lessons': lessons,'rubric':rubrics}
    return render(request, 'registration/profile.html', context)

@login_required
def profile_lesson_add(request):
    rubrics = SuperRubric.objects.all()
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=lesson)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Урок добавлен')
                return redirect('profile')
    else:
        form = LessonForm(initial={'author': request.user.pk})
        formset = AIFormSet()
    context = {'form': form, 'formset': formset,'rubric':rubrics}
    return render(request, 'registration/profile_lesson_add.html', context)

@login_required
def profile_lesson_change(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    rubrics = SuperRubric.objects.all()
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            lesson = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=lesson)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Урок исправлен')
                return redirect('profile')
    else:
        form = LessonForm(instance=lesson)
        formset = AIFormSet(instance=lesson)
    context = {'form': form, 'formset': formset,'rubric':rubrics}
    return render(request, 'registration/profile_lesson_change.html', context)

@login_required
def profile_lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    rubrics = SuperRubric.objects.all()
    ais = lesson.additionalfile_set.all()
    comments = Comment.objects.filter(lesson=pk, is_active=True)
    context = {'lesson': lesson, 'ais': ais, 'comments': comments,'rubric':rubrics}
    return render(request, 'main/profile_lesson_detail.html', context)


@login_required
def profile_lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    rubrics = SuperRubric.objects.all()
    if request.method == 'POST':
        lesson.delete()
        messages.add_message(request, messages.SUCCESS,
                             'Урок удален')
        return redirect('profile')
    else:
        context = {'lesson': lesson,'rubric':rubrics}
        return render(request, 'registration/profile_lesson_delete.html',
                      context)
@login_required
def detail(request, rubric_pk, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    lesson.video = lesson.video.split('/')[-1].split('=')[-1]
    rubrics = SuperRubric.objects.all()
    ais = lesson.additionalfile_set.all()
    comments = Comment.objects.filter(lesson=pk, is_active=True)
    quiz = Quiz.objects.filter(lesson=lesson)
    next_lesson = Lesson.objects.filter(rubric_id=rubric_pk,
                                        order=lesson.order + 1)
    initial = {'lesson': lesson.pk}
    context = {'rubric':rubrics,'lesson': lesson, 'ais': ais, 'comments': comments,
               'quiz': quiz, 'next_lesson': next_lesson.first()}
    print(lesson.video,type(lesson.video))
    if request.user.is_authenticated:
        initial['author'] = request.user.username
        form_class = UserCommentForm
        form = form_class(initial=initial)
        if request.method == 'POST':
            c_form = form_class(request.POST)
            if c_form.is_valid():
                c_form.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Комментарий добавлен')
            else:
                form = c_form
                messages.add_message(request, messages.WARNING,
                                     'Комментарий не добавлен')
        context['form'] = form
    else:
        context['form'] = None

    return render(request, 'main/detail.html', context)