from django.contrib import admin

from .models import Calendar, HebrewDate


class CommentInline(admin.TabularInline):
    model = HebrewDate


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    inlines = [
        CommentInline,
    ]


admin.site.register(HebrewDate)
