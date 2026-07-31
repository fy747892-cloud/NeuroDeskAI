import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum AppLanguage {
  tr(Locale('tr'), 'Türkçe'),
  en(Locale('en'), 'English');

  const AppLanguage(this.locale, this.label);

  final Locale locale;
  final String label;
}

final appLanguageProvider = StateProvider<AppLanguage>((ref) => AppLanguage.tr);

AppStrings appStrings(WidgetRef ref) =>
    AppStrings(ref.watch(appLanguageProvider));

class AppStrings {
  const AppStrings(this.language);

  final AppLanguage language;

  bool get isEnglish => language == AppLanguage.en;

  String get summary => isEnglish ? 'Summary' : 'Özet';
  String get content => isEnglish ? 'Content' : 'İçerik';
  String get tasks => isEnglish ? 'Tasks' : 'Görevler';
  String get contacts => isEnglish ? 'Contacts' : 'Kişiler';
  String get more => isEnglish ? 'More' : 'Daha Fazla';
  String get retry => isEnglish ? 'Retry' : 'Dene';
  String get connectionError =>
      isEnglish ? 'Connection error' : 'Bağlantı hatası';
  String apiWeak([String? statusLabel]) {
    if (statusLabel == null) {
      return isEnglish
          ? 'API connection is weak. Check backend and network status.'
          : 'API bağlantısı zayıf. Backend ve ağ durumunu kontrol edin.';
    }
    return isEnglish
        ? 'API connection is weak: $statusLabel. Check backend and network status.'
        : 'API bağlantısı zayıf: $statusLabel. Backend ve ağ durumunu kontrol edin.';
  }

  String get settings => isEnglish ? 'Settings' : 'Ayarlar';
  String get general => isEnglish ? 'General' : 'Genel';
  String get languageSetting => isEnglish ? 'Language' : 'Dil';
  String get languageSubtitle =>
      isEnglish ? 'Mobile app display language' : 'Mobil uygulama dili';
  String get notifications => isEnglish ? 'Notifications' : 'Bildirimler';
  String get connectedAccounts =>
      isEnglish ? 'Connected Accounts' : 'Bağlı Hesaplar';
  String get account => isEnglish ? 'Account' : 'Hesap';
  String get support => isEnglish ? 'Support' : 'Destek';
  String get signOut => isEnglish ? 'Sign out' : 'Çıkış yap';
  String get settingsLoadFailed =>
      isEnglish ? 'Settings could not be loaded.' : 'Ayarlar alınamadı.';
  String get profile => isEnglish ? 'Profile' : 'Profil';
  String get fullName => isEnglish ? 'Full name' : 'Ad soyad';
  String get title => isEnglish ? 'Title' : 'Unvan';
  String get saveProfile => isEnglish ? 'Save profile' : 'Profili kaydet';
  String get fullNameRequired =>
      isEnglish ? 'Full name is required.' : 'Ad soyad zorunlu.';
  String get profileUpdated =>
      isEnglish ? 'Profile updated.' : 'Profil güncellendi.';
  String get profileUpdateFailed =>
      isEnglish ? 'Profile could not be updated.' : 'Profil güncellenemedi.';
  String get peopleAndCalendar =>
      isEnglish ? 'Contacts and Calendar' : 'Kişiler ve Takvim';
  String get emails => isEnglish ? 'Emails' : 'E-postalar';
  String get calendar => isEnglish ? 'Calendar' : 'Takvim';
  String get viewAppointments =>
      isEnglish ? 'View appointments' : 'Randevuları görüntüle';
  String get connected => isEnglish ? 'Connected' : 'Bağlı';
  String get notConnected => isEnglish ? 'Not connected' : 'Bağlı değil';
  String get email => isEnglish ? 'Email' : 'E-posta';
  String get status => isEnglish ? 'Status' : 'Durum';
  String get emailVerified =>
      isEnglish ? 'Email verified' : 'E-posta doğrulandı';
  String get yes => isEnglish ? 'Yes' : 'Evet';
  String get no => isEnglish ? 'No' : 'Hayır';
  String get phone => isEnglish ? 'Phone' : 'Telefon';

  String accountStatus(String status) {
    return switch (status.toLowerCase()) {
      'active' => isEnglish ? 'Active' : 'Aktif',
      'inactive' => isEnglish ? 'Inactive' : 'Pasif',
      'pending' => isEnglish ? 'Pending' : 'Beklemede',
      'suspended' => isEnglish ? 'Suspended' : 'Askıya alındı',
      _ => status,
    };
  }
}
