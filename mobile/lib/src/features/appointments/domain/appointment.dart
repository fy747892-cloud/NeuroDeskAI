class Appointment {
  const Appointment({
    required this.id,
    required this.title,
    required this.startAt,
    required this.endAt,
    required this.status,
    this.description,
    this.location,
  });

  final String id;
  final String title;
  final String? description;
  final String? location;
  final DateTime startAt;
  final DateTime endAt;
  final String status;

  factory Appointment.fromJson(Map<String, dynamic> json) {
    return Appointment(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      location: json['location'] as String?,
      startAt: DateTime.parse(json['start_at'] as String),
      endAt: DateTime.parse(json['end_at'] as String),
      status: json['status'] as String,
    );
  }
}
