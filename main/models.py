from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime
from os.path import splitext
from education_platform import settings
# Create your models here.

def get_timestamp_path(instance, filename):
    return '%s%s' % (datetime.now().timestamp(), splitext(filename)[1])
class AdvUser(AbstractUser):
    is_activated = models.BooleanField(default=True, db_index=True,
                                       verbose_name='Прошел активацию?')
    send_messages = models.BooleanField(default=True,
                                        verbose_name='Слать оповещения о новых комментариях?')
    is_teacher = models.BooleanField(default=False,
                                     verbose_name='Является учителем?')

    def delete(self, *args, **kwargs):
        for lesson in self.lesson_set.all():
            lesson.delete()
        super().delete(*args, **kwargs)

    class Meta(AbstractUser.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Rubric(models.Model):
    name = models.CharField(max_length=20, db_index=True, unique=True,
                            verbose_name='Название')
    order = models.SmallIntegerField(default=0, db_index=True,
                                     verbose_name='Порядок')
    super_rubric = models.ForeignKey('SuperRubric',
                                     on_delete=models.PROTECT, null=True,
                                     blank=True,
                                     verbose_name='Надрубрика')
    description = models.TextField(default=None, null=True,
                                   verbose_name='Описание курса')
    image = models.ImageField(blank=True, upload_to=get_timestamp_path,
                              verbose_name='Изображение')


class SuperRubricManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=True)


class SuperRubric(Rubric):
    objects = SuperRubricManager()

    def __str__(self):
        return self.name

    class Meta:
        proxy = True
        ordering = ('order', 'name')
        verbose_name = 'Надрубрика'
        verbose_name_plural = 'Надрубрики'


class SubRubricManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=False)


class SubRubric(Rubric):
    objects = SubRubricManager()

    def __str__(self):
        return '%s - %s' % (self.super_rubric.name, self.name)

    class Meta:
        proxy = True
        ordering = ('super_rubric__order', 'super_rubric__name', 'order',
                    'name')
        verbose_name = 'Подрубрика'
        verbose_name_plural = 'Подрубрики'


class Lesson(models.Model):
    rubric = models.ForeignKey(SubRubric, on_delete=models.PROTECT,
                               verbose_name='Рубрика')
    title = models.CharField(max_length=40, verbose_name='Урок')
    content = models.TextField(verbose_name='Oпиcaниe')
    contacts = models.TextField(verbose_name='Koнтaкты')
    video = models.CharField(max_length=140, verbose_name='Видео',
                             default=None)
    author = models.ForeignKey(AdvUser, on_delete=models.CASCADE,
                               verbose_name='Преподаватель')
    is_active = models.BooleanField(default=True, db_index=True,
                                    verbose_name='Выводить в списке?')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True,
                                      verbose_name='Опубликовано')
    order = models.SmallIntegerField(default=0, db_index=True,
                                     verbose_name='Порядок')

    def __str__(self):
        """
        String for representing the Model object.
        """
        return f'{self.title}'

    def delete(self, *args, **kwargs):
        for ai in self.additionalfile_set.all():
            ai.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Уроки'
        verbose_name = 'Урок'
        ordering = ('order', '-created_at')


class AdditionalFile(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               verbose_name='Урок')
    file = models.FileField(upload_to=get_timestamp_path,
                            verbose_name='Файл',
                            default=None)

    class Meta:
        verbose_name_plural = 'Дополнительные материалы'
        verbose_name = 'Дополнительная материалы'


class Comment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               verbose_name='Урок')
    author = models.CharField(max_length=30, verbose_name='Автор')
    content = models.CharField(max_length=255, verbose_name='Содержание')
    is_active = models.BooleanField(default=True, db_index=True,
                                    verbose_name='Выводить на экран?')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True,
                                      verbose_name='Опубликован')

    def __str__(self):
        """
        String for representing the Model object.
        """
        return f'{self.content}'

    class Meta:
        verbose_name_plural = 'Комментарии'
        verbose_name = 'Комментарий'
        ordering = ['-created_at']


class GroupStudents(models.Model):
    course = models.ForeignKey(
        SubRubric, null=True, blank=True,
        verbose_name="Курс", on_delete=models.CASCADE)

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE)

    def __str__(self):
        """
        String for representing the Model object.
        """
        return f'{self.student.email}'

    class Meta:
        verbose_name = "Группа студентов"
        verbose_name_plural = "Группы студентов"


class CourseProject(models.Model):
    rubric = models.ForeignKey(SubRubric, on_delete=models.PROTECT,
                               verbose_name='Рубрика')
    title = models.CharField(max_length=40, verbose_name='Название')
    content = models.TextField(verbose_name='Oпиcaниe')
    file = models.FileField(upload_to=get_timestamp_path,
                            verbose_name='Файл',
                            default=None)

    def __str__(self):
        """
        String for representing the Model object.
        """
        return f'{self.title}'

    class Meta:
        verbose_name = "Курсовой проект"
        verbose_name_plural = "Курсовые проекты"


class Crew(models.Model):
    course = models.ForeignKey(CourseProject, on_delete=models.PROTECT,
                               verbose_name='Курсовой проект7')
    student1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='student1',
        verbose_name="Пользователь 1",
        on_delete=models.CASCADE, )
    student2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,related_name='student2',
        verbose_name="Пользователь 2",
        on_delete=models.CASCADE, null=True)
    student3 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='student3',
        verbose_name="Пользователь 3",
        on_delete=models.CASCADE, null=True)
    student4 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='student4',
        verbose_name="Пользователь 4",
        on_delete=models.CASCADE, null=True)

    def __str__(self):
        """
        String for representing the Model object.
        """
        return f'{self.course} - {self.course_id}'

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"