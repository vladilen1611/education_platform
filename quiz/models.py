from django.db import models
import json
import re
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import MaxValueValidator, \
    validate_comma_separated_integer_list
from django.db import models
from django.utils.timezone import now
from model_utils.managers import InheritanceManager
from education_platform import settings
from main.models import Lesson

# Create your models here.

class Quiz(models.Model):
    title = models.CharField(
        verbose_name="Название", max_length=60, blank=False)

    description = models.TextField(
        verbose_name="Описание",
        blank=True, help_text="Описание теста")

    url = models.SlugField(
        max_length=60, blank=False,
        help_text="url теста",
        verbose_name="url теста")

    lesson = models.ForeignKey(
        Lesson, null=True, blank=True,
        verbose_name="Урок", on_delete=models.CASCADE)

    random_order = models.BooleanField(
        blank=False, default=False,
        verbose_name="Случайная порядок",
        help_text="Отображать вопросы в случайном порядке или в порядке добавления?")

    max_questions = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Максимальное количество вопросов",
        help_text="Количество вопросов, на которые должны быть даны ответы при каждой попытке")

    answers_at_end = models.BooleanField(
        blank=False, default=False,
        help_text="Правильный ответ НЕ показан после вопроса. Ответы отображаются после "
                  "прохождения теста",
        verbose_name="Ответы в конце")

    exam_paper = models.BooleanField(
        blank=False, default=False,
        help_text="Если отмечено, результаты каждой попытки пользователя будет сохранен",
        verbose_name="Экзаменационный лист")

    single_attempt = models.BooleanField(
        blank=False, default=False,
        help_text="Если отмечено, пользователю будет разрешена только одна попытка",
        verbose_name="Единственная попытка")

    pass_mark = models.SmallIntegerField(
        blank=True, default=0,
        verbose_name="Pass Mark",
        help_text="Процент правильных ответов для прохождения теста",
        validators=[MaxValueValidator(100)])

    success_text = models.TextField(
        blank=True,
        help_text="Отображается, если пользователь успешно прошел тест",
        verbose_name="Текст при успешном выполнении теста")

    fail_text = models.TextField(
        verbose_name="Текст в случае неудачи",
        blank=True, help_text="Текст при не выполнении теста")

    draft = models.BooleanField(
        blank=True, default=False,
        verbose_name="Черновик",
        help_text="Если отмечено, то не "
                  "отображается в публичном списке и может быть "
                  "взято только пользователями с соответствующим правом")

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.url = re.sub('\s+', '-', self.url).lower()

        self.url = ''.join(letter for letter in self.url if
                           letter.isalnum() or letter == '-')

        if self.single_attempt is True:
            self.exam_paper = True

        if self.pass_mark > 100:
            raise ValidationError('%s is above 100' % self.pass_mark)

        super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()

    def anon_score_id(self):
        return str(self.id) + "_score"

    def anon_q_list(self):
        return str(self.id) + "_q_list"

    def anon_q_data(self):
        return str(self.id) + "_data"


class Question(models.Model):
    """
    Base class for all question types.
    Shared properties placed here.
    """

    quiz = models.ManyToManyField(Quiz,
                                  verbose_name="Тест",
                                  blank=True)

    lesson = models.ForeignKey(Lesson,
                               verbose_name="Урок",
                               blank=True,
                               null=True, on_delete=models.CASCADE)

    figure = models.ImageField(upload_to='uploads/%Y/%m/%d',
                               blank=True,
                               null=True,
                               verbose_name="Рисунок")

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text="Введите текст вопроса, "
                                         "который должен отобразиться",
                               verbose_name='Вопрос')

    explanation = models.TextField(max_length=2000,
                                   blank=True,
                                   help_text="Объяснение показывается после "
                                             "того, как дан ответ на вопрос",
                                   verbose_name='Объяснение')

    objects = InheritanceManager()

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['lesson']

    def __str__(self):
        return self.content

class SittingManager(models.Manager):

    def new_sitting(self, user, quiz):
        if quiz.random_order is True:
            question_set = quiz.question_set.all() \
                .select_subclasses() \
                .order_by('?')
        else:
            question_set = quiz.question_set.all() \
                .select_subclasses()

        question_set = [item.id for item in question_set]

        if len(question_set) == 0:
            raise ImproperlyConfigured('Question set of the quiz is empty. '
                                       'Please configure questions properly')

        if quiz.max_questions and quiz.max_questions < len(question_set):
            question_set = question_set[:quiz.max_questions]

        questions = ",".join(map(str, question_set)) + ","

        new_sitting = self.create(user=user,
                                  quiz=quiz,
                                  question_order=questions,
                                  question_list=questions,
                                  incorrect_questions="",
                                  current_score=0,
                                  complete=False,
                                  user_answers='{}')
        return new_sitting

    def user_sitting(self, user, quiz):
        if quiz.single_attempt is True and self.filter(user=user,
                                                       quiz=quiz,
                                                       complete=True) \
                .exists():
            return False

        try:
            sitting = self.get(user=user, quiz=quiz, complete=False)
        except Sitting.DoesNotExist:
            sitting = self.new_sitting(user, quiz)
        except Sitting.MultipleObjectsReturned:
            sitting = self.filter(user=user, quiz=quiz, complete=False)[0]
        return sitting

