from django.core.exceptions import ValidationError
from django.test import TestCase

from main.models import Lesson, Rubric, AdvUser
from quiz.models import Quiz, MCQQuestion


class TestQuiz(TestCase):
    def setUp(self):
        self.user = AdvUser.objects.create(username='testuser1')
        self.superrub = Rubric.objects.create(name='super',
                                              super_rubric=None)
        self.rub = Rubric.objects.create(name='sub',
                                         super_rubric_id=self.superrub.id)
        self.c1 = Lesson.objects.create(rubric_id=self.rub.id, title='test',
                                        video='asd', author_id=self.user.id)

        self.quiz1 = Quiz.objects.create(id=1,
                                         title='test quiz 1',
                                         description='d1',
                                         url='tq1')
        self.quiz2 = Quiz.objects.create(id=2,
                                         title='test quiz 2',
                                         description='d2',
                                         url='t q2')
        self.quiz3 = Quiz.objects.create(id=3,
                                         title='test quiz 3',
                                         description='d3',
                                         url='t   q3')
        self.quiz4 = Quiz.objects.create(id=4,
                                         title='test quiz 4',
                                         description='d4',
                                         url='T-!£$%^&*Q4')

        self.question1 = MCQQuestion.objects.create(id=1,
                                                    content='squawk')
        self.question1.quiz.add(self.quiz1)

    def test_quiz_url(self):
        self.assertEqual(self.quiz1.url, 'tq1')
        self.assertEqual(self.quiz2.url, 't-q2')
        self.assertEqual(self.quiz3.url, 't-q3')
        self.assertEqual(self.quiz4.url, 't-q4')

    def test_quiz_options(self):
        q5 = Quiz.objects.create(id=5,
                                 title='test quiz 5',
                                 description='d5',
                                 url='tq5',
                                 lesson=self.c1)

        self.assertEqual(q5.lesson.title, self.c1.title)
        self.assertEqual(q5.random_order, False)
        self.assertEqual(q5.answers_at_end, False)

    def test_pass_mark(self):
        self.assertEqual(self.quiz1.pass_mark, False)
        self.quiz1.pass_mark = 50
        self.assertEqual(self.quiz1.pass_mark, 50)
        self.quiz1.pass_mark = 101
        with self.assertRaises(ValidationError):
            self.quiz1.save()
