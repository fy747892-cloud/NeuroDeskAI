import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/ai_action_approval.dart';

final aiApprovalsRepositoryProvider = Provider<AiApprovalsRepository>((ref) {
  return AiApprovalsRepository(ref.watch(dioProvider));
});

final pendingAiApprovalsProvider =
    FutureProvider.autoDispose<List<AiActionApproval>>((ref) async {
  return ref.watch(aiApprovalsRepositoryProvider).listPendingApprovals();
});

class AiApprovalsRepository {
  const AiApprovalsRepository(this._dio);

  final Dio _dio;

  Future<List<AiActionApproval>> listPendingApprovals() async {
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/ai/approvals',
      queryParameters: {'status_filter': 'pending'},
    );

    return response.data!
        .cast<Map<String, dynamic>>()
        .map(AiActionApproval.fromJson)
        .toList(growable: false);
  }

  Future<AiActionApproval> approve(AiActionApproval approval) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/ai/approvals/${approval.id}/approve',
      data: {'approved_payload': approval.suggestedPayload},
    );
    final approved = AiActionApproval.fromJson(response.data!);
    await _materializeApprovedAction(approved);
    return approved;
  }

  Future<AiActionApproval> reject(String approvalId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/ai/approvals/$approvalId/reject',
    );
    return AiActionApproval.fromJson(response.data!);
  }

  Future<void> _materializeApprovedAction(AiActionApproval approval) async {
    final endpoint = switch (approval.actionType) {
      'task' || 'create_task' => '/api/v1/tasks/from-approval',
      'appointment' ||
      'create_appointment' =>
        '/api/v1/appointments/from-approval',
      'deal' || 'create_deal' => '/api/v1/deals/from-approval',
      _ => null,
    };

    if (endpoint == null) {
      return;
    }

    await _dio.post<void>(
      endpoint,
      data: {'approval_id': approval.id},
    );
  }
}
