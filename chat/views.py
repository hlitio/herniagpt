from __future__ import annotations

import json
import logging
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from openai import OpenAI

from .models import Conversation, Message


logger = logging.getLogger(__name__)

LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "qwen2.5-7b-instruct")
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", "lm-studio")

TOPIC_CHAT_MAX_HISTORY_MESSAGES = 6
FREE_CHAT_MAX_HISTORY_MESSAGES = 12


def _build_lmstudio_client() -> OpenAI:
    return OpenAI(
        base_url=LM_STUDIO_BASE_URL,
        api_key=LM_STUDIO_API_KEY,
    )


def _serialize_conversation(conv: Conversation) -> dict:
    return {
        "id": conv.pk,
        "title": conv.title,
        "detail_url": f"/chat/{conv.pk}/",
    }


def _normalize_role(role: str | None) -> str:
    role = (role or "").lower()
    if role not in {"system", "user", "assistant"}:
        return "user"
    return role


def _get_recent_messages(conversation: Conversation, limit: int) -> list[Message]:
    message_ids = list(
        conversation.messages.order_by("-created_at", "-id")
        .values_list("id", flat=True)[:limit]
    )

    if not message_ids:
        return []

    return list(
        conversation.messages.filter(id__in=message_ids).order_by("created_at", "id")
    )


def _build_topic_system_prompt(conversation: Conversation) -> str:
    topic = conversation.topic

    return (
        "Sos HerniaGPT, asistente interno de la empresa.\n\n"
        "Estás respondiendo preguntas sobre un topic corporativo oficial.\n\n"
        "Reglas obligatorias:\n"
        "1. Basate principalmente en el contenido del topic provisto.\n"
        "2. No inventes información que no esté respaldada por el topic.\n"
        "3. Si la respuesta no surge claramente del topic, decilo explícitamente.\n"
        "4. Usá el historial del chat solo para entender continuidad o referencias.\n"
        "5. Respondé en español, de forma clara, precisa y útil.\n"
        "6. Si el usuario pide un resumen o una reformulación, hacelo solo a partir del topic.\n\n"
        f"TÍTULO DEL TOPIC:\n{topic.title}\n\n"
        f"RESUMEN DEL TOPIC:\n{topic.summary or 'Sin resumen.'}\n\n"
        f"CONTENIDO DEL TOPIC:\n{topic.content}\n"
    )


def _build_free_chat_system_prompt() -> str:
    return (
        "Sos HerniaGPT, un asistente útil, claro y preciso. "
        "Respondé en español salvo que el usuario pida otro idioma."
    )


def _build_history(conversation: Conversation) -> list[dict]:
    history: list[dict] = []

    if conversation.topic_id:
        history.append(
            {
                "role": "system",
                "content": _build_topic_system_prompt(conversation),
            }
        )
        recent_messages = _get_recent_messages(
            conversation,
            TOPIC_CHAT_MAX_HISTORY_MESSAGES,
        )
    else:
        history.append(
            {
                "role": "system",
                "content": _build_free_chat_system_prompt(),
            }
        )
        recent_messages = _get_recent_messages(
            conversation,
            FREE_CHAT_MAX_HISTORY_MESSAGES,
        )

    for msg in recent_messages:
        history.append(
            {
                "role": _normalize_role(msg.role),
                "content": msg.content,
            }
        )

    return history


def _generate_assistant_reply(conversation: Conversation) -> str:
    client = _build_lmstudio_client()
    history = _build_history(conversation)

    response = client.chat.completions.create(
        model=LM_STUDIO_MODEL,
        messages=history,
        temperature=0.7,
    )

    choice = response.choices[0]
    content = choice.message.content if choice.message else None

    if not content:
        return "No pude generar una respuesta en este momento."

    return content.strip()


@login_required
def chat_home(request):
    conversations = Conversation.objects.filter(user=request.user).order_by("-updated_at", "-id")
    conversation = conversations.first()

    if conversation is None:
        conversation = Conversation.objects.create(
            user=request.user,
            title="Nuevo chat",
        )
        conversations = Conversation.objects.filter(user=request.user).order_by("-updated_at", "-id")

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
    conversations = Conversation.objects.filter(user=request.user).order_by("-updated_at", "-id")
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

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "conversation": _serialize_conversation(conversation),
            }
        )

    return redirect("chat:detail", pk=conversation.pk)


