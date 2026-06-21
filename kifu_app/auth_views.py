from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse


def login_view(request):
    if request.user.is_authenticated:
        return redirect('kifu_app:top')

    if request.method == 'POST':
        from .models import User
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'kifu_app:top')
            return redirect(next_url)

        if User.objects.filter(username=username, is_active=False).exists():
            messages.error(request, 'メール認証が完了していません。登録時に送信されたメールをご確認ください')
        else:
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
        elif not email:
            error = 'メールアドレスを入力してください'
        elif User.objects.filter(email=email).exists():
            error = 'このメールアドレスは既に使われています'
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
                is_active=False,
            )
            send_verification_email(request, user)
            messages.success(request, '確認メールを送信しました。メール内のリンクをクリックして登録を完了してください')
            return redirect('kifu_app:login')

    return render(request, 'kifu_app/register.html')


def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_path = reverse('kifu_app:verify_email', kwargs={'uidb64': uid, 'token': token})
    verify_url = request.build_absolute_uri(verify_path)

    send_mail(
        subject='【囲碁SNS】メールアドレスの確認',
        message=(
            f'{user.username} 様\n\n'
            'ご登録ありがとうございます。以下のリンクをクリックして、登録を完了してください。\n\n'
            f'{verify_url}\n\n'
            'このメールに心当たりがない場合は、本メールを破棄してください。'
        ),
        from_email=None,
        recipient_list=[user.email],
    )


def verify_email_view(request, uidb64, token):
    from .models import User
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        login(request, user)
        messages.success(request, 'メール認証が完了しました')
        return redirect('kifu_app:top')

    messages.error(request, 'リンクが無効か期限切れです')
    return redirect('kifu_app:login')
