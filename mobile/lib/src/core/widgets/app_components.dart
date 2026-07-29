import 'package:flutter/material.dart';

/// Shared visual primitives matching the NeuroDesk AI Stitch design
/// (projectId 3678649583756480882): a white rounded-xl card with a soft
/// 0.06-alpha shadow, small pill badges, section headings and the
/// "bento" stat-tile pair that recurs on Özet/Takvim. Centralizing these
/// keeps every rebuilt screen visually identical instead of each page
/// re-deriving its own radius/shadow/border values.
const kCardShadow = [
  BoxShadow(
    color: Color(0x0F17152F),
    blurRadius: 20,
    offset: Offset(0, 4),
  ),
];

const kFabShadow = [
  BoxShadow(
    color: Color(0x263525CD),
    blurRadius: 24,
    offset: Offset(0, 8),
  ),
];

const kCardRadius = 16.0;
const kLargeCardRadius = 20.0;
const kScreenPadding = EdgeInsets.fromLTRB(20, 16, 20, 100);

/// White rounded-xl card with the Stitch soft shadow. Used everywhere a
/// Stitch mockup shows a `bg-white rounded-xl/2xl card-shadow` block.
class AppCard extends StatelessWidget {
  const AppCard({
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.radius = kCardRadius,
    this.color,
    this.onTap,
    super.key,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final Color? color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final card = Container(
      decoration: BoxDecoration(
        color: color ?? Colors.white,
        borderRadius: BorderRadius.circular(radius),
        boxShadow: kCardShadow,
      ),
      // Material(transparency) so any interactive child (ListTile,
      // CheckboxListTile, InkWell, ...) finds a Material ancestor for its
      // ink/splash effects instead of painting invisibly under the
      // decorated background -- without this, Flutter throws a debug
      // assertion for e.g. a CheckboxListTile nested in an AppCard.
      child: Material(
        type: MaterialType.transparency,
        borderRadius: BorderRadius.circular(radius),
        child: Padding(padding: padding, child: child),
      ),
    );

    if (onTap == null) return card;

    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(radius),
      child: InkWell(
        borderRadius: BorderRadius.circular(radius),
        onTap: onTap,
        child: card,
      ),
    );
  }
}

/// Small rounded-full colored badge, e.g. "Analiz Edildi", "BEKLEMEDE".
class StatusPill extends StatelessWidget {
  const StatusPill({
    required this.label,
    required this.color,
    this.icon,
    this.dense = false,
    super.key,
  });

  final String label;
  final Color color;
  final IconData? icon;
  final bool dense;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: dense ? 8 : 12,
        vertical: dense ? 3 : 6,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: dense ? 12 : 15, color: color),
            const SizedBox(width: 5),
          ],
          Text(
            label,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w700,
              fontSize: dense ? 10 : 12,
              letterSpacing: dense ? 0.4 : 0,
            ),
          ),
        ],
      ),
    );
  }
}

/// "Title" + optional trailing action, e.g. "Bugünkü Program · 11 Ekim".
class SectionHeading extends StatelessWidget {
  const SectionHeading({
    required this.title,
    this.trailing,
    this.onTrailingTap,
    super.key,
  });

  final String title;
  final String? trailing;
  final VoidCallback? onTrailingTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: theme.textTheme.titleMedium),
        if (trailing != null)
          if (onTrailingTap != null)
            TextButton(
              onPressed: onTrailingTap,
              style: TextButton.styleFrom(
                foregroundColor: theme.colorScheme.secondary,
                padding: EdgeInsets.zero,
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: Text(trailing!,
                  style: const TextStyle(fontWeight: FontWeight.w700)),
            )
          else
            Text(
              trailing!,
              style: TextStyle(
                color: theme.colorScheme.secondary,
                fontWeight: FontWeight.w700,
                fontSize: 12,
              ),
            ),
      ],
    );
  }
}

/// The primary-filled "value + label" tile used for e.g. "Tamamlanan 12/15".
class BentoStatTile extends StatelessWidget {
  const BentoStatTile({
    required this.icon,
    required this.label,
    required this.value,
    super.key,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF3525CD),
        borderRadius: BorderRadius.circular(kCardRadius),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white),
          const SizedBox(height: 8),
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              color: Colors.white70,
              fontWeight: FontWeight.w700,
              fontSize: 11,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 28,
              fontWeight: FontWeight.w800,
              height: 1.1,
            ),
          ),
        ],
      ),
    );
  }
}

/// The white bordered "label + short text" tile paired with [BentoStatTile],
/// e.g. the "AI ÖZETİ" card next to "Tamamlanan".
class InfoTile extends StatelessWidget {
  const InfoTile({
    required this.icon,
    required this.label,
    required this.text,
    super.key,
  });

  final IconData icon;
  final String label;
  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(kCardRadius),
        border: Border.all(color: const Color(0xFFC7C4D8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: theme.colorScheme.secondary),
              Text(
                label.toUpperCase(),
                style: TextStyle(
                  color: theme.colorScheme.outline,
                  fontWeight: FontWeight.w700,
                  fontSize: 11,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            text,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

/// Color coding matching the Stitch task-priority left-border stripes.
Color priorityColor(String priority) {
  return switch (priority.toLowerCase()) {
    'urgent' || 'high' => const Color(0xFFEF4444),
    'medium' => const Color(0xFFF59E0B),
    _ => const Color(0xFF22C55E),
  };
}

/// Squircle icon-in-tinted-box used across list rows (contacts, more grid,
/// settings rows) to avoid re-declaring the same BoxDecoration everywhere.
class TintedIcon extends StatelessWidget {
  const TintedIcon({
    required this.icon,
    required this.color,
    this.size = 40,
    this.radius = 12,
    super.key,
  });

  final IconData icon;
  final Color color;
  final double size;
  final double radius;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(radius),
      ),
      child: Icon(icon, color: color, size: size * 0.5),
    );
  }
}