@login_required
@require_POST
def conversation_rename(request, pk: int):
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        user=request.user,
    )

    title = (request.POST.get("title") or "").strip()

    if not title:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"ok": False, "error": "El nombre no puede estar vacío."},
                status=400,
            )
        return redirect("chat:detail", pk=conversation.pk)

    conversation.title = title[:120]
    conversation.save(update_fields=["title", "updated_at"])

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "conversation": _serialize_conversation(conversation),
            }
        )

    return redirect("chat:detail", pk=conversation.pk)


@login_required
@require_POST
def conversation_delete(request, pk: int):
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        user=request.user,
    )

    conversation.delete()

    next_conversation = (
        Conversation.objects.filter(user=request.user)
        .order_by("-updated_at", "-id")
        .first()
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "redirect_url": (
                    f"/chat/{next_conversation.pk}/" if next_conversation else "/chat/"
                ),
            }
        )

    if next_conversation:
        return redirect("chat:detail", pk=next_conversation.pk)

    return redirect("chat:home")


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
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"ok": False, "error": "El mensaje no puede estar vacío."},
                status=400,
            )
        return redirect("chat:detail", pk=conversation.pk)

    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=content,
    )

    if conversation.title == "Nuevo chat":
        conversation.title = content[:40]
        conversation.save(update_fields=["title", "updated_at"])

    try:
        assistant_reply = _generate_assistant_reply(conversation)
    except Exception:
        logger.exception("Error consultando LM Studio")
        assistant_reply = (
            "Hubo un problema al consultar el modelo local en LM Studio. "
            "Verificá que el servidor esté iniciado, que haya un modelo cargado "
            "y que la URL configurada sea correcta."
        )

    assistant_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=assistant_reply,
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "conversation": _serialize_conversation(conversation),
                "user_message": {
                    "id": user_message.pk,
                    "role": user_message.role,
                    "content": user_message.content,
                },
                "assistant_message": {
                    "id": assistant_message.pk,
                    "role": assistant_message.role,
                    "content": assistant_message.content,
                },
            }
        )

    return redirect("chat:detail", pk=conversation.pk)


@login_required
@require_POST
def send_message_stream(request, pk: int):
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        user=request.user,
    )

    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse(
            {"ok": False, "error": "El mensaje no puede estar vacío."},
            status=400,
        )

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=content,
    )

    if conversation.title == "Nuevo chat":
        conversation.title = content[:40]
        conversation.save(update_fields=["title", "updated_at"])

    def generate():
        full_text_parts = []

        start_payload = {
            "type": "meta",
            "conversation": _serialize_conversation(conversation),
        }
        yield json.dumps(start_payload) + "\n"

        try:
            client = _build_lmstudio_client()
            history = _build_history(conversation)

            stream = client.chat.completions.create(
                model=LM_STUDIO_MODEL,
                messages=history,
                temperature=0.7,
                stream=True,
            )

            for chunk in stream:
                delta = ""
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content or ""

                if delta:
                    full_text_parts.append(delta)
                    yield json.dumps({"type": "token", "content": delta}) + "\n"

            full_text = "".join(full_text_parts).strip()
            if not full_text:
                full_text = "No pude generar una respuesta en este momento."

            Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=full_text,
            )

            yield json.dumps({"type": "done"}) + "\n"

        except Exception:
            logger.exception("Error consultando LM Studio en streaming")
            error_text = (
                "Hubo un problema al consultar el modelo local en LM Studio. "
                "Verificá que el servidor esté iniciado, que haya un modelo cargado "
                "y que la URL configurada sea correcta."
            )

            Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=error_text,
            )

            yield json.dumps({"type": "error", "content": error_text}) + "\n"

    response = StreamingHttpResponse(
        generate(),
        content_type="application/x-ndjson; charset=utf-8",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response