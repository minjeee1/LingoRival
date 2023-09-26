from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('signup/', views.signup, name="signup"),

    path('', views.home, name="home"),

    path('start_matching/', views.start_matching, name='start_matching'),
    path('room/<str:pk>/', views.gameroom, name="gameroom"),
    path('check_match/', views.check_match, name='check-match'),
    #path('profile/<str:pk>', views.userProfile, name='user-profile'),
    path('unset_wait/', views.unset_wait, name='unset_wait'),
    path('room/<str:pk>/submit/', views.get_gpt_response, name='submit'),
    #path('room/<str:pk>/submit/<str:username>/', views.get_gpt_response, name='submit'),

    path('room/<str:pk>/eval/', views.evaluate_answers, name='eval'),

    
    path('create_game_room/', views.create_game_room, name='create-game-room'),
    path('room/<str:pk>/exit/', views.exit_game_room, name='exit-game-room'),
    #path('join_room/<int:room_id>/', views.join_room, name='join_room'),
    #path('game_room/<int:room_id>/', views.game_room, name='game_room'),
    #path('room_full/', views.room_full, name='room_full'),  # 방이 가득 찼을 때 표시할 페이지
]