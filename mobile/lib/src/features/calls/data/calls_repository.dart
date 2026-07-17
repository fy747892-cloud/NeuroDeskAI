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

  Future<CallTextResult> createFromText({
    required String title,
    required String transcriptText,
    required List<String> participantNames,
    String? callDirection,
    String? phoneNumber,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/calls/text',
      data: {
        'title': title.trim(),
        'transcript_text': transcriptText.trim(),
        'participant_names': participantNames,
        'call_direction': _emptyToNull(callDirection),
        'phone_number': _emptyToNull(phoneNumber),
        'language': 'tr',
      },
    );
    return CallTextResult.fromJson(response.data!);
  }

  Future<CallTextResult> createFromAudio({
    required String title,
    required List<int> audioBytes,
    required List<String> participantNames,
    String? callDirection,
    String? phoneNumber,
    String language = 'tr',
  }) async {
    final formData = FormData.fromMap({
      'title': title.trim(),
      'participant_names': participantNames.join(','),
      if (callDirection != null) 'call_direction': callDirection,
      if (phoneNumber != null && phoneNumber.trim().isNotEmpty)
        'phone_number': phoneNumber.trim(),
      'language': language,
      'audio': MultipartFile.fromBytes(
        audioBytes,
        filename: 'recording.m4a',
        contentType: DioMediaType('audio', 'mp4'),
      ),
    });

    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/calls/audio',
      data: formData,
    );
    return CallTextResult.fromJson(response.data!);
  }

  Future<AiAnalysisJob> requestAnalysis(String conversationId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/ai/analysis/conversations/$conversationId',
    );
    return AiAnalysisJob.fromJson(response.data!);
  }

  Future<List<AiAnalysisJob>> listAnalysisJobs() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/ai/analysis/jobs');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(AiAnalysisJob.fromJson)
        .toList(growable: false);
  }

  Future<AiAnalysisJob> retryAnalysisJob(String jobId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/ai/analysis/jobs/$jobId/retry',
    );
    return AiAnalysisJob.fromJson(response.data!);
  }

  String? _emptyToNull(String? value) {
    final trimmed = value?.trim();
    return trimmed == null || trimmed.isEmpty ? null : trimmed;
  }
}
