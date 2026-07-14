class Deal {
  const Deal({
    required this.id,
    required this.title,
    required this.currency,
    required this.stage,
    required this.sourceType,
    required this.createdAt,
    this.description,
    this.value,
    this.expectedCloseDate,
    this.contactId,
  });

  final String id;
  final String title;
  final String? description;
  final double? value;
  final String currency;
  final String stage;
  final DateTime? expectedCloseDate;
  final String? contactId;
  final String sourceType;
  final DateTime createdAt;

  factory Deal.fromJson(Map<String, dynamic> json) {
    return Deal(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      value: (json['value'] as num?)?.toDouble(),
      currency: json['currency'] as String,
      stage: json['stage'] as String,
      expectedCloseDate: json['expected_close_date'] == null
          ? null
          : DateTime.parse(json['expected_close_date'] as String),
      contactId: json['contact_id'] as String?,
      sourceType: json['source_type'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

const dealStages = [
  'lead',
  'proposal_sent',
  'negotiation',
  'invoiced',
  'won',
  'lost',
];

const openDealStages = {
  'lead',
  'proposal_sent',
  'negotiation',
  'invoiced',
};

String dealStageLabel(String stage) {
  return switch (stage) {
    'lead' => 'Aday',
    'proposal_sent' => 'Teklif',
    'negotiation' => 'Muzakere',
    'invoiced' => 'Fatura',
    'won' => 'Kazanildi',
    'lost' => 'Kaybedildi',
    _ => stage,
  };
}
