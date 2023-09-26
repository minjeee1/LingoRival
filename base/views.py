from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import GameRoom, AnswerInput, MatchQueue, UserProfile, QuizStorage
from .forms import RoomForm, SignUpForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import random
from datetime import datetime, timedelta
import openai

# ChatGPT API 키를 설정합니다.
openai.api_key = "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"

def find_and_return_alpha(input_string):
    if 'A' in input_string and 'B' in input_string:
        return False
    if 'A' in input_string:
        return 'A'
    elif 'B' in input_string:
        return 'B'
    else:
        return False

# Create your views here.

def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exist')

    context = {'page':page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user.set_password(password)
            user.save()

            # UserProfile 생성
            user_profile = UserProfile.objects.create(
                user=user,
                email=form.cleaned_data.get('email'),
                native_language=form.cleaned_data.get('native_language'),
                languages_to_learn=','.join(form.cleaned_data.get('languages_to_learn'))
            )

            # 로그인 처리
            user = authenticate(request, username=username, password=password)
            login(request, user)

            return redirect('home')  # 회원가입 후 홈 페이지로 리다이렉트
    else:
        form = SignUpForm()
    return render(request, 'base/login_register.html', {'form': form})



def home(request):
    gamerooms = GameRoom.objects.all()
    context = {'gamerooms':gamerooms}
    return render(request, 'base/home.html', context)



@login_required(login_url='login')
def gameroom(request, pk):
    gameroom = GameRoom.objects.get(id=pk)
    game_answers = gameroom.answerinput_set.all() #.order_by('-created')
    participants = gameroom.participants.all()
    selected_quiz = gameroom.quiz

    if request.method == 'POST':
        answer = AnswerInput.objects.create(
            user = request.user,
            room = gameroom,
            QnA = selected_quiz,
            body = request.POST.get('body')
        )

    
    if not participants.filter(id=request.user.id).exists():
        gameroom.participants.add(request.user)

        if gameroom.participants.all().count() >= 3:
            gameroom.participants.remove(request.user)
            raise Http404("This game room is full.")


    context = {'gameroom': gameroom, 'game_answers': game_answers, 'participants' : participants, 'selected_quiz': selected_quiz,}

    return render(request, 'base/room.html', context)


@login_required(login_url='login')
def create_game_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            gameroom = form.save(commit=False)
            gameroom.host = request.user
            gameroom.save()
            gameroom.participants.add(request.user)
            return redirect('gameroom', pk=gameroom.pk)
    else:
        form = RoomForm()

    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def exit_game_room(request, pk):
    if request.method == 'POST':
        #room_id = request.POST.get('room_id')
        # 여기에서 room_id를 사용하여 사용자를 방에서 제외하고 다른 로직을 수행합니다.

        # 예: 사용자를 방에서 제외하는 로직
        room = GameRoom.objects.get(id=pk)
        # 호스트가 이탈한 경우, 새로운 호스트 설정
        if request.user == room.host:
            remaining_participants = room.participants.exclude(id=request.user.id)
            if remaining_participants.exists():
                new_host = remaining_participants.first()
                room.host = new_host
                room.save()
        if room.participants.count() == 0:
            room.delete()

        room.participants.remove(request.user)

        # 성공 응답 반환
        return JsonResponse({'success': True})
    else:
        # 잘못된 요청에 대한 응답
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required(login_url='login')
def start_matching(request):
    # 매칭 대기열에 유저 추가
    me, created = MatchQueue.objects.get_or_create(user=request.user)
    
     # 이미 대기 중이라면 다시 대기 중 상태로
    if not created:
        me.now_waiting = True
        me.now_gaming = False
        me.last_activity = datetime.now()  # 사용자의 마지막 활동 시간 업데이트
        me.save()
    # 매칭 대기 중인 유저 목록 취득
    waiting_users = MatchQueue.objects.filter(now_waiting=True).exclude(user=request.user)

    
    # 매칭 대기 중인 유저가 충분히 많을 때 매칭을 시작합니다.
    if waiting_users.count() >= 1:
        # 두 명의 유저 선택 및 방 생성
        #user1 = request.user #MatchQueue.objects.filter(is_waiting=True).first()
        opponent = waiting_users.first()
        
        if opponent:
            # 방 생성
            nat_lang = me.user.userprofile.native_language
            tar_lang = me.user.userprofile.languages_to_learn.split(',')[0].strip()
            room = GameRoom.objects.create(host=me.user, native_language=nat_lang, 
                                            target_language=tar_lang)
            room.participants.add(me.user, opponent.user)
            room.is_waiting = False
            
            # 게임 룸에 문제 선택
            quizs = QuizStorage.objects.filter(
                from_lang=nat_lang,
                to_lang=tar_lang
            )
            
            selected_quiz = random.choice(quizs)
            
            # 문제와 게임 룸 연결
            room.quiz = selected_quiz
            room.save()    


            # 대기열에서 유저 제거
            me.now_waiting = False
            me.now_gaming = True
            me.room = room
            me.save()
            opponent.now_waiting = False
            opponent.now_gaming = True
            opponent.room = room
            opponent.save()
            
            # 방 URL 생성
            room_url = f'/room/{room.id}/'
            
            # 유저들을 방으로 리다이렉트
            return redirect(room_url)
        

    return render(request, 'base/matching_waiting.html')

@login_required(login_url='login')
def check_match(request):
    # 현재 사용자에 대한 매칭 여부를 확인하고 JSON 응답을 반환합니다.
    # 여기서 실제로는 사용자의 상태를 확인하고 매칭 여부를 판단해야 합니다.
    me = MatchQueue.objects.get(user=request.user)  # 현재 요청을 보낸 사용자
    
    # # now_waiting을 3초 동안 유지하고 그 후에 False로 설정
    # me.now_waiting = True
    # me.save()
    # time.sleep(3)  # 3초 동안 대기
    
    # me.now_waiting = False
    # me.save()
    
    if me.now_gaming:
        # 게임 중인 경우 해당 게임 방의 ID를 가져옵니다.
        room_id = me.room.id
        room_url = f'/room/{room_id}/'  # 게임 방 URL을 생성합니다.
    else:
        room_url = None
    
    response_data = {'matched': me.now_gaming, 'room_url': room_url}
    return JsonResponse(response_data)

@login_required(login_url='login')
def unset_wait(request):
    # 사용자의 now_waiting을 False로 업데이트
    me = MatchQueue.objects.get(user=request.user)
    me.now_waiting = False
    me.save()
    return JsonResponse({'success': True})
# def check_match(request):
#     # 현재 사용자에 대한 매칭 여부를 확인하고 JSON 응답을 반환합니다.
#     # 여기서 실제로는 사용자의 상태를 확인하고 매칭 여부를 판단해야 합니다.
#     me = MatchQueue.objects.get(user=request.user)  # 현재 요청을 보낸 사용자
#     # 매칭 여부를 확인하는 로직을 구현해야 합니다.
    
#     if me.now_gaming:
#         # 게임 중인 경우 해당 게임 방의 ID를 가져옵니다.
#         room_id = me.room.id
#         room_url = f'/room/{room_id}/'  # 게임 방 URL을 생성합니다.
#     else:
#         room_url = None
    
#     response_data = {'matched': me.now_gaming, 'room_url': room_url}
#     return JsonResponse(response_data)

def get_gpt_response(request, pk):#, username):
    results = []
    # 게임룸 조회
    room = get_object_or_404(GameRoom, pk=pk)
    
    # 현재 요청한 사용자 확인 (예: request.user)
    user = request.user
    #user = User.objects.get(username=username)
    answer = AnswerInput.objects.filter(user=user, room=room).first()

    # opponent 확인
    opponent = room.participants.exclude(id=user.id).first()
    opponent_answer = AnswerInput.objects.filter(user=opponent, room=room).first()
    
    # 사용자가 게임룸의 host인지 opponent인지 확인
    if user == room.host:
        role = "host"
    elif user in room.participants.all():
        role = "opponent"
    else:
        return HttpResponse("Unauthorized", status=401)
    
    # 사용자가 제출한 답변 가져오기 (예: request.POST.get('body'))
    system_message = f"이 게임은 참가자의 언어공부를 위한 번역게임이야. 참가자에게 [문제 ({room.native_language})]가 주어지고, 참가자가 그 문제를 {room.target_language}로 번역하는 게임의 참가자가 한 변역에 대해 번역이 얼마나 원어민이 자주 사용하는 표현인지, [문제]의 내용과 뉘앙스를 빠짐없이 잘 유지하였는지, 문법적으로 정확하고 자연스러운지에 번역 퀄리티를 평가하는 것이 너의 역할이야. 답변은 한국어로 부탁해"
    user_message = f"[문제 ({room.native_language})] : \"{room.quiz.Quiz}\" 라는 문제에 대해 할 수 있는 가장 완변한 번역을 먼저 해봐"
    assistant_message = f"나는 \"{room.quiz.Answer}\"이 가장 적절한 번역이라고 생각해"
    question = f"실제 게임에서 {user.username}이 제출한 번역은 \n[{user.username}님의 번역 ({room.target_language})] : \"{answer}\"이였다. \n{user.username}가 한 번역이 얼마나 좋은 번역이였는지 너가 직접한 번역을 모범답안이라고 생각하고 {user.username}님의 답변을 평가 및 설명해줘"
    
    try:
        # ChatGPT API를 호출하여 질문에 대한 답변을 받습니다.
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": question}
            ]
        )
        
        # ChatGPT 응답에서 답변 텍스트 추출
        gpt_response = response.choices[0]["message"]["content"]
        


        i=4

        # 둘다 제출 된 경우, 판정 시작
        if AnswerInput.objects.filter(room=room).count() >= 2:
            
            while i>0:
                # 사용자가 제출한 답변 가져오기 (예: request.POST.get('body'))
                system_message_eval = f"이 게임은 참가자의 언어공부를 위한 번역게임이야. 참가자에게 [문제 ({room.native_language})]가 주어지고, 참가자가 그 문제를 {room.target_language}로 번역하는 게임이야. 참가자 A와 B의 변역을 듣고 누가 승자인지 심사할거야. \n[심사기준] -번역은 주어진 문장의 의미와 내용을 빠짐없이 담으며, 문장의 뉘앙스를 최대한 유지하였는가\n- 너무 초급적인 영어표현으로 대체하여 뉘앙스를 잃지 않았는가\n- 문법적으로 정확하고 자연스러운 표현을 사용였는가\n- 영어 표현 품질이 얼마나 훌륭한가\n- 단순한 스펠링 미스는 무시한다."
                user_message_eval = f"[문제 ({room.native_language})] : \"{room.quiz.Quiz}\" 라는 문제에 대해 할 수 있는 가장 완변한 번역을 먼저 해봐"
                assistant_message_eval = f"나는 \"{room.quiz.Answer}\"이 가장 적절한 번역이라고 생각해"
                question_eval = f"참가자 A의 번역 : \"{answer}\"\n 참가자 B의 번역 : \"{opponent_answer}\" \n 둘중에 너가 직접한 번역을 모범답안이라고 생각하고 누가 승자인지 알려줘. 대답을 크롤링해서 사용할 것이 때문에, 다른 설명은 제외하고 승자의 이름만 답변해"
                

                # ChatGPT API를 호출하여 질문에 대한 답변을 받습니다.
                response_eval = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message_eval},
                        {"role": "user", "content": user_message_eval},
                        {"role": "assistant", "content": assistant_message_eval},
                        {"role": "user", "content": question_eval}
                    ]
                )
                
                # ChatGPT 응답에서 답변 텍스트 추출
                gpt_response_eval = response_eval.choices[0]["message"]["content"]
                result = find_and_return_alpha(gpt_response_eval)
                print(result)
                if result:
                    results.append(result)
                    i-=1
            # 게임룸에 답변 저장 (host_response 또는 opponent_response 필드에 저장)
            if role == "host":
                eval_results = ['h' if r == 'A' else 'o' for r in results]
                room.evaluation_results = ''.join(eval_results)
            else:
                eval_results = ['o' if r == 'A' else 'h' for r in results]
                room.evaluation_results = ''.join(eval_results)

        # 게임룸에 답변 저장 (host_response 또는 opponent_response 필드에 저장)
        if role == "host":
            room.host_response = gpt_response
                
        else:
            room.opponent_response = gpt_response
        
        room.save()

        # 응답 페이지 렌더링 (원하는 HTML 템플릿 사용)
        return redirect('home')
    
    except Exception as e:
        print(f"Error getting GPT response: {e}")
        return HttpResponse("ChatGPT Error", status=500)




