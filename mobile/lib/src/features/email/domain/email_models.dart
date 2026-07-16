class EmailAccount {
  const EmailAccount({
    required this.id,
    required this.provider,
    required this.status,
    required this.createdAt,
    this.emailAddress,
    this.consentScope,
    this.consentGrantedAt,
    this.lastSyncedAt,
  });

  final String id;
  final String provider;
  final String? emailAddress;
  final String status;
  final DateTime? consentGrantedAt;
  final String? consentScope;
  final DateTime? lastSyncedAt;
  final DateTime createdAt;

  factory EmailAccount.fromJson(Map<String, dynamic> json) {
    return EmailAccount(
      id: json['id'] as String,
      provider: json['provider'] as String,
      emailAddress: json['email_address'] as String?,
      status: json['status'] as String,
      consentGrantedAt: json['consent_granted_at'] == null
          ? null
          : DateTime.parse(json['consent_granted_at'] as String),
      consentScope: json['consent_scope'] as String?,
      lastSyncedAt: json['last_synced_at'] == null
          ? null
          : DateTime.parse(json['last_synced_at'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class EmailMessage {
  const EmailMessage({
    required this.id,
    required this.emailAccountId,
    required this.providerMessageId,
    required this.isReplied,
    this.threadId,
    this.subject,
    this.fromAddress,
    this.snippet,
    this.body,
    this.receivedAt,
  });

  final String id;
  final String emailAccountId;
  final String providerMessageId;
  final String? threadId;
  final String? subject;
  final String? fromAddress;
  final String? snippet;
  final String? body;
  final DateTime? receivedAt;
  final bool isReplied;

  factory EmailMessage.fromJson(Map<String, dynamic> json) {
    return EmailMessage(
      id: json['id'] as String,
      emailAccountId: json['email_account_id'] as String,
      providerMessageId: json['provider_message_id'] as String,
      threadId: json['thread_id'] as String?,
      subject: json['subject'] as String?,
      fromAddress: json['from_address'] as String?,
      snippet: json['snippet'] as String?,
      body: json['body'] as String?,
      receivedAt: json['received_at'] == null
          ? null
          : DateTime.parse(json['received_at'] as String),
      isReplied: json['is_replied'] as bool,
    );
  }
}

class EmailConnectStart {
  const EmailConnectStart({required this.authorizeUrl, required this.state});

  final String authorizeUrl;
  final String state;

  factory EmailConnectStart.fromJson(Map<String, dynamic> json) {
    return EmailConnectStart(
      authorizeUrl: json['authorize_url'] as String,
      state: json['state'] as String,
    );
  }
}

class EmailSyncSummary {
  const EmailSyncSummary({
    required this.fetched,
    required this.created,
    required this.skipped,
  });

  final int fetched;
  final int created;
  final int skipped;

  factory EmailSyncSummary.fromJson(Map<String, dynamic> json) {
    return EmailSyncSummary(
      fetched: json['fetched'] as int,
      created: json['created'] as int,
      skipped: json['skipped'] as int,
    );
  }
}
