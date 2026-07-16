import 'package:flutter_test/flutter_test.dart';
import 'package:neurodesk_ai_mobile/src/features/ai_approvals/domain/ai_action_approval.dart';
import 'package:neurodesk_ai_mobile/src/features/ai_chat/domain/chat_message.dart';
import 'package:neurodesk_ai_mobile/src/features/analytics/domain/analytics_models.dart';
import 'package:neurodesk_ai_mobile/src/features/calls/domain/call_record.dart'
    as call_domain;
import 'package:neurodesk_ai_mobile/src/features/contacts/domain/contact.dart';
import 'package:neurodesk_ai_mobile/src/features/conversations/domain/conversation.dart';
import 'package:neurodesk_ai_mobile/src/features/deals/domain/deal.dart';
import 'package:neurodesk_ai_mobile/src/features/email/domain/email_models.dart';
import 'package:neurodesk_ai_mobile/src/features/files/domain/file_record.dart';
import 'package:neurodesk_ai_mobile/src/features/notifications/domain/app_notification.dart';
import 'package:neurodesk_ai_mobile/src/features/priority/domain/priority_queue.dart';
import 'package:neurodesk_ai_mobile/src/features/search/domain/search_result.dart';
import 'package:neurodesk_ai_mobile/src/features/settings/domain/user_profile.dart';

