from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import F, Count
from django.views import generic
from django.utils import timezone
from .models import Question, Choice

# Create your views here.
class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published poll questions (not including those set
        to be published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]
    

class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Only allow for past (published) polls to be voted on
        """
        return Question.objects.annotate(num_choices=Count('choice')
            ).filter(num_choices__gt=1
            ).filter(pub_date__lte=timezone.now()
        )
    

class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

    def get_queryset(self):
        """
        Only allow for past (published) polls to be viewed
        """
        return Question.objects.annotate(num_choices=Count('choice')
            ).filter(num_choices__gt=1
            ).filter(pub_date__lte=timezone.now()
        )
    

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        # Attempt to capture the selected choice
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redirect to the voting page with an attached error_message
        context = {'question_id': question_id,'error_message':'No choice selected.'}
        render(request, 'polls/detail.html', context)
    else:
        # Add a vote to the selected choice
        # Avoid race conditions with F()
        selected_choice.votes = F('votes') + 1
        selected_choice.save()

        return HttpResponseRedirect(reverse('polls:results', args=(question_id,)))