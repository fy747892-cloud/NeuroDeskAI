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
    if (error.type == DioExceptionType.cancel) {
      return 'İstek iptal edildi. İşlemi tekrar başlatabilirsiniz.';
    }

    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final message = _friendlyMessageFromData(data, error.response?.statusCode);
      if (message != null && message.isNotEmpty) {
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
      return 'Sunucu tarafında geçici bir sorun oluştu. Biraz sonra tekrar deneyin; devam ederse backend loglarını kontrol edin.';
    }
  }
  return fallback;
}

String? _friendlyMessageFromData(Map<String, dynamic> data, int? statusCode) {
  final code = data['error_code'];
  final rawMessage = _messageFromData(data);
  final message = rawMessage?.trim();
  if (message != null && message.isNotEmpty && !_looksTechnical(message)) {
    return message;
  }

  if (code == 'auth_error') {
    return 'Oturum bilgisi doğrulanamadı. Tekrar giriş yapın.';
  }
  if (code == 'forbidden') {
    return 'Bu işlem için yetkiniz yok. Hesap rolünüzü veya ekip izinlerinizi kontrol edin.';
  }
  if (code == 'not_found') {
    return 'İstenen kayıt bulunamadı. Listeyi yenileyip tekrar deneyin.';
  }
  if (code == 'conflict') {
    return 'Bu işlem mevcut kayıtla çakışıyor. Sayfayı yenileyip son durumu kontrol edin.';
  }
  if (code == 'validation_error') {
    return 'Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin.';
  }
  if (code == 'rate_limited') {
    return 'Kısa sürede çok fazla istek gönderildi. Biraz bekleyip tekrar deneyin.';
  }
  if (code == 'quota_exceeded') {
    return 'Kullanım kotası doldu. Plan limitlerini kontrol edin veya daha sonra tekrar deneyin.';
  }
  if (code == 'provider_error') {
    return 'AI sağlayıcısı isteği tamamlayamadı. API anahtarı, kota ve dosya formatını kontrol edip tekrar deneyin.';
  }

  if (statusCode == 400 || statusCode == 422) {
    return 'Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin.';
  }
  return null;
}

String? _messageFromData(Map<String, dynamic> data) {
  final message = data['message'] ?? data['detail'] ?? data['error'];
  if (message is List && message.isNotEmpty) {
    final items = message
        .map((item) {
          if (item is Map<String, dynamic>) {
            return item['msg'] ?? item['message'] ?? item['detail'];
          }
          return item;
        })
        .whereType<Object>()
        .map((item) => item.toString())
        .where((item) => item.trim().isNotEmpty)
        .toList();
    return items.isEmpty ? null : items.join(' ');
  }
  if (message is Map<String, dynamic>) {
    final nested = message['msg'] ?? message['message'] ?? message['detail'];
    return nested?.toString();
  }
  return message?.toString();
}

bool _looksTechnical(String message) {
  final lower = message.toLowerCase();
  return lower.contains('dioexception') ||
      lower.contains('httpexception') ||
      lower.contains('runtimeerror') ||
      lower.contains('traceback') ||
      lower.contains('status code of') ||
      lower.contains('requestoptions');
}
