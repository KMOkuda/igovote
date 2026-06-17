from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Kifu, Comment, Tag, KifuTag, KifuLike, CommentLike


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('プロフィール', {'fields': ('avatar', 'bio')}),
    )


class KifuTagInline(admin.TabularInline):
    model = KifuTag
    extra = 1


@admin.register(Kifu)
class KifuAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'visibility', 'like_count', 'comment_count', 'created_at')
    list_filter = ('visibility', 'created_at')
    search_fields = ('title', 'user__username', 'black_player', 'white_player')
    inlines = [KifuTagInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('kifu', 'user', 'move_number', 'body', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('body', 'user__username', 'kifu__title')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(KifuLike)
admin.site.register(CommentLike)
