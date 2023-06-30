from django.contrib import admin

from .models import Calendar, HebrewDate


class CommentInline(admin.TabularInline):
    model = HebrewDate


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    inlines = [
        CommentInline,
    ]
    list_display = ("name", "display_uuid")  # Include the display_uuid method in list_display

    @admin.display(description="UUID")
    def display_uuid(self, obj):
        return obj.uuid  # Display the UUID field value


admin.site.register(HebrewDate)
