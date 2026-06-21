from django.urls import path
from . import views
from . import auth_views

app_name = 'kifu_app'

urlpatterns = [
    # 公開ページ
    path('', views.top, name='top'),
    path('kifu/<int:kifu_id>/', views.kifu_detail, name='kifu_detail'),
    path('search/', views.search, name='search'),

    # 要ログイン
    path('kifu/create/', views.kifu_create, name='kifu_create'),
    path('kifu/<int:kifu_id>/delete/', views.kifu_delete, name='kifu_delete'),
    path('kifu/<int:kifu_id>/visibility/', views.kifu_visibility, name='kifu_visibility'),
    path('mypage/', views.mypage, name='mypage'),
    path('mypage/avatar/', views.update_avatar, name='update_avatar'),

    # API（Ajax）
    path('api/kifu/<int:kifu_id>/comments/', views.api_comments, name='api_comments'),
    path('api/kifu/<int:kifu_id>/comment/', views.api_comment_post, name='api_comment_post'),
    path('api/comment/<int:comment_id>/like/', views.api_comment_like, name='api_comment_like'),
    path('api/kifu/<int:kifu_id>/like/', views.api_kifu_like, name='api_kifu_like'),

    # 認証
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),
    path('verify-email/<uidb64>/<token>/', auth_views.verify_email_view, name='verify_email'),
]
