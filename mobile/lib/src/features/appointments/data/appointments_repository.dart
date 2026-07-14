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

class AppointmentsRepository {
  const AppointmentsRepository(this._dio);

  final Dio _dio;

  Future<List<Appointment>> listAppointments() async {
    final now = DateTime.now().toUtc();
    final end = now.add(const Duration(days: 14));
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/appointments',
      queryParameters: {
        'start_date': now.toIso8601String(),
        'end_date': end.toIso8601String(),
      },
    );

    return response.data!
        .cast<Map<String, dynamic>>()
        .map(Appointment.fromJson)
        .toList(growable: false);
  }
}
