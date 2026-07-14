import 'package:dio/dio.dart';

String readableApiError(Object error, String fallback) {
  if (error is DioException) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return 'Sunucuya ulasilamadi. Baglantiyi kontrol edip tekrar deneyin.';
    }
    if (error.type == DioExceptionType.connectionError) {
      return 'API baglantisi kurulamadi. Backend calisiyor mu kontrol edin.';
    }

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
