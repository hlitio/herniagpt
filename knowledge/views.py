from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from chat.models import Conversation

from .forms import KnowledgeTopicForm
from .models import KnowledgeCategory, KnowledgeTopic


def _require_admin(user):
    if not user.is_authenticated:
        raise PermissionDenied

    profile = getattr(user, "profile", None)
    if not profile or profile.role != "ADMIN":
        raise PermissionDenied


def _is_admin(user):
    profile = getattr(user, "profile", None)
    return bool(user.is_authenticated and profile and profile.role == "ADMIN")


@login_required
def topic_list(request):
    if _is_admin(request.user):
        topics = (
            KnowledgeTopic.objects
            .select_related("category", "created_by", "updated_by")
            .order_by("category__name", "title")
        )
    else:
        topics = (
            KnowledgeTopic.objects
            .filter(status=KnowledgeTopic.Status.PUBLISHED)
            .select_related("category", "created_by", "updated_by")
            .order_by("category__name", "title")
        )

    categories = KnowledgeCategory.objects.all()

    return render(
        request,
        "knowledge/topic_list.html",
        {
            "topics": topics,
            "categories": categories,
            "is_admin": _is_admin(request.user),
        },
    )


@login_required
def topic_detail(request, slug):
    if _is_admin(request.user):
        topic = get_object_or_404(
            KnowledgeTopic.objects.select_related("category", "created_by", "updated_by"),
            slug=slug,
        )
    else:
        topic = get_object_or_404(
            KnowledgeTopic.objects.select_related("category", "created_by", "updated_by"),
            slug=slug,
            status=KnowledgeTopic.Status.PUBLISHED,
        )

    return render(
        request,
        "knowledge/topic_detail.html",
        {
            "topic": topic,
            "is_admin": _is_admin(request.user),
        },
    )


@login_required
def start_topic_chat(request, slug):
    if _is_admin(request.user):
        topic = get_object_or_404(KnowledgeTopic, slug=slug)
    else:
        topic = get_object_or_404(
            KnowledgeTopic,
            slug=slug,
            status=KnowledgeTopic.Status.PUBLISHED,
        )

    conversation = Conversation.objects.create(
        user=request.user,
        topic=topic,
        title=topic.title[:200],
    )

    return redirect("chat:detail", pk=conversation.pk)


@login_required
def topic_create(request):
    _require_admin(request.user)

    if request.method == "POST":
        form = KnowledgeTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.created_by = request.user
            topic.updated_by = request.user
            topic.save()
            return redirect("knowledge:topic_detail", slug=topic.slug)
    else:
        form = KnowledgeTopicForm()

    return render(
        request,
        "knowledge/topic_form.html",
        {
            "form": form,
            "page_title": "Nuevo topic",
            "submit_label": "Crear topic",
            "is_edit": False,
        },
    )


@login_required
def topic_edit(request, slug):
    _require_admin(request.user)

    topic = get_object_or_404(KnowledgeTopic, slug=slug)

    if request.method == "POST":
        form = KnowledgeTopicForm(request.POST, instance=topic)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.updated_by = request.user
            topic.save()
            return redirect("knowledge:topic_detail", slug=topic.slug)
    else:
        form = KnowledgeTopicForm(instance=topic)

    return render(
        request,
        "knowledge/topic_form.html",
        {
            "form": form,
            "topic": topic,
            "page_title": "Editar topic",
            "submit_label": "Guardar cambios",
            "is_edit": True,
        },
    )