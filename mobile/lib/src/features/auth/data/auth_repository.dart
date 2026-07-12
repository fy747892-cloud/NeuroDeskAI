import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/auth_tokens.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(dioProvider));
});

class AuthRepository {
  const AuthRepository(this._dio);

  final Dio _dio;

  Future<AuthTokens> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {'email': email, 'password': password},
    );
    return AuthTokens.fromJson(response.data!);
  }

  Future<void> logout(String refreshToken) async {
    await _dio.post<void>(
      '/api/v1/auth/logout',
      data: {'refresh_token': refreshToken},
    );
  }
}
