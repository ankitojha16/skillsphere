from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import AIConversation, AIMessage
from services.ai_service import AIService
from gamification.services import award_user_xp

@login_required
def assistant_view(request, conversation_id=None):
    user_conversations = AIConversation.objects.filter(user=request.user)

    current_conv = None
    if conversation_id:
        current_conv = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
    elif user_conversations.exists():
        current_conv = user_conversations.first()
    else:
        current_conv = AIConversation.objects.create(
            user=request.user,
            title='New Study Session',
            mode='detailed'
        )

    # Handle question submission
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        mode = request.POST.get('mode', current_conv.mode)

        if not question:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Please enter a valid academic or programming question.'}, status=400)
            messages.error(request, "Please enter a question.")
            return redirect('assistant:chat_detail', conversation_id=current_conv.id)

        # Update mode if changed
        if mode in dict(AIConversation.MODE_CHOICES):
            current_conv.mode = mode
            current_conv.save()

        # Update conversation title if default
        if current_conv.title == 'New Study Session':
            current_conv.title = (question[:45] + '...') if len(question) > 45 else question
            current_conv.save()

        # Save student message
        student_msg = AIMessage.objects.create(
            conversation=current_conv,
            role='user',
            content=question
        )

        # Build history
        history = [
            {'role': m.role, 'content': m.content}
            for m in current_conv.messages.all()[:6]
        ]

        # Call AI Engine with explicit metadata
        ai_meta = AIService.ask_study_assistant_with_meta(
            question=question,
            mode=current_conv.mode,
            conversation_history=history
        )

        # Save AI message with provider attribution
        ai_msg = AIMessage.objects.create(
            conversation=current_conv,
            role='assistant',
            content=ai_meta['text'],
            provider=ai_meta.get('provider', 'offline-knowledge-engine'),
            is_fallback=ai_meta.get('is_fallback', True)
        )

        # Award small curiosity XP
        award_user_xp(request.user, 5, "Consulted AI Study Assistant")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'conversation_id': current_conv.id,
                'conversation_title': current_conv.title,
                'user_message': student_msg.content,
                'ai_message': ai_msg.content,
                'provider': ai_msg.provider,
                'provider_label': ai_meta.get('provider_label', 'SkillSphere Knowledge Engine'),
                'is_fallback': ai_msg.is_fallback,
                'mode': current_conv.mode,
                'created_at': ai_msg.created_at.strftime('%H:%M'),
            })

        return redirect('assistant:chat_detail', conversation_id=current_conv.id)

    chat_messages = current_conv.messages.all()
    ai_status = AIService.get_ai_status()

    return render(request, 'assistant/index.html', {
        'current_conv': current_conv,
        'chat_messages': chat_messages,
        'user_conversations': user_conversations,
        'mode_choices': AIConversation.MODE_CHOICES,
        'ai_status': ai_status,
    })


@login_required
def new_conversation_view(request):
    mode = request.GET.get('mode', 'detailed')
    if mode not in dict(AIConversation.MODE_CHOICES):
        mode = 'detailed'

    conv = AIConversation.objects.create(
        user=request.user,
        title='New Study Session',
        mode=mode
    )
    return redirect('assistant:chat_detail', conversation_id=conv.id)


@login_required
def delete_conversation_view(request, conversation_id):
    conv = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
    if request.method == 'POST':
        conv.delete()
        messages.info(request, "Conversation deleted.")
    return redirect('assistant:index')


@login_required
def clear_all_conversations_view(request):
    if request.method == 'POST':
        count, _ = AIConversation.objects.filter(user=request.user).delete()
        messages.info(request, f"Cleared {count} study session conversations.")
    return redirect('assistant:index')


def ai_status_view(request):
    """Returns real-time status of configured AI providers and knowledge engine."""
    status_info = AIService.get_ai_status()
    return JsonResponse(status_info)
