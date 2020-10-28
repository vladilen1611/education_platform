from django.urls import path
from .views import main,profile,RegisterUserView,LWMLoginView,RegisterDoneView,LWMLogoutView,LWMPasswordChangeView,ChangeUserInfoView,by_rubric,project,DeleteUserView,profile_lesson_add,profile_lesson_change,profile_lesson_delete,profile_lesson_detail,detail




urlpatterns = [
    path('<int:rubric_pk>/<int:pk>/', detail, name='detail'),
    path('<int:pk>/', by_rubric, name='by_rubric'),
    path('', main, name='main'),
    path('projects/<int:pk>/', project, name='project'),
]

urlpatterns+=[
    path('accounts/login/', LWMLoginView.as_view(), name='login'),
    path('accounts/logout/', LWMLogoutView.as_view(), name='logout'),
    path('accounts/register/', RegisterUserView.as_view(), name='register'),
    path('accounts/register/done/', RegisterDoneView.as_view(),
         name='register_done'),
    path('accounts/password/change/', LWMPasswordChangeView.as_view(),
         name='password_change'),
    path('accounts/profile/change/', ChangeUserInfoView.as_view(),
         name='profile_change'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/profile/delete/', DeleteUserView.as_view(),
         name='profile_delete'),
    path('accounts/profile/add/', profile_lesson_add,
         name='profile_lesson_add'),

    path('accounts/profile/change/<int:pk>/', profile_lesson_change,
         name='profile_lesson_change'),
    path('accounts/profile/delete/<int:pk>/', profile_lesson_delete,
         name='profile_lesson_delete'),
    path('accounts/profile/<int:pk>/', profile_lesson_detail,
         name='profile_lesson_detail'),
]