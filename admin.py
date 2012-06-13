from django.contrib import admin

"""
Some admin actions for bulk publishing/drafting records
"""

def make_published(modeladmin, request, queryset):
    queryset.update(status='1')

make_published.short_description = "Mark selected items as published"

def make_draft(modeladmin, request, queryset):
    queryset.update(status='0')

make_draft.short_description = "Mark selected items as draft"

admin.site.add_action(make_published)
admin.site.add_action(make_draft)