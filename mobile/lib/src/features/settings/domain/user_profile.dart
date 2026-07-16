class CurrentUser {
  const CurrentUser({
    required this.id,
    required this.email,
    required this.tenantId,
    required this.status,
    required this.isEmailVerified,
    required this.createdAt,
    this.organizationId,
    this.profile,
  });

  final String id;
  final String email;
  final String tenantId;
  final String? organizationId;
  final String status;
  final bool isEmailVerified;
  final DateTime createdAt;
  final UserProfile? profile;

  factory CurrentUser.fromJson(Map<String, dynamic> json) {
    return CurrentUser(
      id: json['id'] as String,
      email: json['email'] as String,
      tenantId: json['tenant_id'] as String,
      organizationId: json['organization_id'] as String?,
      status: json['status'] as String,
      isEmailVerified: json['is_email_verified'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      profile: json['profile'] == null
          ? null
          : UserProfile.fromJson(json['profile'] as Map<String, dynamic>),
    );
  }
}

class UserProfile {
  const UserProfile({
    required this.fullName,
    this.title,
    this.avatarUrl,
  });

  final String fullName;
  final String? title;
  final String? avatarUrl;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      fullName: json['full_name'] as String,
      title: json['title'] as String?,
      avatarUrl: json['avatar_url'] as String?,
    );
  }
}
