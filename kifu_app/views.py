import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count

from .models import Kifu, Comment, Tag, KifuLike, CommentLike


# ------------------------------------------------------------------ #
# 公開ページ
# ------------------------------------------------------------------ #

def top(request):
    """トップ：最新の公開棋譜一覧"""
    kifus = (
        Kifu.objects
        .filter(visibility='public')
        .select_related('user')
        .prefetch_related('tags')[:30]
    )
    return render(request, 'kifu_app/top.html', {'kifus': kifus})


def kifu_detail(request, kifu_id):
    """棋譜詳細"""
    kifu = get_object_or_404(Kifu, pk=kifu_id)

    # 非公開棋譜は投稿者本人のみ閲覧可
    if kifu.visibility == 'private' and kifu.user != request.user:
        return redirect('kifu_app:top')

    comments = kifu.comments.select_related('user').all()

    # ログイン済みならいいね状態を取得
    user_liked_kifu = False
    liked_comment_ids = set()
    if request.user.is_authenticated:
        user_liked_kifu = KifuLike.objects.filter(
            kifu=kifu, user=request.user
        ).exists()
        liked_comment_ids = set(
            CommentLike.objects.filter(
                comment__kifu=kifu, user=request.user
            ).values_list('comment_id', flat=True)
        )

    return render(request, 'kifu_app/kifu_detail.html', {
        'kifu': kifu,
        'comments': comments,
        'user_liked_kifu': user_liked_kifu,
        'liked_comment_ids': liked_comment_ids,
    })


def search(request):
    """棋譜検索（「#タグ名」はタグ検索、それ以外はキーワード検索。すべてAND条件）"""
    query = request.GET.get('q', '').strip()
    tokens = query.split()
    tag_names = [t[1:] for t in tokens if t.startswith('#') and len(t) > 1]
    keywords = [t for t in tokens if not t.startswith('#')]

    kifus = Kifu.objects.filter(visibility='public').select_related('user').prefetch_related('tags')

    for tag_name in tag_names:
        kifus = kifus.filter(tags__name__icontains=tag_name)
    if tag_names:
        kifus = kifus.distinct()

    for word in keywords:
        kifus = kifus.filter(
            Q(title__icontains=word) |
            Q(black_player__icontains=word) |
            Q(white_player__icontains=word)
        )

    popular_tags = (
        Tag.objects.annotate(num_kifus=Count('kifu'))
        .filter(num_kifus__gt=0)
        .order_by('-num_kifus')[:10]
    )

    return render(request, 'kifu_app/search.html', {
        'kifus': kifus[:50],
        'query': query,
        'popular_tags': popular_tags,
    })


# ------------------------------------------------------------------ #
# 要ログインページ
# ------------------------------------------------------------------ #

@login_required
def kifu_create(request):
    """棋譜投稿"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        sgf_data = request.POST.get('sgf_data', '').strip()
        visibility = request.POST.get('visibility', 'public')
        tag_input = request.POST.get('tags', '')

        if title and sgf_data:
            kifu = Kifu.objects.create(
                user=request.user,
                title=title,
                sgf_data=sgf_data,
                visibility=visibility,
                black_player=request.POST.get('black_player', ''),
                white_player=request.POST.get('white_player', ''),
                event_name=request.POST.get('event_name', ''),
                result=request.POST.get('result', ''),
                komi=request.POST.get('komi') or None,
                handicap=request.POST.get('handicap', 0),
            )
            # タグ処理
            for tag_name in [t.strip() for t in tag_input.split(',') if t.strip()]:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                kifu.tags.add(tag)

            return redirect('kifu_app:kifu_detail', kifu_id=kifu.pk)

    return render(request, 'kifu_app/kifu_create.html')


@login_required
@require_POST
def kifu_delete(request, kifu_id):
    """棋譜削除（投稿者のみ）"""
    kifu = get_object_or_404(Kifu, pk=kifu_id, user=request.user)
    kifu.delete()
    return redirect('kifu_app:mypage')


@login_required
@require_POST
def kifu_visibility(request, kifu_id):
    """公開範囲変更（投稿者のみ）"""
    kifu = get_object_or_404(Kifu, pk=kifu_id, user=request.user)
    new_visibility = request.POST.get('visibility')
    if new_visibility in ('public', 'private'):
        kifu.visibility = new_visibility
        kifu.save(update_fields=['visibility'])
    return JsonResponse({'visibility': kifu.visibility})


@login_required
def mypage(request):
    """マイページ"""
    kifus = (
        request.user.kifus
        .prefetch_related('tags')
        .all()
    )
    return render(request, 'kifu_app/mypage.html', {'kifus': kifus})


@login_required
@require_POST
def update_avatar(request):
    """アバター画像の更新"""
    avatar = request.FILES.get('avatar')
    if avatar:
        request.user.avatar = avatar
        request.user.save(update_fields=['avatar'])
    return redirect('kifu_app:mypage')


# ------------------------------------------------------------------ #
# API（Ajax）
# ------------------------------------------------------------------ #

def api_comments(request, kifu_id):
    """コメント一覧取得"""
    kifu = get_object_or_404(Kifu, pk=kifu_id)
    comments = kifu.comments.select_related('user').all()
    data = [
        {
            'id': c.pk,
            'user': c.user.username,
            'avatar': c.user.avatar.url if c.user.avatar else None,
            'move_number': c.move_number,
            'body': c.body,
            'like_count': c.like_count,
            'created_at': c.created_at.strftime('%Y.%m.%d'),
        }
        for c in comments
    ]
    return JsonResponse({'comments': data})


@login_required
@require_POST
def api_comment_post(request, kifu_id):
    """コメント投稿"""
    kifu = get_object_or_404(Kifu, pk=kifu_id)
    try:
        body_data = json.loads(request.body)
        body = body_data.get('body', '').strip()
        move_number = int(body_data.get('move_number', 0))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'invalid'}, status=400)

    if not body:
        return JsonResponse({'error': 'empty'}, status=400)

    comment = Comment.objects.create(
        kifu=kifu,
        user=request.user,
        move_number=move_number,
        body=body,
    )
    return JsonResponse({
        'id': comment.pk,
        'user': comment.user.username,
        'move_number': comment.move_number,
        'body': comment.body,
        'like_count': 0,
        'created_at': comment.created_at.strftime('%Y.%m.%d'),
    }, status=201)


@login_required
@require_POST
def api_comment_like(request, comment_id):
    """コメントいいねトグル"""
    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = CommentLike.objects.get_or_create(
        comment=comment, user=request.user
    )
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'like_count': comment.like_count})


@login_required
@require_POST
def api_kifu_like(request, kifu_id):
    """棋譜いいねトグル"""
    kifu = get_object_or_404(Kifu, pk=kifu_id)
    like, created = KifuLike.objects.get_or_create(
        kifu=kifu, user=request.user
    )
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'like_count': kifu.like_count})
