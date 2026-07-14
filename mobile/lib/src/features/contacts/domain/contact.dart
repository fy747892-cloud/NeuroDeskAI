class Contact {
  const Contact({
    required this.id,
    required this.fullName,
    required this.tags,
    required this.status,
    required this.createdAt,
    this.email,
    this.phone,
    this.company,
    this.title,
  });

  final String id;
  final String fullName;
  final String? email;
  final String? phone;
  final String? company;
  final String? title;
  final List<String> tags;
  final String status;
  final DateTime createdAt;

  factory Contact.fromJson(Map<String, dynamic> json) {
    return Contact(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      email: json['email'] as String?,
      phone: json['phone'] as String?,
      company: json['company'] as String?,
      title: json['title'] as String?,
      tags: (json['tags'] as List<dynamic>).cast<String>(),
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class ContactNote {
  const ContactNote({
    required this.id,
    required this.contactId,
    required this.noteText,
    required this.createdAt,
  });

  final String id;
  final String contactId;
  final String noteText;
  final DateTime createdAt;

  factory ContactNote.fromJson(Map<String, dynamic> json) {
    return ContactNote(
      id: json['id'] as String,
      contactId: json['contact_id'] as String,
      noteText: json['note_text'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class ContactTimelineEvent {
  const ContactTimelineEvent({
    required this.id,
    required this.eventType,
    required this.occurredAt,
    this.sourceType,
    this.eventMetadata,
  });

  final String id;
  final String eventType;
  final String? sourceType;
  final Map<String, dynamic>? eventMetadata;
  final DateTime occurredAt;

  factory ContactTimelineEvent.fromJson(Map<String, dynamic> json) {
    return ContactTimelineEvent(
      id: json['id'] as String,
      eventType: json['event_type'] as String,
      sourceType: json['source_type'] as String?,
      eventMetadata: json['event_metadata'] == null
          ? null
          : Map<String, dynamic>.from(json['event_metadata'] as Map),
      occurredAt: DateTime.parse(json['occurred_at'] as String),
    );
  }
}

class ContactDetail extends Contact {
  const ContactDetail({
    required super.id,
    required super.fullName,
    required super.tags,
    required super.status,
    required super.createdAt,
    required this.notes,
    required this.recentTimeline,
    super.email,
    super.phone,
    super.company,
    super.title,
  });

  final List<ContactNote> notes;
  final List<ContactTimelineEvent> recentTimeline;

  factory ContactDetail.fromJson(Map<String, dynamic> json) {
    return ContactDetail(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      email: json['email'] as String?,
      phone: json['phone'] as String?,
      company: json['company'] as String?,
      title: json['title'] as String?,
      tags: (json['tags'] as List<dynamic>).cast<String>(),
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      notes: (json['notes'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(ContactNote.fromJson)
          .toList(growable: false),
      recentTimeline: (json['recent_timeline'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(ContactTimelineEvent.fromJson)
          .toList(growable: false),
    );
  }
}

class ContactMemory {
  const ContactMemory({
    required this.contactId,
    required this.fullName,
    required this.pendingItemsCount,
    required this.openDealsCount,
    required this.openDealsTotalValue,
    required this.generatedAt,
    this.lastTopic,
    this.nextAppointmentTitle,
    this.lastConversationTitle,
  });

  final String contactId;
  final String fullName;
  final String? lastTopic;
  final int pendingItemsCount;
  final int openDealsCount;
  final double openDealsTotalValue;
  final String? nextAppointmentTitle;
  final String? lastConversationTitle;
  final DateTime generatedAt;

  factory ContactMemory.fromJson(Map<String, dynamic> json) {
    final nextAppointment = json['next_appointment'] as Map<String, dynamic>?;
    final lastConversation = json['last_conversation'] as Map<String, dynamic>?;

    return ContactMemory(
      contactId: json['contact_id'] as String,
      fullName: json['full_name'] as String,
      lastTopic: json['last_topic'] as String?,
      pendingItemsCount: json['pending_items_count'] as int,
      openDealsCount: json['open_deals_count'] as int,
      openDealsTotalValue: (json['open_deals_total_value'] as num).toDouble(),
      nextAppointmentTitle: nextAppointment?['title'] as String?,
      lastConversationTitle: lastConversation?['title'] as String?,
      generatedAt: DateTime.parse(json['generated_at'] as String),
    );
  }
}
