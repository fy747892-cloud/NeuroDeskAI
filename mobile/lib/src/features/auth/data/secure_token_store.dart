import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../domain/auth_tokens.dart';

final secureTokenStoreProvider = Provider<SecureTokenStore>((ref) {
  return const SecureTokenStore(FlutterSecureStorage());
});

class SecureTokenStore {
  const SecureTokenStore(this._storage);

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  static const _tokenTypeKey = 'token_type';

  final FlutterSecureStorage _storage;

  Future<AuthTokens?> read() async {
    final accessToken = await _storage.read(key: _accessTokenKey);
    final refreshToken = await _storage.read(key: _refreshTokenKey);
    final tokenType = await _storage.read(key: _tokenTypeKey);

    if (accessToken == null || refreshToken == null || tokenType == null) {
      return null;
    }

    return AuthTokens(
      accessToken: accessToken,
      refreshToken: refreshToken,
      tokenType: tokenType,
    );
  }

  Future<void> save(AuthTokens tokens) async {
    await _storage.write(key: _accessTokenKey, value: tokens.accessToken);
    await _storage.write(key: _refreshTokenKey, value: tokens.refreshToken);
    await _storage.write(key: _tokenTypeKey, value: tokens.tokenType);
  }

  Future<bool> hasSavedSession() async {
    return await _storage.read(key: _refreshTokenKey) != null;
  }

  Future<void> clear() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
    await _storage.delete(key: _tokenTypeKey);
  }
}
