# Narzędzia Lokalizacyjne

Ten folder zawiera narzędzia do zarządzania tłumaczeniami modułu.

## LocalizationUpdater

Zaawansowany system Python do automatycznej aktualizacji tłumaczeń.

### Pliki:

- **update_localization.py** - Główny skrypt uruchamiający proces aktualizacji
- **localization_updater.py** - Klasa implementująca logikę porównywania i aktualizacji
- **translator_config.py** - Konfiguracja ścieżek i list plików
- **auto_translation_regex.py** - Wzorce regex do automatycznego tłumaczenia

### Użycie:

```bash
# Pobierz źródła i zaktualizuj tłumaczenia
npm run update

# Lub bezpośrednio:
python tools/LocalizationUpdater/update_localization.py --UpdateSourceData

# Wymusz ponowne tłumaczenie przez regex
python tools/LocalizationUpdater/update_localization.py --PerformRegexTranslate

# Tryb verbose (szczegółowe logi)
python tools/LocalizationUpdater/update_localization.py --UpdateSourceData -v
```

### Logi:

Wszystkie logi zapisywane są w `tools/LocalizationUpdater/Logs/`

Format: `LocalizationUpdate_YYYY-MM-DD_HH-MM-SS.log`

## Inne Narzędzia

### _Glossary

Słownik terminów do tłumaczenia (dla przyszłego rozwoju).

### UtilScripts

Pomocnicze skrypty narzędziowe (obecnie nieużywane w tym module).

## Zależności

Zainstaluj zależności Python:

```bash
pip install -r requirements.txt
```

Wymagane pakiety:
- colorama - kolorowanie outputu w terminalu
- regex - zaawansowane wyrażenia regularne
- tqdm - paski postępu
