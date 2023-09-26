from django.contrib import admin

# Register your models here.

from .models import UserProfile, GameRoom, QuizStorage, Game, AnswerInput, MatchQueue
admin.site.register(UserProfile)
admin.site.register(GameRoom)
admin.site.register(QuizStorage)
admin.site.register(Game)
admin.site.register(AnswerInput)
admin.site.register(MatchQueue)
