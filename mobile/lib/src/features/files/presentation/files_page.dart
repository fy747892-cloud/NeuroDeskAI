import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';

import '../../../core/api/api_error.dart';
import '../data/files_repository.dart';
import '../domain/file_record.dart';

class FilesPage extends ConsumerStatefulWidget {
  const FilesPage({super.key});

  @override
  ConsumerState<FilesPage> createState() => _FilesPageState();
}

class _FilesPageState extends ConsumerState<FilesPage> {
  String? _activeFileId;
  String? _notice;
  bool _isUploading = false;

  @override
  Widget build(BuildContext context) {
    final files = ref.watch(filesProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(filesProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Dosyalar', style: theme.textTheme.headlineMedium),
                    const SizedBox(height: 6),
                    Text(
                      'Yüklenen dokümanları izle, analiz et ve temizle.',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              IconButton.filled(
                tooltip: 'Dosya yükle',
                onPressed: _isUploading ? null : _pickAndUpload,
                icon: _isUploading
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.upload_file),
              ),
            ],
          ),
          if (_notice != null) ...[
            const SizedBox(height: 12),
            _Notice(message: _notice!),
          ],
          const SizedBox(height: 16),
          files.when(
            data: (items) => items.isEmpty
                ? const _PageMessage(message: 'Dosya bulunmuyor.')
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _FilesSummary(files: items),
                      const SizedBox(height: 14),
                      ...items.map(
                        (file) => _FileCard(
                          file: file,
                          isActive: _activeFileId == file.id,
                          onAnalyze: () => _analyze(file),
                          onDelete: () => _confirmDelete(file),
                        ),
                      ),
                    ],
                  ),
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Dosyalar alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }

  Future<void> _analyze(FileRecord file) async {
    setState(() {
      _activeFileId = file.id;
      _notice = null;
    });

    try {
      final analysis =
          await ref.read(filesRepositoryProvider).analyzeFile(file.id);
      setState(() {
        _notice = '${file.filename} analiz durumu: ${analysis.status}';
      });
      ref.invalidate(filesProvider);
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Dosya analiz edilemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeFileId = null);
      }
    }
  }

  Future<void> _pickAndUpload() async {
    setState(() {
      _isUploading = true;
      _notice = null;
    });

    try {
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: false,
        type: FileType.custom,
        allowedExtensions: const [
          'pdf',
          'docx',
          'txt',
          'mp3',
          'wav',
          'm4a',
          'eml',
        ],
        withData: false,
        withReadStream: true,
      );
      final file = result?.files.single;
      if (file == null) {
        return;
      }
      if (file.size > _maxUploadSizeBytes) {
        setState(() {
          _notice =
              '${file.name} yüklenemedi. En fazla ${_formatBytes(_maxUploadSizeBytes)} dosya yükleyebilirsin.';
        });
        return;
      }
      final stream = file.readStream;
      if (stream == null || file.size <= 0) {
        setState(() {
          _notice = 'Dosya okunamadı.';
        });
        return;
      }

      final uploaded = await ref.read(filesRepositoryProvider).uploadFile(
            filename: file.name,
            mimeType: _mimeTypeFor(file.extension),
            sizeBytes: file.size,
            bytes: stream,
          );
      setState(() {
        _notice = '${uploaded.filename} yüklendi.';
      });
      ref.invalidate(filesProvider);
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Dosya yüklenemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isUploading = false);
      }
    }
  }

  Future<void> _confirmDelete(FileRecord file) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Dosyayı sil'),
        content: Text('${file.filename} kalıcı olarak silinsin mi?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Vazgec'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Sil'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _delete(file);
    }
  }

  Future<void> _delete(FileRecord file) async {
    setState(() {
      _activeFileId = file.id;
      _notice = null;
    });

    try {
      await ref.read(filesRepositoryProvider).deleteFile(file.id);
      setState(() => _notice = '${file.filename} silindi.');
      ref.invalidate(filesProvider);
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Dosya silinemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeFileId = null);
      }
    }
  }
}

const _maxUploadSizeBytes = 25 * 1024 * 1024;

class _FilesSummary extends StatelessWidget {
  const _FilesSummary({required this.files});

  final List<FileRecord> files;

  @override
  Widget build(BuildContext context) {
    final readyCount = files.where((file) => file.status == 'ready').length;
    final totalBytes = files.fold<int>(0, (sum, file) => sum + file.sizeBytes);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF17152F),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              label: 'Dosya',
              value: files.length.toString(),
              icon: Icons.folder_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Hazır',
              value: readyCount.toString(),
              icon: Icons.verified_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Boyut',
              value: _formatBytes(totalBytes),
              icon: Icons.storage_outlined,
            ),
          ),
        ],
      ),
    );
  }
}

class _FileCard extends StatelessWidget {
  const _FileCard({
    required this.file,
    required this.isActive,
    required this.onAnalyze,
    required this.onDelete,
  });

  final FileRecord file;
  final bool isActive;
  final VoidCallback onAnalyze;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: const Color(0x1A3525CD),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.description_outlined,
                    color: Color(0xFF3525CD),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(file.filename, style: theme.textTheme.titleMedium),
                      const SizedBox(height: 4),
                      Text(
                        file.mimeType,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                _StatusChip(status: file.status),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: [
                _MetaLine(
                  icon: Icons.storage_outlined,
                  text: _formatBytes(file.sizeBytes),
                ),
                _MetaLine(
                  icon: Icons.schedule,
                  text: _formatDateTime(file.createdAt),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: isActive ? null : onAnalyze,
                    icon: isActive
                        ? const SizedBox.square(
                            dimension: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.auto_awesome),
                    label: const Text('Analiz et'),
                  ),
                ),
                const SizedBox(width: 10),
                IconButton.outlined(
                  tooltip: 'Sil',
                  onPressed: isActive ? null : onDelete,
                  icon: const Icon(Icons.delete_outline),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: Colors.white, size: 20),
        const SizedBox(height: 8),
        Text(
          value,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.w800,
              ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.white.withValues(alpha: 0.72),
              ),
        ),
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final label = switch (status) {
      'ready' => 'Hazır',
      'processing' => 'İşlemde',
      'failed' => 'Hata',
      'uploaded' => 'Yüklendi',
      _ => status,
    };

    return Chip(
      label: Text(label),
      visualDensity: VisualDensity.compact,
    );
  }
}

class _MetaLine extends StatelessWidget {
  const _MetaLine({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 16,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 5),
        Text(text, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFFF4F5FB),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Text(message),
      ),
    );
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(message),
      ),
    );
  }
}

String _formatBytes(int bytes) {
  if (bytes < 1024) {
    return '$bytes B';
  }
  if (bytes < 1024 * 1024) {
    return '${(bytes / 1024).round()} KB';
  }
  return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}

String _mimeTypeFor(String? extension) {
  return switch (extension?.toLowerCase()) {
    'pdf' => 'application/pdf',
    'docx' =>
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'txt' => 'text/plain',
    'mp3' => 'audio/mpeg',
    'wav' => 'audio/wav',
    'm4a' => 'audio/x-m4a',
    'eml' => 'message/rfc822',
    _ => 'text/plain',
  };
}