def evaluate_answers(request, pk):
    gameroom = get_object_or_404(GameRoom, id=pk)

    # 현재 사용자와 상대방의 답변 가져오기
    user_answer = AnswerInput.objects.filter(user=request.user, room=gameroom).first()
    opponent = gameroom.participants.exclude(id=request.user.id).first()
    opponent_answer = AnswerInput.objects.filter(user=opponent, room=gameroom).first()

    # chatGPT 답변 가져오기
    if gameroom.host == request.user:
        user_response = gameroom.host_response
        opponent_response = gameroom.opponent_response
    else:
        user_response = gameroom.opponent_response
        opponent_response = gameroom.host_response

    # 판정 결과 가져오기
    evaluation_results = gameroom.evaluation_results

    context = {
        'gameroom': gameroom,
        'Quiz': gameroom.quiz.Quiz,
        'Answer':gameroom.quiz.Answer,
        'user_answer': user_answer,
        'opponent_answer': opponent_answer,
        'user_response': user_response,
        'opponent_response': opponent_response,
        'evaluation_results': evaluation_results
        #'winner': winner,
    }
    
    return render(request, 'base/eval.html', context)



##AJAX로 버튼눌렀을때마다 실행되게 해서 판정할수 있도록!!!

# def find_and_return_alpha(input_string):
#     # 문자열에 "A"와 "B"가 모두 들어있으면 오류 반환
#     if 'A' in input_string and 'B' in input_string:
#         raise ValueError("문자열에 'A'와 'B'가 모두 포함되어 있습니다.")

