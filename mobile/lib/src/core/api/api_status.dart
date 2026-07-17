import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';

final apiStatusProvider = FutureProvider.autoDispose<ApiStatus>((ref) async {
  final dio = ref.watch(dioProvider);
  final response = await dio.get<Map<String, dynamic>>(
    '/health',
    options: Options(extra: {'skipAuth': true}),
  );
  return ApiStatus.fromJson(response.data!);
});

class ApiStatus {
  const ApiStatus({required this.status});

  final String status;

  String get normalizedStatus => status.trim().toLowerCase();

  bool get isOk => normalizedStatus == 'ok';

  String get displayLabel {
    return switch (normalizedStatus) {
      'ok' => 'Sağlıklı',
      'degraded' => 'Zayıf',
      'maintenance' => 'Bakımda',
      'unknown' => 'Bilinmiyor',
      _ => status.isEmpty ? 'Bilinmiyor' : status,
    };
  }

  factory ApiStatus.fromJson(Map<String, dynamic> json) {
    return ApiStatus(status: json['status'] as String? ?? 'unknown');
  }
}
