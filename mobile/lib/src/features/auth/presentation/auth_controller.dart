import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/auth_repository.dart';
import '../data/biometric_auth_service.dart';
import '../data/secure_token_store.dart';
import '../domain/auth_tokens.dart';

final authControllerProvider =
    AsyncNotifierProvider<AuthController, AuthState>(AuthController.new);

class AuthState {
  const AuthState({
    required this.tokens,
    this.errorMessage,
    this.hasLockedSession = false,
  });

  final AuthTokens? tokens;
  final String? errorMessage;
  final bool hasLockedSession;

  bool get isAuthenticated => tokens != null;

  AuthState copyWith({
    AuthTokens? tokens,
    String? errorMessage,
    bool? hasLockedSession,
  }) {
    return AuthState(
      tokens: tokens ?? this.tokens,
      errorMessage: errorMessage,
      hasLockedSession: hasLockedSession ?? this.hasLockedSession,
    );
  }
}

class AuthController extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final store = ref.watch(secureTokenStoreProvider);
    final tokens = await store.read();
    if (tokens == null) {
      return const AuthState(tokens: null);
    }
    final unlocked =
        await ref.read(biometricAuthServiceProvider).authenticate();
    if (!unlocked) {
      return const AuthState(
        tokens: null,
        hasLockedSession: true,
        errorMessage: 'Kayıtlı oturum biyometrik doğrulama bekliyor.',
      );
    }
    return AuthState(tokens: tokens);
  }

  Future<void> unlockSavedSession() async {
    state = const AsyncLoading();
    final unlocked =
        await ref.read(biometricAuthServiceProvider).authenticate();
    if (!unlocked) {
      state = const AsyncData(
        AuthState(
          tokens: null,
          hasLockedSession: true,
          errorMessage: 'Biyometrik doğrulama tamamlanamadı.',
        ),
      );
      return;
    }
    final tokens = await ref.read(secureTokenStoreProvider).read();
    state = AsyncData(
      AuthState(
        tokens: tokens,
        hasLockedSession: tokens != null,
        errorMessage: tokens == null ? 'Kayıtlı oturum bulunamadı.' : null,
      ),
    );
  }

  Future<void> login(
    String email,
    String password, {
    bool rememberMe = true,
  }) async {
    state = const AsyncLoading();
    try {
      final tokens = await ref
          .read(authRepositoryProvider)
          .login(email: email, password: password);
      if (rememberMe) {
        await ref.read(secureTokenStoreProvider).save(tokens);
      } else {
        await ref.read(secureTokenStoreProvider).clear();
      }
      state =
          AsyncData(AuthState(tokens: tokens, hasLockedSession: rememberMe));
    } catch (error) {
      state = AsyncData(
        AuthState(
          tokens: null,
          errorMessage: readableApiError(error, 'Giriş tamamlanamadı.'),
        ),
      );
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    state = const AsyncLoading();
    try {
      final tokens = await ref.read(authRepositoryProvider).register(
            email: email,
            password: password,
            displayName: displayName,
          );
      await ref.read(secureTokenStoreProvider).save(tokens);
      state = AsyncData(const AuthState(tokens: null).copyWith(tokens: tokens));
    } catch (error) {
      state = AsyncData(
        AuthState(
          tokens: null,
          errorMessage: readableApiError(error, 'Kayıt tamamlanamadı.'),
        ),
      );
    }
  }

  Future<void> logout() async {
    final tokens = state.valueOrNull?.tokens;
    await ref.read(secureTokenStoreProvider).clear();
    state = const AsyncData(AuthState(tokens: null));
    if (tokens != null) {
      await ref.read(authRepositoryProvider).logout(tokens.refreshToken);
    }
  }
}
