# Changelog

## [1.3.0] - 2026-01-22

### Added
- **Zaawansowany System Aktualizacji Tłumaczeń**
  - Python-owe narzędzia do automatycznej aktualizacji tłumaczeń
  - Inteligentne porównywanie źródeł i wykrywanie zmian
  - Auto-tłumaczenie popularnych terminów Foundry VTT przez regex
  - Szczegółowe logi ze zmianami

- **Nowe narzędzia CLI:**
  - `npm run update` - pobiera źródła i automatycznie aktualizuje tłumaczenia
  - `npm run translate` - wymusza ponowne tłumaczenie przez regex

- **System Budowania:**
  - `npm run build` - buduje moduł z walidacją JSON
  - `npm run download` - pobiera źródłowe pliki z serwera SFTP
  - Inteligentna synchronizacja z serwerem (uploaduje tylko zmienione pliki)

- **Dokumentacja:**
  - QUICKSTART.md - szybki przewodnik
  - DEVELOPMENT.md - szczegółowa dokumentacja techniczna
  - README.md - zaktualizowany przegląd projektu

- **VS Code Integration:**
  - Taski do budowania, pobierania i aktualizacji
  - Skróty klawiszowe (Ctrl+Shift+B dla build)

### Technical Details
- Dodano `requirements.txt` z zależnościami Python
- Zintegrowano narzędzia z modułu `lang-pl-pf2e` i zaadaptowano do Foundry VTT
- System automatycznie:
  - Wykrywa nowe klucze i dodaje z auto-tłumaczeniem
  - Wykrywa zmienione nazwy kluczy i przenosi tłumaczenia
  - Wykrywa zmienione wartości i zaznacza wymagające uwagi
  - Usuwa nieaktualne klucze

## [1.2] - Previous version
- Podstawowa lokalizacja Foundry VTT