class Sitting(models.Model):
    """
    Used to store the progress of logged in users sitting a quiz.
    Replaces the session system used by anon users.
    Question_order is a list of integer pks of all the questions in the
    quiz, in order.
    Question_list is a list of integers which represent id's of
    the unanswered questions in csv format.
    Incorrect_questions is a list in the same format.
    Sitting deleted when quiz finished unless quiz.exam_paper is true.
    User_answers is a json object in which the question PK is stored
    with the answer the user gave.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name="Пользователь",
                             on_delete=models.CASCADE)

    quiz = models.ForeignKey(Quiz, verbose_name="Тест",
                             on_delete=models.CASCADE)

    question_order = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=1024, verbose_name="Порядок вопросов")

    question_list = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=1024, verbose_name="Список вопросов")

    incorrect_questions = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=1024, blank=True,
        verbose_name="Вопросы, на которые дан неверный ответ")

    current_score = models.IntegerField(verbose_name="Текущий балл")

    complete = models.BooleanField(default=False, blank=False,
                                   verbose_name="Завершен")

    user_answers = models.TextField(blank=True, default='{}',
                                    verbose_name="Ответы пользователя")

    start = models.DateTimeField(auto_now_add=True,
                                 verbose_name="Начало")

    end = models.DateTimeField(null=True, blank=True, verbose_name="Окончание")

    objects = SittingManager()

    class Meta:
        permissions = (
            ("view_sittings", "Может просматривать оконченные тесты"),)

    def get_first_question(self):
        """
        Returns the next question.
        If no question is found, returns False
        Does NOT remove the question from the front of the list.
        """
        if not self.question_list:
            return False

        first, _ = self.question_list.split(',', 1)
        question_id = int(first)
        return Question.objects.get_subclass(id=question_id)

    def remove_first_question(self):
        if not self.question_list:
            return

        _, others = self.question_list.split(',', 1)
        self.question_list = others
        self.save()

    def add_to_score(self, points):
        self.current_score += int(points)
        self.save()

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):
        return [int(n) for n in self.question_order.split(',') if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0  # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = now()
        self.save()

    def add_incorrect_question(self, question):
        """
        Adds uid of incorrect question to the list.
        The question object must be passed in.
        """
        if len(self.incorrect_questions) > 0:
            self.incorrect_questions += ','
        self.incorrect_questions += str(question.id) + ","
        if self.complete:
            self.add_to_score(-1)
        self.save()

    @property
    def get_incorrect_questions(self):
        """
        Returns a list of non empty integers, representing the pk of
        questions
        """
        return [int(q) for q in self.incorrect_questions.split(',') if q]

    def remove_incorrect_question(self, question):
        current = self.get_incorrect_questions
        current.remove(question.id)
        self.incorrect_questions = ','.join(map(str, current))
        self.add_to_score(1)
        self.save()

    @property
    def check_if_passed(self):
        return self.get_percent_correct >= self.quiz.pass_mark

    @property
    def result_message(self):
        if self.check_if_passed:
            return self.quiz.success_text
        else:
            return self.quiz.fail_text

    def add_user_answer(self, question, guess):
        current = json.loads(self.user_answers)
        current[question.id] = guess
        self.user_answers = json.dumps(current)
        self.save()

    def get_questions(self, with_answers=False):
        question_ids = self._question_ids()
        questions = sorted(
            self.quiz.question_set.filter(id__in=question_ids)
                .select_subclasses(),
            key=lambda q: question_ids.index(q.id))

        if with_answers:
            user_answers = json.loads(self.user_answers)
            for question in questions:
                question.user_answer = user_answers[str(question.id)]

        return questions

    @property
    def questions_with_user_answers(self):
        return {
            q: q.user_answer for q in self.get_questions(with_answers=True)
        }

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        """
        Returns the number of questions answered so far and the total number of
        questions.
        """
        answered = len(json.loads(self.user_answers))
        total = self.get_max_score
        return answered, total

class ProgressManager(models.Manager):

    def new_progress(self, user):
        new_progress = self.create(user=user,
                                   score="")
        new_progress.save()
        return new_progress


class Progress(models.Model):
    """
    Progress is used to track an individual signed in users score on different
    quiz's and categories
    Data stored in csv using the format:
        category, score, possible, category, score, possible, ...
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name="Пользователь",
                             on_delete=models.CASCADE)

    score = models.CharField(
        validators=[validate_comma_separated_integer_list], max_length=1024,
        verbose_name="Баллы")

    correct_answer = models.CharField(max_length=10,
                                      verbose_name='Правильные ответы')

    wrong_answer = models.CharField(max_length=10,
                                    verbose_name='Неправильные ответы')

    objects = ProgressManager()

    class Meta:
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователя"

    @property
    def list_all_cat_scores(self):
        """
        Returns a dict in which the key is the category name and the item is
        a list of three integers.
        The first is the number of questions correct,
        the second is the possible best score,
        the third is the percentage correct.
        The dict will have one key for every category that you have defined
        """
        score_before = self.score
        output = {}

        for cat in Lesson.objects.all():
            to_find = re.escape(cat.title) + r",(\d+),(\d+),"
            #  group 1 is score, group 2 is highest possible

            match = re.search(to_find, self.score, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                possible = int(match.group(2))

                try:
                    percent = int(round((float(score) / float(possible))
                                        * 100))
                except:
                    percent = 0

                output[cat.title] = [score, possible, percent]

            else:  # if category has not been added yet, add it.
                self.score += cat.title + ",0,0,"
                output[cat.title] = [0, 0]

        if len(self.score) > len(score_before):
            # If a new category has been added, save changes.
            self.save()

        return output

    def update_score(self, question, score_to_add=0, possible_to_add=0):
        """
        Pass in question object, amount to increase score
        and max possible.
        Does not return anything.
        """
        lesson_test = Lesson.objects.filter(title=question.lesson) \
            .exists()

        if any([item is False for item in [lesson_test,
                                           score_to_add,
                                           possible_to_add,
                                           isinstance(score_to_add, int),
                                           isinstance(possible_to_add, int)]]):
            return "ошибка", "урока не существует или недопустимый балл"

        to_find = re.escape(str(question.lesson)) + \
                  r",(?P<score>\d+),(?P<possible>\d+),"

        match = re.search(to_find, self.score, re.IGNORECASE)

        if match:
            updated_score = int(match.group('score')) + abs(score_to_add)
            updated_possible = int(match.group('possible')) + \
                               abs(possible_to_add)

            new_score = ",".join(
                [
                    str(question.lesson),
                    str(updated_score),
                    str(updated_possible), ""
                ])

            # swap old score for the new one
            self.score = self.score.replace(match.group(), new_score)
            self.save()

        else:
            #  if not present but existing, add with the points passed in
            self.score += ",".join(
                [
                    str(question.lesson),
                    str(score_to_add),
                    str(possible_to_add),
                    ""
                ])
            self.save()

    def show_exams(self):
        """
        Finds the previous quizzes marked as 'exam papers'.
        Returns a queryset of complete exams.
        """
        return Sitting.objects.filter(user=self.user, complete=True)

    def __str__(self):
        return self.user.username + ' - ' + self.score


ANSWER_ORDER_OPTIONS = (
    ('content', 'Содержание'),
    ('none', 'Ничего'),
    ('random', 'Случайно')
)


class MCQQuestion(Question):
    answer_order = models.CharField(
        max_length=30, null=True, blank=True,
        choices=ANSWER_ORDER_OPTIONS,
        help_text="Порядок отображения вопросов",
        verbose_name="Порядок вопросов")

    def check_if_correct(self, guess):
        answer = Answer.objects.get(id=guess)

        if answer.correct is True:
            return True
        else:
            return False

    def order_answers(self, queryset):
        if self.answer_order == 'content':
            return queryset.order_by('content')
        if self.answer_order == 'random':
            return queryset.order_by('Random')
        if self.answer_order == 'none':
            return queryset.order_by('None')

    def get_answers(self):
        return self.order_answers(Answer.objects.filter(question=self))

    def get_answers_list(self):
        return [(answer.id, answer.content) for answer in
                self.order_answers(Answer.objects.filter(question=self))]

    def answer_choice_to_string(self, guess):
        return Answer.objects.get(id=guess).content

    class Meta:
        verbose_name = "Вопрос с несколькими вариантами ответов"
        verbose_name_plural = "Вопросы с несколькими вариантами ответов"


class Answer(models.Model):
    question = models.ForeignKey(MCQQuestion, verbose_name='Вопрос',
                                 on_delete=models.CASCADE)

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text="Введите текст ответа",
                               verbose_name="Содержание")

    correct = models.BooleanField(blank=False,
                                  default=False,
                                  help_text="Это правильный ответ?",
                                  verbose_name="Правильно")

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
