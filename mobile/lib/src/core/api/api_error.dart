import 'package:dio/dio.dart';

String readableApiError(Object error, String fallback) {
  if (error is DioException) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return 'Sunucu geç yanıt verdi. Bağlantıyı kontrol edip tekrar deneyin.';
    }
    if (error.type == DioExceptionType.connectionError) {
      return 'API bağlantısı kurulamadı. Backend adresi ve ağ bağlantısını kontrol edin.';
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
      return 'Oturum süresi doldu. Tekrar giriş yapın.';
    }
    if (statusCode == 403) {
      return 'Bu işlem için yetkiniz yok.';
    }
    if (statusCode == 404) {
      return 'İstenen kayıt bulunamadı.';
    }
    if (statusCode == 429) {
      return 'Çok fazla istek gönderildi. Biraz bekleyip tekrar deneyin.';
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
