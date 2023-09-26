from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# 언어 선택 옵션
LANGUAGE_CHOICES = [
    ('english', 'english'),
    ('japanese', 'japanese'),
    ('korean', 'korean')
    # 다른 언어를 필요에 따라 추가할 수 있습니다.
]


# 사용자 모델
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()  # 이메일 주소 필드
    native_language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)  # 모국어 선택
    # 배우고 싶은 언어 필드 (쉼표로 구분된 문자열)
    languages_to_learn = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username


class QuizStorage(models.Model):
    from_lang = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)
    to_lang = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)
    Quiz = models.TextField()  # 문제 텍스트
    Answer = models.TextField()  # 답변 텍스트


# 방 모델
class GameRoom(models.Model):
    id = models.AutoField(primary_key=True)
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    quiz = models.ForeignKey(QuizStorage, on_delete=models.CASCADE, default=None, null=True, blank=True)  # 어떤 문제에 대한 답변인지
    is_waiting = models.BooleanField(default=True)  # 게임 시작 여부
    native_language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)  # 모국어 선택
    target_language = models.CharField(max_length=255)  # 학습 언어 선택

    # 각 참가자의 답변 필드 추가
    host_response = models.TextField(null=True)
    opponent_response = models.TextField(null=True)

    # 평가 및 결과 필드 추가
    evaluation_results = models.CharField(max_length=5, default="")  # "hoohh", "host wins", "opponent wins" 등으로 결과 저장

    class Meta:
        ordering = ['-is_waiting']

    def __str__(self):
        return f"Room {self.id}"


class MatchQueue(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    now_waiting = models.BooleanField(default=True)  # 대기 중 여부
    now_gaming = models.BooleanField(default=False)  # 게임 중 여부
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)  # 새로운 필드 추가
    
    def __str__(self):
        return self.user.username


# 게임 모델
class Game(models.Model):
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE)
    sentence = models.TextField()  # 게임 문장
    translation = models.TextField()  # 번역
    is_winner = models.BooleanField(default=False)  # 승리 여부

    def __str__(self):
        return f"Game in Room: {self.room.id}"


class AnswerInput(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 유저와의 관계
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE)  # 어떤 게임방에서 생성된 답변인지
    QnA = models.ForeignKey(QuizStorage, on_delete=models.CASCADE, default=None)  # 어떤 문제에 대한 답변인지
    body = models.TextField(blank=True, null=True)  # 유저의 답변
    def __str__(self):
        return self.body
