import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/appointment.dart';

final appointmentsRepositoryProvider = Provider<AppointmentsRepository>((ref) {
  return AppointmentsRepository(ref.watch(dioProvider));
});

final appointmentsProvider =
    FutureProvider.autoDispose<List<Appointment>>((ref) async {
  return ref.watch(appointmentsRepositoryProvider).listAppointments();
});

/// Keyed by the first day of the visible month; fetches that whole month.
final appointmentsForMonthProvider = FutureProvider.autoDispose
    .family<List<Appointment>, DateTime>((ref, monthStart) async {
  final nextMonth = monthStart.month == 12
      ? DateTime(monthStart.year + 1, 1, 1)
      : DateTime(monthStart.year, monthStart.month + 1, 1);
  return ref
      .watch(appointmentsRepositoryProvider)
      .listAppointments(start: monthStart, end: nextMonth);
});

class AppointmentsRepository {
  const AppointmentsRepository(this._dio);

  final Dio _dio;

  Future<List<Appointment>> listAppointments({
    DateTime? start,
    DateTime? end,
  }) async {
    final rangeStart = (start ?? DateTime.now()).toUtc();
    final rangeEnd = (end ?? rangeStart.add(const Duration(days: 14))).toUtc();
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/appointments',
      queryParameters: {
        'start_date': rangeStart.toIso8601String(),
        'end_date': rangeEnd.toIso8601String(),
      },
    );

    return response.data!
        .cast<Map<String, dynamic>>()
        .map(Appointment.fromJson)
        .toList(growable: false);
  }

  Future<Appointment> createAppointment({
    required String title,
    required DateTime startAt,
    required DateTime endAt,
    String? location,
    String? description,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/appointments',
      data: {
        'title': title,
        'start_at': startAt.toUtc().toIso8601String(),
        'end_at': endAt.toUtc().toIso8601String(),
        if (location != null && location.isNotEmpty) 'location': location,
        if (description != null && description.isNotEmpty)
          'description': description,
      },
    );
    return Appointment.fromJson(response.data!);
  }

  Future<void> deleteAppointment(String appointmentId) async {
    await _dio.delete<void>('/api/v1/appointments/$appointmentId');
  }

  Future<void> clearAppointments() async {
    final appointments = await listAppointments();
    await Future.wait(
      appointments.map((appointment) => deleteAppointment(appointment.id)),
    );
  }
}