#     # 문자열에서 "A"를 찾으면 "A" 반환
#     if 'A' in input_string:
#         return 'A'

#     # 문자열에서 "B"를 찾으면 "B" 반환
#     if 'B' in input_string:
#         return 'B'

#     # 문자열에 "A"나 "B"가 없으면 오류 반환
#     raise ValueError("문자열에 'A'나 'B'가 포함되어 있지 않습니다.")

# # 테스트
# try:
#     input_string = "참가자 A가 승자입니다."
#     result = find_and_return_alpha(input_string)
#     print(f"결과: {result}")
# except ValueError as e:
#     print(f"오류: {e}")



    # # 둘다 제출 된 경우, 판정 시작
    # if AnswerInput.objects.filter(room=room).count() >= 2:
    #     # 사용자가 제출한 답변 가져오기 (예: request.POST.get('body'))
    #     system_message_eval = f"이 게임은 참가자의 언어공부를 위한 번역게임이야. 참가자에게 [문제 ({room.native_language})]가 주어지고, 참가자가 그 문제를 {room.target_language}로 번역하는 게임이야. 참가자 A와 B의 변역을 듣고 누가 승자인지 심사할거야. \n[심사기준] -번역은 주어진 문장의 의미와 내용을 빠짐없이 담으며, 문장의 뉘앙스를 최대한 유지하였는가\n- 너무 초급적인 영어표현으로 대체하여 뉘앙스를 잃지 않았는가\n- 문법적으로 정확하고 자연스러운 표현을 사용였는가\n- 영어 표현 품질이 얼마나 훌륭한가\n- 단순한 스펠링 미스는 무시한다."
    #     user_message_eval = f"[문제 ({room.native_language})] : \"{room.quiz.Quiz}\" 라는 문제에 대해 할 수 있는 가장 완변한 번역을 먼저 해봐"
    #     assistant_message_eval = f"나는 \"{room.quiz.Answer}\"이 가장 적절한 번역이라고 생각해"
    #     question_eval = f"참가자 A의 번역 : \"{answer}\"\n 참가자 B의 번역 : \"{opponent_answer}\" \n 둘중에 너가 직접한 번역을 모범답안이라고 생각하고 누가 승자인지 알려줘. 대답을 크롤링해서 사용할 것이 때문에, 다른 설명은 제외하고 승자의 이름만 답변해"
        
    #     try:
    #         # ChatGPT API를 호출하여 질문에 대한 답변을 받습니다.
    #         response_eval = openai.ChatCompletion.create(
    #             model="gpt-3.5-turbo",
    #             messages=[
    #                 {"role": "system", "content": system_message_eval},
    #                 {"role": "user", "content": user_message_eval},
    #                 {"role": "assistant", "content": assistant_message_eval},
    #                 {"role": "user", "content": question_eval}
    #             ]
    #         )
            
    #         # ChatGPT 응답에서 답변 텍스트 추출
    #         try:
    #             gpt_response_eval = response_eval.choices[0]["message"]["content"]
    #             gpt_response_result = find_and_return_alpha(gpt_response_eval)
    #             print(f"결과: {gpt_response_result}")
    #         except ValueError as e:
    #             print(f"오류: {e}")
                
    #     except Exception as e:
    #         print(f"Error getting GPT response: {e}")
    #         return HttpResponse("ChatGPT Error", status=500)