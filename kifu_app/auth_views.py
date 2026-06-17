from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect('kifu_app:top')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'kifu_app:top')
            return redirect(next_url)
        messages.error(request, 'ユーザー名またはパスワードが違います')

    return render(request, 'kifu_app/login.html')


def logout_view(request):
    logout(request)
    return redirect('kifu_app:top')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('kifu_app:top')

    if request.method == 'POST':
        from .models import User
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        error = None
        if not username:
            error = 'ユーザー名を入力してください'
        elif User.objects.filter(username=username).exists():
            error = 'このユーザー名は既に使われています'
        elif password != password2:
            error = 'パスワードが一致しません'
        elif len(password) < 8:
            error = 'パスワードは8文字以上にしてください'

        if error:
            messages.error(request, error)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            login(request, user)
            return redirect('kifu_app:top')

    return render(request, 'kifu_app/register.html')
