from django.http import HttpResponse
from django.contrib import admin
import csv
from .models import UserRequestTrack, PromptUpdateTrack

@admin.register(UserRequestTrack)
class UserRequestTrackAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'timestamp',
        'difficulty',
        'question_type',
        'topic',
        'subtopic',
        'question_count',
        'input_token',
        'output_token',
    )
    list_filter = (
        'difficulty',
        'question_type',
        'topic',
        'subtopic',
        'timestamp',
    )
    search_fields = (
        'user__username',
        'question_type',
        'topic',
        'subtopic',
    )
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

@admin.register(PromptUpdateTrack)
class PromptUpdateTrackAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'timestamp',
        'short_original_prompt',
        'short_updated_prompt',
        'content_type'
    )
    list_filter = (
        'user',
        'content_type'
    )
    search_fields = (
        'user__username',
        'content_type'
    )
    ordering = ('-timestamp', '-user')
    readonly_fields = ('timestamp',)

    def short_original_prompt(self, obj):
        return f'{obj.original_prompt[:50]}...' if len(obj.original_prompt) > 50 else obj.original_prompt

    short_original_prompt.short_description = 'Original Prompt'

    def short_updated_prompt(self, obj):
        return f'{obj.updated_prompt[:50]}...' if len(obj.updated_prompt) > 50 else obj.updated_prompt

    short_updated_prompt.short_description = 'Updated Prompt'

    # Add export to CSV functionality
    actions = ['export_to_csv']

    def export_to_csv(self, request, queryset):
        # Define the response and set the CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="prompt_update_track_data.csv"'

        # Create a CSV writer object
        writer = csv.writer(response)

        # Write the header row (field names of the model)
        writer.writerow(['User', 'Timestamp', 'Original Prompt', 'Updated Prompt', 'Content Type'])

        # Write the data rows (values of the model's fields)
        for obj in queryset:
            writer.writerow(
                [obj.user.username, obj.timestamp, obj.original_prompt, obj.updated_prompt, obj.content_type])

        return response

    export_to_csv.short_description = "Export Selected Rows to CSV"
