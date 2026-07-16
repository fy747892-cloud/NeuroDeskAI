import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/email_models.dart';

final emailRepositoryProvider = Provider<EmailRepository>((ref) {
  return EmailRepository(ref.watch(dioProvider));
});

final emailAccountsProvider =
    FutureProvider.autoDispose<List<EmailAccount>>((ref) {
  return ref.watch(emailRepositoryProvider).listAccounts();
});

final emailMessagesProvider =
    FutureProvider.autoDispose.family<List<EmailMessage>, String>((
  ref,
  accountId,
) {
  return ref.watch(emailRepositoryProvider).listMessages(accountId);
});

class EmailRepository {
  const EmailRepository(this._dio);

  final Dio _dio;

  Future<List<EmailAccount>> listAccounts() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/email/accounts');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(EmailAccount.fromJson)
        .toList(growable: false);
  }

  Future<List<EmailMessage>> listMessages(String accountId) async {
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/email/accounts/$accountId/messages',
    );
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(EmailMessage.fromJson)
        .toList(growable: false);
  }

  Future<EmailConnectStart> startConnect(String provider) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/email/$provider/connect',
    );
    return EmailConnectStart.fromJson(response.data!);
  }

  Future<EmailSyncSummary> syncAccount(String accountId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/email/accounts/$accountId/sync',
    );
    return EmailSyncSummary.fromJson(response.data!);
  }

  Future<EmailAccount> revokeAccount(String accountId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/email/accounts/$accountId/revoke',
    );
    return EmailAccount.fromJson(response.data!);
  }
}
