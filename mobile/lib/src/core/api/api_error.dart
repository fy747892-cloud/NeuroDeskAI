import 'package:dio/dio.dart';

String readableApiError(Object error, String fallback) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final message = data['message'] ?? data['detail'];
      if (message is String && message.isNotEmpty) {
        return message;
      }
    }
  }
  return fallback;
}
