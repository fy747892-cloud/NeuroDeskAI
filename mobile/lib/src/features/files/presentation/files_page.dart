import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api/api_error.dart';
import '../../ai_approvals/data/ai_approvals_repository.dart';
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
                      'PDF, Word, Excel, metin, ses ve e-posta dosyalarını yükle; AI özet ve aksiyon önerilerini çıkar.',
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
          _UploadGuideCard(
            isUploading: _isUploading,
            onUpload: _pickAndUpload,
          ),
          const SizedBox(height: 16),
          files.when(
            data: (items) => items.isEmpty
                ? const _PageMessage(
                    message:
                        'Henüz dosya yok. Excel, PDF, Word veya ses dosyası yükleyerek başlayabilirsin.',
                  )
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
                          onDownload: () => _download(file),
                          onShowText: () => _showExtractedText(file),
                          onShowAnalysis: () => _showAnalysis(file),
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
      await ref.read(filesRepositoryProvider).analyzeFile(file.id);
      setState(() {
        _notice =
            '${file.filename} analiz edildi. Görev/randevu önerileri varsa Onay Merkezi’nde bekliyor.';
      });
      ref.invalidate(filesProvider);
      ref.invalidate(pendingAiApprovalsProvider);
      if (mounted) {
        final messenger = ScaffoldMessenger.of(context);
        messenger.hideCurrentSnackBar();
        messenger.showSnackBar(
          SnackBar(
            content: const Text('Analiz tamamlandı. Onay Merkezi’ne geçebilirsin.'),
            action: SnackBarAction(
              label: 'Aç',
              onPressed: () => context.go('/app/approvals'),
            ),
          ),
        );
      }
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
          'xlsx',
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
      ref.invalidate(filesProvider);
      setState(() => _activeFileId = uploaded.id);
      try {
        await ref.read(filesRepositoryProvider).analyzeFile(uploaded.id);
        ref.invalidate(pendingAiApprovalsProvider);
        setState(() {
          _notice =
              '${uploaded.filename} yüklendi ve analiz edildi. Öneriler varsa Onay Merkezi’nde bekliyor.';
        });
      } catch (error) {
        setState(() {
          _notice =
              '${uploaded.filename} yüklendi, ancak analiz başlatılamadı: ${readableApiError(error, 'bilinmeyen hata')}. Karttaki Analiz et butonuyla tekrar deneyebilirsin.';
        });
      }
      setState(() {
        _activeFileId = null;
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
            child: const Text('Vazgeç'),
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

  Future<void> _download(FileRecord file) async {
    setState(() {
      _activeFileId = file.id;
      _notice = null;
    });

    try {
      final url = await ref.read(filesRepositoryProvider).getDownloadUrl(file.id);
      final launched = await launchUrl(
        Uri.parse(url),
        mode: LaunchMode.externalApplication,
      );
      if (!launched) {
        setState(() => _notice = 'Dosya bağlantısı açılamadı.');
      }
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Dosya indirilemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeFileId = null);
      }
    }
  }

  Future<void> _showExtractedText(FileRecord file) async {
    setState(() {
      _activeFileId = file.id;
      _notice = null;
    });

    try {
      final text = await ref.read(filesRepositoryProvider).getText(file.id);
      if (!mounted) return;
      await _showLongTextDialog(
        title: '${file.filename} metni',
        status: text.status,
        content: text.extractedText ?? 'Çıkarılmış metin yok.',
      );
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Dosya metni alınamadı.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeFileId = null);
      }
    }
  }

  Future<void> _showAnalysis(FileRecord file) async {
    setState(() {
      _activeFileId = file.id;
      _notice = null;
    });

    try {
      final analysis = await ref.read(filesRepositoryProvider).getAnalysis(file.id);
      if (!mounted) return;
      await _showLongTextDialog(
        title: '${file.filename} özeti',
        status: analysis.status,
        content: analysis.summary ?? 'Analiz özeti yok.',
      );
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Analiz özeti alınamadı.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeFileId = null);
      }
    }
  }

  Future<void> _showLongTextDialog({
    required String title,
    required String status,
    required String content,
  }) {
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Chip(
                  label: Text(_statusLabel(status)),
                  visualDensity: VisualDensity.compact,
                ),
                const SizedBox(height: 10),
                SelectableText(content),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Kapat'),
          ),
        ],
      ),
    );
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

class _UploadGuideCard extends StatelessWidget {
  const _UploadGuideCard({
    required this.isUploading,
    required this.onUpload,
  });

  final bool isUploading;
  final VoidCallback onUpload;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: theme.colorScheme.primary.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.upload_file,
                color: theme.colorScheme.primary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Dosya yükle ve yorumlat',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Excel, PDF, Word, TXT, ses ve EML dosyaları desteklenir. En fazla ${_formatBytes(_maxUploadSizeBytes)}.',
                    style: theme.textTheme.bodySmall,
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: const [
                      _FormatChip(label: 'Excel'),
                      _FormatChip(label: 'PDF'),
                      _FormatChip(label: 'Word'),
                      _FormatChip(label: 'Ses'),
                      _FormatChip(label: 'E-posta'),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            FilledButton.icon(
              onPressed: isUploading ? null : onUpload,
              icon: isUploading
                  ? const SizedBox.square(
                      dimension: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.add),
              label: Text(isUploading ? 'Yükleniyor' : 'Yükle'),
            ),
          ],
        ),
      ),
    );
  }
}

class _FormatChip extends StatelessWidget {
  const _FormatChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(label),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
    );
  }
}

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
    required this.onDownload,
    required this.onShowText,
    required this.onShowAnalysis,
    required this.onDelete,
  });

  final FileRecord file;
  final bool isActive;
  final VoidCallback onAnalyze;
  final VoidCallback onDownload;
  final VoidCallback onShowText;
  final VoidCallback onShowAnalysis;
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
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: isActive ? null : onAnalyze,
                  icon: isActive
                      ? const SizedBox.square(
                          dimension: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.auto_awesome),
                  label: const Text('Analiz et'),
                ),
                Tooltip(
                  message: 'Metni göster',
                  child: OutlinedButton.icon(
                    onPressed: isActive ? null : onShowText,
                    icon: const Icon(Icons.article_outlined),
                    label: const Text('Metin'),
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: isActive ? null : onShowAnalysis,
                  icon: const Icon(Icons.summarize_outlined),
                  label: const Text('Özet'),
                ),
                OutlinedButton.icon(
                  onPressed: isActive ? null : onDownload,
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Aç'),
                ),
                OutlinedButton.icon(
                  onPressed: isActive ? null : onDelete,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('Sil'),
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
    return Chip(
      label: Text(_statusLabel(status)),
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
    'xlsx' =>
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt' => 'text/plain',
    'mp3' => 'audio/mpeg',
    'wav' => 'audio/wav',
    'm4a' => 'audio/x-m4a',
    'eml' => 'message/rfc822',
    _ => 'text/plain',
  };
}

String _statusLabel(String status) {
  return switch (status) {
    'ready' => 'Hazır',
    'processing' => 'İşlemde',
    'failed' => 'Hata',
    'uploaded' => 'Yüklendi',
    'extracted' => 'Metin çıkarıldı',
    'unsupported' => 'Desteklenmiyor',
    'completed' => 'Tamamlandı',
    _ => status,
  };
}
