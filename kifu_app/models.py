from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """カスタムユーザー"""

    class Rank(models.TextChoices):
        BEGINNER = 'beginner', '初心者'
        KYU = 'kyu', '級位者'
        DAN = 'dan', '段位者'
        PRO = 'pro', 'プロ'

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, default='')
    rank = models.CharField(max_length=20, choices=Rank.choices, blank=True, default='')

    class Meta:
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'

    def __str__(self):
        return self.username


class Tag(models.Model):
    """タグ"""
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'タグ'
        verbose_name_plural = 'タグ'

    def __str__(self):
        return self.name


class Kifu(models.Model):
    """棋譜"""

    class Visibility(models.TextChoices):
        PUBLIC = 'public', '公開'
        PRIVATE = 'private', '非公開'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='kifus'
    )
    title = models.CharField(max_length=200)
    sgf_data = models.TextField()
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    # 対局情報（SGFから自動抽出 or 手入力）
    black_player = models.CharField(max_length=100, blank=True, default='')
    white_player = models.CharField(max_length=100, blank=True, default='')
    black_rank = models.CharField(max_length=20, choices=User.Rank.choices, blank=True, default='')
    white_rank = models.CharField(max_length=20, choices=User.Rank.choices, blank=True, default='')
    result = models.CharField(max_length=50, blank=True, default='')
    komi = models.FloatField(null=True, blank=True)
    handicap = models.IntegerField(default=0)

    # 一覧表示用にハイライトする手数（未設定なら最終局面を表示）
    highlight_move = models.PositiveIntegerField(null=True, blank=True)

    tags = models.ManyToManyField(Tag, through='KifuTag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '棋譜'
        verbose_name_plural = '棋譜'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def like_count(self):
        return self.kifu_likes.count()

    @property
    def comment_count(self):
        return self.comments.count()


class KifuTag(models.Model):
    """棋譜-タグ中間テーブル"""
    kifu = models.ForeignKey(Kifu, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('kifu', 'tag')


class Comment(models.Model):
    """コメント（着手番号に紐付く）"""
    kifu = models.ForeignKey(
        Kifu, on_delete=models.CASCADE, related_name='comments'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )
    move_number = models.IntegerField(default=0)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'コメント'
        verbose_name_plural = 'コメント'
        ordering = ['move_number', 'created_at']

    def __str__(self):
        return f'{self.kifu.title} @ {self.move_number}: {self.body[:30]}'

    @property
    def like_count(self):
        return self.comment_likes.count()


class KifuLike(models.Model):
    """棋譜いいね"""
    kifu = models.ForeignKey(
        Kifu, on_delete=models.CASCADE, related_name='kifu_likes'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='kifu_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('kifu', 'user')


class CommentLike(models.Model):
    """コメントいいね"""
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name='comment_likes'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comment_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')
