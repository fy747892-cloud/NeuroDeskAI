import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/ai_analysis_job.dart';
import '../domain/call_record.dart';

final callsRepositoryProvider = Provider<CallsRepository>((ref) {
  return CallsRepository(ref.watch(dioProvider));
});

final callsProvider = FutureProvider.autoDispose<List<CallRecord>>((ref) {
  return ref.watch(callsRepositoryProvider).listCalls();
});

/// All AI analysis jobs for the org — used to look up each call's analysis
/// status by matching `sourceId` against a call's `conversationId`, since
/// jobs aren't returned nested under `/calls`.
final callAnalysisJobsProvider =
    FutureProvider.autoDispose<List<AiAnalysisJob>>((ref) {
  return ref.watch(callsRepositoryProvider).listAnalysisJobs();
});

class CallsRepository {
  const CallsRepository(this._dio);

  final Dio _dio;

  Future<List<CallRecord>> listCalls() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/calls');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(CallRecord.fromJson)
        .toList(growable: false);
  }

  Future<List<AiAnalysisJob>> listAnalysisJobs() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/ai/analysis/jobs');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(AiAnalysisJob.fromJson)
        .toList(growable: false);
  }

}
