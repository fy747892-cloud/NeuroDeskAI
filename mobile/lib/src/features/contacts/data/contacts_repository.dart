import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/contact.dart';

final contactsRepositoryProvider = Provider<ContactsRepository>((ref) {
  return ContactsRepository(ref.watch(dioProvider));
});

final contactsProvider =
    FutureProvider.autoDispose.family<List<Contact>, String?>((ref, search) {
  return ref.watch(contactsRepositoryProvider).listContacts(search: search);
});

final contactDetailProvider =
    FutureProvider.autoDispose.family<ContactDetail, String>((ref, contactId) {
  return ref.watch(contactsRepositoryProvider).getContact(contactId);
});

final contactMemoryProvider =
    FutureProvider.autoDispose.family<ContactMemory, String>((ref, contactId) {
  return ref.watch(contactsRepositoryProvider).getMemory(contactId);
});

class ContactsRepository {
  const ContactsRepository(this._dio);

  final Dio _dio;

  Future<List<Contact>> listContacts({String? search}) async {
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/contacts',
      queryParameters: {
        if (search != null && search.trim().isNotEmpty) 'search': search.trim(),
      },
    );
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(Contact.fromJson)
        .toList(growable: false);
  }

  Future<Contact> createContact({
    required String fullName,
    String? email,
    String? phone,
    String? company,
    String? title,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/contacts',
      data: {
        'full_name': fullName,
        'email': _emptyToNull(email),
        'phone': _emptyToNull(phone),
        'company': _emptyToNull(company),
        'title': _emptyToNull(title),
      },
    );
    return Contact.fromJson(response.data!);
  }

  Future<ContactDetail> getContact(String contactId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/contacts/$contactId',
    );
    return ContactDetail.fromJson(response.data!);
  }

  Future<ContactMemory> getMemory(String contactId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/contacts/$contactId/memory',
    );
    return ContactMemory.fromJson(response.data!);
  }

  Future<ContactNote> addNote(String contactId, String noteText) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/contacts/$contactId/notes',
      data: {'note_text': noteText},
    );
    return ContactNote.fromJson(response.data!);
  }

  String? _emptyToNull(String? value) {
    final trimmed = value?.trim();
    return trimmed == null || trimmed.isEmpty ? null : trimmed;
  }
}
