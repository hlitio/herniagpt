from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Conversation, Message


@login_required
def chat_home(request):
    conversations = Conversation.objects.filter(user=request.user)

    conversation = conversations.first()

    if conversation is None:
        conversation = Conversation.objects.create(
            user=request.user,
            title="Nuevo chat",
        )
        conversations = Conversation.objects.filter(user=request.user)

    return render(
        request,
        "chat/chat.html",
        {
            "conversations": conversations,
            "conversation": conversation,
        },
    )


@login_required
def conversation_detail(request, pk: int):
    conversations = Conversation.objects.filter(user=request.user)
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        user=request.user,
    )

    return render(
        request,
        "chat/chat.html",
        {
            "conversations": conversations,
            "conversation": conversation,
        },
    )


@login_required
@require_POST
def conversation_create(request):
    conversation = Conversation.objects.create(
        user=request.user,
        title="Nuevo chat",
    )
    return redirect("chat:detail", pk=conversation.pk)


@login_required
@require_POST
def send_message(request, pk: int):
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        user=request.user,
    )

    content = (request.POST.get("content") or "").strip()
    if not content:
        return redirect("chat:detail", pk=conversation.pk)

    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=content,
    )

    if conversation.title == "Nuevo chat":
        conversation.title = content[:40]
        conversation.save(update_fields=["title", "updated_at"])

    assistant_reply = f"Recibí tu mensaje: {user_message.content}"

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=assistant_reply,
    )

    return redirect("chat:detail", pk=conversation.pk)