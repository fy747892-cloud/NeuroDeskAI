import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/data/secure_token_store.dart';
import '../../features/auth/domain/auth_tokens.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

final dioProvider = Provider<Dio>((ref) {
  final baseOptions = BaseOptions(
    baseUrl: apiBaseUrl,
    connectTimeout: const Duration(seconds: 12),
    receiveTimeout: const Duration(seconds: 20),
    sendTimeout: const Duration(seconds: 20),
  );
  final dio = Dio(baseOptions);
  final tokenStore = ref.watch(secureTokenStoreProvider);
  final refreshDio = Dio(baseOptions);

  dio.interceptors.add(
    QueuedInterceptorsWrapper(
      onRequest: (options, handler) async {
        options.headers['x-device-id'] = 'neurodesk-mobile-mvp';
        if (options.extra['skipAuth'] == true) {
          handler.next(options);
          return;
        }

        final tokens = await tokenStore.read();
        final accessToken = tokens?.accessToken;
        if (accessToken != null) {
          options.headers['Authorization'] = 'Bearer $accessToken';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        final request = error.requestOptions;
        final isUnauthorized = error.response?.statusCode == 401;
        final alreadyRetried = request.extra['retriedAfterRefresh'] == true;
        final canRefresh = !_isAuthEndpoint(request.path);

        if (!isUnauthorized || alreadyRetried || !canRefresh) {
          handler.next(error);
          return;
        }

        final refreshed = await _refreshTokens(refreshDio, tokenStore);
        if (refreshed == null) {
          await tokenStore.clear();
          handler.next(error);
          return;
        }

        final retryOptions = _copyForRetry(request, refreshed.accessToken);
        try {
          final response = await dio.fetch<dynamic>(retryOptions);
          handler.resolve(response);
        } on DioException catch (retryError) {
          handler.next(retryError);
        }
      },
    ),
  );

  return dio;
});

bool _isAuthEndpoint(String path) {
  return path.contains('/api/v1/auth/login') ||
      path.contains('/api/v1/auth/register') ||
      path.contains('/api/v1/auth/refresh') ||
      path.contains('/api/v1/auth/logout');
}

Future<AuthTokens?> _refreshTokens(
  Dio refreshDio,
  SecureTokenStore tokenStore,
) async {
  final currentTokens = await tokenStore.read();
  final refreshToken = currentTokens?.refreshToken;
  if (refreshToken == null) {
    return null;
  }

  try {
    final response = await refreshDio.post<Map<String, dynamic>>(
      '/api/v1/auth/refresh',
      data: {'refresh_token': refreshToken},
      options: Options(
        headers: {'x-device-id': 'neurodesk-mobile-mvp'},
        extra: {'skipAuth': true},
      ),
    );
    final tokens = AuthTokens.fromJson(response.data!);
    await tokenStore.save(tokens);
    return tokens;
  } on DioException {
    return null;
  }
}

RequestOptions _copyForRetry(RequestOptions request, String accessToken) {
  final headers = Map<String, dynamic>.from(request.headers)
    ..['Authorization'] = 'Bearer $accessToken'
    ..['x-device-id'] = 'neurodesk-mobile-mvp';
  final extra = Map<String, dynamic>.from(request.extra)
    ..['retriedAfterRefresh'] = true;

  return request.copyWith(headers: headers, extra: extra);
}
