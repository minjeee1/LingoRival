from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GameRoom, UserProfile

class RoomForm(forms.ModelForm):
    class Meta:
        model = GameRoom
        fields = '__all__'
        exclude = ['host', 'participants', 'is_waiting']

# 사용 가능한 언어 선택 옵션
LANGUAGE_CHOICES = [
    ('english', 'English'),
    ('japanese', 'Japanese'),
    ('korean', 'Korean'),
    # 다른 언어를 필요에 따라 추가할 수 있습니다.
]

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Enter a valid email address.')
    native_language = forms.ChoiceField(choices=LANGUAGE_CHOICES, required=True)
    
    # 배우고 싶은 언어를 다중 선택할 수 있는 필드
    languages_to_learn = forms.MultipleChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'native_language', 'languages_to_learn')