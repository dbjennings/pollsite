import datetime
from django.http import response

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Question

def create_question(question_text, days=0, choices=3):
    """
    Creates a question with the given question_text, dummy choices, and a pub_date 
    offset by days (future publishing set with a positive value of days, already 
    published questions with a negative value).
    """
    time = timezone.now() + datetime.timedelta(days=days)

    question = Question.objects.create(question_text=question_text, pub_date=time)
    
    for choice in range(choices):
        question.choice_set.create(choice_text=str(choice))

    return question


# Create your tests here.
class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        Test that future questions aren't mistakenly labeled as recently published
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)


    def test_was_published_recently_with_old_question(self):
        """
        Test that questions older than a day aren't labeled as recently published
        """
        time = timezone.now() - datetime.timedelta(days=30)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)


    def test_was_published_recently_with_recent_question(self):
        """
        Test that a recently published question is correctly identified
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

class QuestionIndexViewTests(TestCase):

    def test_no_questions(self):
        """
        Test that the view handles an empty query set correctly
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No polls available')
        self.assertQuerysetEqual(response.context['latest_question_list'], [])


    def test_one_past_question(self):
        """
        Tests that past questions are published
        """
        create_question('Past question', days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'],
                                ['<Question: Past question>'])


    def test_one_future_question(self):
        """
        Tests that future questions are not published
        """
        create_question('Future question', days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'], [])


    def test_one_future_and_one_past_question(self):
        """
        Tests that 
        """
        create_question('Past question', days=-5)
        create_question('Future question', days=5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'],
                                ['<Question: Past question>'])


    def test_two_past_questions(self):
        """
        Tests the presence and order of two published polls
        """
        create_question('Past question 1', days=-30)
        create_question('Past question 2', days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'],
                                ['<Question: Past question 2>', '<Question: Past question 1>'])

class QuestionDetailViewTests(TestCase):

    def test_future_question(self):
        """
        Tests that voting is disabled for polls yet to be published
        """
        future_question = create_question('Future question', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


    def test_past_question_with_three_choices(self):
        """
        Tests that voting is enabled for published polls with a valid # of choices
        """
        past_question = create_question('Past question', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


    def test_past_question_with_one_choice(self):
        """
        Tests that past questions with less than two choices are invalid
        """
        past_question = create_question('Past question', days=-5, choices=1)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

class QuestionResultsViewTests(TestCase):

    def test_future_question(self):
        """
        Tests that viewing results is disabled for polls yet to be published
        """
        future_question = create_question('Future question', days=5)
        url = reverse('polls:results', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


    def test_past_question(self):
        """
        Tests that viewing results is enabled for published polls
        """
        past_question = create_question('Past question', days=-5)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


    def test_past_question_with_one_choice(self):
        """
        Tests that viewing results is disabled for past questions with less than two choices 
        """
        past_question = create_question('Past question', days=-5, choices=1)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
