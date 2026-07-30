import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
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

  @override
  Widget build(BuildContext context) {
    final files = ref.watch(filesProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(filesProvider.future),
      child: ListView(
        padding: kScreenPadding,
        children: [
          StitchDetailHeader(
            title: 'Icerik takibi',
            onBack: () =>
                context.canPop() ? context.pop() : context.go('/app/more'),
          ),
          Text(
            'Webden yuklenen dosya, ses, e-posta ve dokumanlar burada sadece takip edilir. '
            'Yukleme, duzenleme ve analiz baslatma islemleri web panelinden yapilir.',
            style: theme.textTheme.bodyMedium,
          ),
          if (_notice != null) ...[
            const SizedBox(height: 12),
            _Notice(message: _notice!),
          ],
          const SizedBox(height: 16),
          files.when(
            data: (items) {
              if (items.isEmpty) {
                return const _PageMessage(
                  message: 'Backendde goruntulenecek icerik henuz yok.',
                );
              }
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _FilesSummary(files: items),
                  const SizedBox(height: 14),
                  for (final file in items)
                    _FileCard(
                      file: file,
                      isActive: _activeFileId == file.id,
                      onDownload: () => _download(file),
                      onShowText: () => _showExtractedText(file),
                      onShowAnalysis: () => _showAnalysis(file),
                    ),
                ],
              );
            },
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Icerikler alinamadi.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
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
        setState(() => _notice = 'Icerik baglantisi acilamadi.');
      }
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Icerik acilamadi.');
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
        content: text.extractedText ?? 'Cikarilmis metin yok.',
      );
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Icerik metni alinamadi.');
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
        title: '${file.filename} ozeti',
        status: analysis.status,
        content: analysis.summary ?? 'Analiz ozeti yok.',
      );
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'Analiz ozeti alinamadi.');
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
}

class _FilesSummary extends StatelessWidget {
  const _FilesSummary({required this.files});

  final List<FileRecord> files;

  @override
  Widget build(BuildContext context) {
    final readyCount = files.where((file) => file.status == 'ready').length;
    final totalBytes = files.fold<int>(0, (sum, file) => sum + file.sizeBytes);

    return AppCard(
      radius: kLargeCardRadius,
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Expanded(
            child: _Metric(
              icon: Icons.folder_outlined,
              label: 'Icerik',
              value: files.length.toString(),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _Metric(
              icon: Icons.verified_outlined,
              label: 'Hazir',
              value: readyCount.toString(),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _Metric(
              icon: Icons.storage_outlined,
              label: 'Boyut',
              value: _formatBytes(totalBytes),
            ),
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: theme.colorScheme.primary, size: 20),
        const SizedBox(height: 8),
        Text(
          value,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w800,
          ),
        ),
        Text(label, style: theme.textTheme.bodySmall),
      ],
    );
  }
}

class _FileCard extends StatelessWidget {
  const _FileCard({
    required this.file,
    required this.isActive,
    required this.onDownload,
    required this.onShowText,
    required this.onShowAnalysis,
  });

  final FileRecord file;
  final bool isActive;
  final VoidCallback onDownload;
  final VoidCallback onShowText;
  final VoidCallback onShowAnalysis;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TintedIcon(
                  icon: _iconForMime(file.mimeType),
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        file.filename,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.titleMedium,
                      ),
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
                const SizedBox(width: 8),
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
                OutlinedButton.icon(
                  onPressed: isActive ? null : onShowText,
                  icon: const Icon(Icons.article_outlined),
                  label: const Text('Metin'),
                ),
                OutlinedButton.icon(
                  onPressed: isActive ? null : onShowAnalysis,
                  icon: const Icon(Icons.summarize_outlined),
                  label: const Text('Ozet'),
                ),
                OutlinedButton.icon(
                  onPressed: isActive ? null : onDownload,
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Ac'),
                ),
                if (isActive)
                  const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
          ],
        ),
      ),
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
    return AppCard(padding: const EdgeInsets.all(12), child: Text(message));
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return AppCard(child: Text(message));
  }
}

IconData _iconForMime(String mimeType) {
  final lower = mimeType.toLowerCase();
  if (lower.contains('audio')) return Icons.graphic_eq;
  if (lower.contains('pdf')) return Icons.picture_as_pdf_outlined;
  if (lower.contains('spreadsheet') || lower.contains('excel')) {
    return Icons.table_chart_outlined;
  }
  if (lower.contains('mail') || lower.contains('message')) {
    return Icons.mail_outline;
  }
  return Icons.description_outlined;
}

String _formatBytes(int bytes) {
  if (bytes < 1024) return '$bytes B';
  if (bytes < 1024 * 1024) return '${(bytes / 1024).round()} KB';
  return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}

String _statusLabel(String status) {
  return switch (status) {
    'ready' => 'Hazir',
    'processing' => 'Islemde',
    'failed' => 'Hata',
    'uploaded' => 'Yuklendi',
    'extracted' => 'Metin cikarildi',
    'unsupported' => 'Desteklenmiyor',
    'completed' => 'Tamamlandi',
    _ => status,
  };
}
