class PriorityQueue {
  const PriorityQueue({
    required this.generatedAt,
    required this.items,
  });

  final DateTime generatedAt;
  final List<PriorityItem> items;

  factory PriorityQueue.fromJson(Map<String, dynamic> json) {
    return PriorityQueue(
      generatedAt: DateTime.parse(json['generated_at'] as String),
      items: (json['items'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(PriorityItem.fromJson)
          .toList(growable: false),
    );
  }
}

class PriorityItem {
  const PriorityItem({
    required this.itemType,
    required this.itemId,
    required this.title,
    required this.status,
    required this.score,
    required this.priority,
    required this.factors,
    this.dueAt,
    this.contactId,
  });

  final String itemType;
  final String itemId;
  final String title;
  final String status;
  final int score;
  final String priority;
  final DateTime? dueAt;
  final String? contactId;
  final List<PriorityFactor> factors;

  factory PriorityItem.fromJson(Map<String, dynamic> json) {
    return PriorityItem(
      itemType: json['item_type'] as String,
      itemId: json['item_id'] as String,
      title: json['title'] as String,
      status: json['status'] as String,
      score: json['score'] as int,
      priority: json['priority'] as String,
      dueAt: json['due_at'] == null
          ? null
          : DateTime.parse(json['due_at'] as String),
      contactId: json['contact_id'] as String?,
      factors: (json['factors'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(PriorityFactor.fromJson)
          .toList(growable: false),
    );
  }
}

class PriorityFactor {
  const PriorityFactor({
    required this.key,
    required this.label,
    required this.weight,
  });

  final String key;
  final String label;
  final int weight;

  factory PriorityFactor.fromJson(Map<String, dynamic> json) {
    return PriorityFactor(
      key: json['key'] as String,
      label: json['label'] as String,
      weight: json['weight'] as int,
    );
  }
}

String priorityLabel(String value) {
  return switch (value) {
    'urgent' => 'Acil',
    'high' => 'Yuksek',
    'medium' => 'Orta',
    'low' => 'Dusuk',
    _ => value,
  };
}

String priorityItemTypeLabel(String value) {
  return switch (value) {
    'task' => 'Görev',
    'appointment' => 'Randevu',
    _ => value,
  };
}
