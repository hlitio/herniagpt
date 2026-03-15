from django.contrib import admin

from .models import KnowledgeCategory, KnowledgeTopic


@admin.register(KnowledgeCategory)
class KnowledgeCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(KnowledgeTopic)
class KnowledgeTopicAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "created_by", "updated_at")
    list_filter = ("status", "category")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}