void main() {
  test('parses AI action approval payloads from backend schema', () {
    final approval = AiActionApproval.fromJson({
      'id': 'approval-1',
      'action_type': 'task',
      'source_type': 'conversation',
      'status': 'pending',
      'suggested_payload': {
        'title': 'Musteriyi ara',
        'description': 'Teklif detaylarini takip et.',
      },
      'confidence_score': 0.82,
      'expires_at': '2026-07-15T12:00:00Z',
      'created_at': '2026-07-14T12:00:00Z',
    });

    expect(approval.displayTitle, 'Musteriyi ara');
    expect(approval.displayDescription, 'Teklif detaylarini takip et.');
    expect(approval.actionLabel, 'Gorev');
    expect(approval.confidenceScore, 0.82);
  });

  test('labels backend AI appointment approvals', () {
    final approval = AiActionApproval.fromJson({
      'id': 'approval-2',
      'action_type': 'appointment',
      'source_type': 'conversation',
      'status': 'pending',
      'suggested_payload': <String, dynamic>{},
      'confidence_score': null,
      'expires_at': null,
      'created_at': '2026-07-14T12:00:00Z',
    });

    expect(approval.displayTitle, 'Randevu onerisi');
    expect(approval.actionLabel, 'Randevu');
  });

  test('parses conversation list payloads from backend schema', () {
    final conversation = Conversation.fromJson({
      'id': 'conversation-1',
      'title': 'Satis gorusmesi',
      'source_type': 'manual_call',
      'status': 'active',
      'created_at': '2026-07-14T12:00:00Z',
    });

    expect(conversation.id, 'conversation-1');
    expect(conversation.title, 'Satis gorusmesi');
    expect(conversation.sourceType, 'manual_call');
    expect(conversation.status, 'active');
  });

  test('parses call text result conversation id', () {
    final result = CallTextResult.fromJson({
      'conversation': {
        'id': 'conversation-2',
        'title': 'Destek gorusmesi',
      },
      'call': {},
      'transcription': {},
    });

    expect(result.conversationId, 'conversation-2');
  });

  test('parses notification payloads from backend schema', () {
    final notification = AppNotification.fromJson({
      'id': 'notification-1',
      'title': 'Analiz tamamlandi',
      'body': 'Yeni AI onaylari hazir.',
      'notification_type': 'ai_analysis_completed',
      'channel': 'in_app',
      'source_type': 'conversation',
      'source_id': 'conversation-1',
      'status': 'sent',
      'scheduled_at': '2026-07-14T12:00:00Z',
      'read_at': null,
      'created_at': '2026-07-14T11:59:00Z',
    });

    expect(notification.title, 'Analiz tamamlandi');
    expect(notification.isRead, isFalse);
    expect(notification.sourceType, 'conversation');
  });

  test('parses AI chat message payloads from backend schema', () {
    final message = ChatMessage.fromJson({
      'id': 'message-1',
      'session_id': 'session-1',
      'role': 'assistant',
      'content': 'Bugun 2 acik gorev var.',
      'confidence': 0.76,
      'sources': [
        {
          'source_type': 'task',
          'source_id': 'task-1',
          'title': 'Musteriyi ara',
          'snippet': 'Teklif takip edilecek.',
        },
      ],
      'created_at': '2026-07-14T12:00:00Z',
    });

    expect(message.sessionId, 'session-1');
    expect(message.confidence, 0.76);
    expect(message.sources, hasLength(1));
    expect(message.sources!.first.title, 'Musteriyi ara');
  });

  test('parses contact and memory payloads from backend schema', () {
    final contact = Contact.fromJson({
      'id': 'contact-1',
      'full_name': 'Ayse Demir',
      'email': 'ayse@example.com',
      'phone': null,
      'company': 'Demo Ltd',
      'title': 'Founder',
      'tags': ['lead'],
      'status': 'active',
      'created_at': '2026-07-14T12:00:00Z',
    });
    final memory = ContactMemory.fromJson({
      'contact_id': 'contact-1',
      'full_name': 'Ayse Demir',
      'last_conversation': {
        'id': 'conversation-1',
        'title': 'Demo',
        'occurred_at': '2026-07-14T12:00:00Z'
      },
      'last_email': null,
      'last_topic': 'Teklif',
      'pending_items_count': 2,
      'open_deals_count': 1,
      'open_deals_total_value': 1200,
      'next_appointment': {
        'id': 'appointment-1',
        'title': 'Takip',
        'start_at': '2026-07-15T12:00:00Z'
      },
      'generated_at': '2026-07-14T12:00:00Z',
    });

    expect(contact.fullName, 'Ayse Demir');
    expect(contact.tags.first, 'lead');
    expect(memory.pendingItemsCount, 2);
    expect(memory.nextAppointmentTitle, 'Takip');
  });

  test('parses semantic search results from backend schema', () {
    final result = SearchResult.fromJson({
      'source_type': 'task',
      'source_id': 'task-1',
      'title': 'Musteriyi ara',
      'snippet': 'Teklif takip edilecek.',
      'score': 0.91,
    });

    expect(result.sourceType, 'task');
    expect(result.sourceId, 'task-1');
    expect(result.title, 'Musteriyi ara');
    expect(result.score, 0.91);
  });

  test('parses deal payloads from backend schema', () {
    final deal = Deal.fromJson({
      'id': 'deal-1',
      'tenant_id': 'tenant-1',
      'organization_id': 'org-1',
      'owner_user_id': 'user-1',
      'contact_id': 'contact-1',
      'title': 'Kurumsal paket',
      'description': null,
      'value': 45000,
      'currency': 'TRY',
      'stage': 'proposal_sent',
      'expected_close_date': '2026-07-20T12:00:00Z',
      'source_type': 'manual',
      'source_id': null,
      'ai_action_approval_id': null,
      'created_at': '2026-07-14T12:00:00Z',
    });

    expect(deal.title, 'Kurumsal paket');
    expect(deal.value, 45000);
    expect(deal.stage, 'proposal_sent');
    expect(dealStageLabel(deal.stage), 'Teklif');
    expect(deal.contactId, 'contact-1');
  });

  test('parses priority queue payloads from backend schema', () {
    final queue = PriorityQueue.fromJson({
      'generated_at': '2026-07-14T12:00:00Z',
      'items': [
        {
          'item_type': 'task',
          'item_id': 'task-1',
          'title': 'Acil teklif takibi',
          'status': 'pending',
          'score': 86,
          'priority': 'urgent',
          'due_at': '2026-07-14T15:00:00Z',
          'contact_id': 'contact-1',
          'factors': [
            {
              'key': 'due_soon',
              'label': 'Task due date is within 24 hours.',
              'weight': 28
            },
            {
              'key': 'urgent_language',
              'label': 'Urgent language detected.',
              'weight': 14
            },
          ],
        },
      ],
    });

    expect(queue.items, hasLength(1));
    expect(queue.items.first.score, 86);
    expect(queue.items.first.factors.first.key, 'due_soon');
    expect(priorityLabel(queue.items.first.priority), 'Acil');
  });

  test('parses analytics overview payloads from backend schema', () {
    final overview = AnalyticsOverview.fromJson({
      'date_from': '2026-07-10',
      'date_to': '2026-07-16',
      'tasks_created': 8,
      'tasks_completed': 5,
      'tasks_overdue': 1,
      'calls_total': 4,
      'calls_analyzed': 3,
      'appointments_completed': 2,
      'appointments_upcoming': 6,
      'ai_requests': 12,
      'ai_cost_amount': 0.0345,
    });

    expect(overview.tasksCompleted, 5);
    expect(overview.callsAnalyzed, 3);
    expect(overview.aiCostAmount, 0.0345);
  });

  test('parses file payloads from backend schema', () {
    final file = FileRecord.fromJson({
      'id': 'file-1',
      'tenant_id': 'tenant-1',
      'organization_id': 'org-1',
      'owner_user_id': 'user-1',
      'filename': 'teklif.pdf',
      'mime_type': 'application/pdf',
      'size_bytes': 2048,
      'status': 'ready',
      'created_at': '2026-07-16T09:00:00Z',
    });
    final analysis = FileAnalysis.fromJson({
      'file_id': 'file-1',
      'summary': 'Kisa ozet',
      'status': 'completed',
    });

    expect(file.filename, 'teklif.pdf');
    expect(file.sizeBytes, 2048);
    expect(analysis.summary, 'Kisa ozet');
  });

  test('parses call payloads from backend schema', () {
    final call = call_domain.CallRecord.fromJson({
      'id': 'call-1',
      'conversation_id': 'conversation-1',
      'call_direction': 'outbound',
      'phone_number': '+905551112233',
      'started_at': '2026-07-16T09:00:00Z',
      'duration_seconds': 180,
      'status': 'uploaded',
      'created_at': '2026-07-16T09:03:00Z',
      'transcriptions': [
        {
          'id': 'transcription-1',
          'call_id': 'call-1',
          'language': 'tr',
          'status': 'completed',
          'transcript_text': 'Teklif konusuldu.',
          'created_at': '2026-07-16T09:04:00Z',
        },
      ],
    });

    expect(call.conversationId, 'conversation-1');
    expect(call.callDirection, 'outbound');
    expect(call.durationSeconds, 180);
    expect(call.transcriptions.first.transcriptText, 'Teklif konusuldu.');
  });

  test('parses email account and message payloads from backend schema', () {
    final account = EmailAccount.fromJson({
      'id': 'account-1',
      'tenant_id': 'tenant-1',
      'organization_id': 'org-1',
      'user_id': 'user-1',
      'provider': 'gmail',
      'email_address': 'demo@example.com',
      'status': 'connected',
      'consent_granted_at': '2026-07-16T09:00:00Z',
      'consent_scope': 'gmail.readonly',
      'last_synced_at': null,
      'created_at': '2026-07-16T09:00:00Z',
    });
    final message = EmailMessage.fromJson({
      'id': 'message-1',
      'email_account_id': 'account-1',
      'provider_message_id': 'provider-1',
      'thread_id': 'thread-1',
      'subject': 'Teklif',
      'from_address': 'lead@example.com',
      'snippet': 'Merhaba',
      'body': null,
      'received_at': '2026-07-16T09:30:00Z',
      'is_replied': false,
    });

    expect(account.provider, 'gmail');
    expect(account.emailAddress, 'demo@example.com');
    expect(message.subject, 'Teklif');
    expect(message.isReplied, isFalse);
  });

  test('parses current user payloads from backend schema', () {
    final user = CurrentUser.fromJson({
      'id': 'user-1',
      'email': 'demo@example.com',
      'tenant_id': 'tenant-1',
      'organization_id': 'org-1',
      'status': 'active',
      'is_email_verified': true,
      'created_at': '2026-07-16T09:00:00Z',
      'profile': {
        'full_name': 'Demo User',
        'title': 'Founder',
        'avatar_url': null,
      },
    });

    expect(user.email, 'demo@example.com');
    expect(user.profile!.fullName, 'Demo User');
    expect(user.isEmailVerified, isTrue);
  });
}
