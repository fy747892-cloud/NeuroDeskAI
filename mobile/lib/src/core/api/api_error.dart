import 'package:dio/dio.dart';

String readableApiError(Object error, String fallback) {
  if (error is DioException) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return 'Sunucu gec yanit verdi. Baglantiyi kontrol edip tekrar deneyin.';
    }
    if (error.type == DioExceptionType.connectionError) {
      return 'API baglantisi kurulamadi. Backend adresi ve ag baglantisini kontrol edin.';
    }

    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final message = _messageFromData(data);
      if (message is String && message.isNotEmpty) {
        return message;
      }
    }

    final statusCode = error.response?.statusCode;
    if (statusCode == 401) {
      return 'Oturum suresi doldu. Tekrar giris yapin.';
    }
    if (statusCode == 403) {
      return 'Bu islem icin yetkiniz yok.';
    }
    if (statusCode == 404) {
      return 'Istenen kayit bulunamadi.';
    }
    if (statusCode == 429) {
      return 'Cok fazla istek gonderildi. Biraz bekleyip tekrar deneyin.';
    }
    if (statusCode != null && statusCode >= 500) {
      return 'Sunucu tarafinda gecici bir sorun olustu. Tekrar deneyin.';
    }
  }
  return fallback;
}

Object? _messageFromData(Map<String, dynamic> data) {
  final message = data['message'] ?? data['detail'] ?? data['error'];
  if (message is List && message.isNotEmpty) {
    final first = message.first;
    if (first is Map<String, dynamic>) {
      return first['msg'] ?? first['message'];
    }
    return first.toString();
  }
  if (message is Map<String, dynamic>) {
    return message['msg'] ?? message['message'] ?? message['detail'];
  }
  return message;
}
