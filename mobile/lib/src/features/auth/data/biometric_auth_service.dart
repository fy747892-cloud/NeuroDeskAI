import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:local_auth/local_auth.dart';

final biometricAuthServiceProvider = Provider<BiometricAuthService>((ref) {
  return BiometricAuthService(LocalAuthentication());
});

class BiometricAuthService {
  const BiometricAuthService(this._localAuth);

  final LocalAuthentication _localAuth;

  Future<bool> canAuthenticate() async {
    try {
      return await _localAuth.isDeviceSupported() &&
          await _localAuth.canCheckBiometrics;
    } catch (_) {
      return false;
    }
  }

  Future<bool> authenticate() async {
    if (!await canAuthenticate()) {
      return true;
    }
    try {
      return _localAuth.authenticate(
        localizedReason: 'NeuroDesk AI oturumunu açmak için doğrula.',
        options: const AuthenticationOptions(
          biometricOnly: false,
          stickyAuth: true,
        ),
      );
    } catch (_) {
      return false;
    }
  }
}
