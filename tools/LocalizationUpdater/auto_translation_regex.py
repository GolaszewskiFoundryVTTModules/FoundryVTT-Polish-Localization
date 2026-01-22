import regex

# Basic formatting and typography for Foundry VTT
formatting_patterns = [
    (r' [—-](\d+)', r' –\1'),
    (r'(\S)—(\S)', r'\1 — \2'),
    (r'([„""])', r'"'),
    (r'([''])', r"'"),
    (r'>\n<', r'><'),
    (r'…', r'...'),
]

# Common Foundry VTT terms - Core functionality
foundry_core_patterns = [
    # Common UI terms (case-sensitive where appropriate)
    (r'\bSettings\b', r'Ustawienia'),
    (r'\bConfiguration\b', r'Konfiguracja'),
    (r'\bPermissions\b', r'Uprawnienia'),
    (r'\bPlayers\b', r'Gracze'),
    (r'\bPlayer\b', r'Gracz'),
    (r'\bGamemaster\b', r'Mistrz Gry'),
    (r'\bGM\b', r'MG'),
    (r'\bWorld\b', r'Świat'),
    (r'\bScene\b', r'Scena'),
    (r'\bActor\b', r'Aktor'),
    (r'\bActors\b', r'Aktorzy'),
    (r'\bItem\b', r'Przedmiot'),
    (r'\bItems\b', r'Przedmioty'),
    (r'\bJournal\b', r'Dziennik'),
    (r'\bRollTable\b', r'Tabela'),
    (r'\bPlaylist\b', r'Lista Odtwarzania'),
    (r'\bCompendium\b', r'Kompendium'),
    (r'\bMacro\b', r'Makro'),
    (r'\bCombat\b', r'Walka'),
    (r'\bChat\b', r'Czat'),
    (r'\bFolder\b', r'Folder'),
    (r'\bModule\b', r'Moduł'),
    (r'\bSystem\b', r'System'),
    (r'\bCanvas\b', r'Płótno'),
    (r'\bToken\b', r'Token'),
    (r'\bTile\b', r'Kafelek'),
    (r'\bWall\b', r'Ściana'),
    (r'\bDoor\b', r'Drzwi'),
    (r'\bLight\b', r'Światło'),
    (r'\bSound\b', r'Dźwięk'),
]

# Dice and rolling terms
dice_patterns = [
    (r'\bRoll\b', r'Rzut'),
    (r'\bDice\b', r'Kości'),
    (r'\bFormula\b', r'Formuła'),
]

# Document management
document_patterns = [
    (r'\bCreate\b', r'Utwórz'),
    (r'\bEdit\b', r'Edytuj'),
    (r'\bDelete\b', r'Usuń'),
    (r'\bDuplicate\b', r'Duplikuj'),
    (r'\bImport\b', r'Importuj'),
    (r'\bExport\b', r'Eksportuj'),
    (r'\bSave\b', r'Zapisz'),
    (r'\bCancel\b', r'Anuluj'),
    (r'\bSubmit\b', r'Zatwierdź'),
    (r'\bReset\b', r'Resetuj'),
    (r'\bUpdate\b', r'Aktualizuj'),
]

# Common actions and verbs
action_patterns = [
    (r'\bEnable\b', r'Włącz'),
    (r'\bDisable\b', r'Wyłącz'),
    (r'\bActivate\b', r'Aktywuj'),
    (r'\bDeactivate\b', r'Dezaktywuj'),
    (r'\bShow\b', r'Pokaż'),
    (r'\bHide\b', r'Ukryj'),
    (r'\bToggle\b', r'Przełącz'),
    (r'\bClear\b', r'Wyczyść'),
    (r'\bSelect\b', r'Wybierz'),
    (r'\bDeselect\b', r'Odznacz'),
]

# Visibility and permission terms
visibility_patterns = [
    (r'\bPublic\b', r'Publiczny'),
    (r'\bPrivate\b', r'Prywatny'),
    (r'\bVisible\b', r'Widoczny'),
    (r'\bHidden\b', r'Ukryty'),
    (r'\bOwner\b', r'Właściciel'),
    (r'\bObserver\b', r'Obserwator'),
    (r'\bLimited\b', r'Ograniczony'),
    (r'\bNone\b', r'Brak'),
]

# Common Foundry VTT setting categories
setting_categories = [
    (r'\bCore Settings\b', r'Ustawienia Rdzenia'),
    (r'\bSystem Settings\b', r'Ustawienia Systemu'),
    (r'\bModule Settings\b', r'Ustawienia Modułów'),
    (r'\bDefault Language\b', r'Domyślny Język'),
    (r'\bVideo/Audio\b', r'Wideo/Audio'),
]

# Combine all patterns in order of priority
default_patterns = (
    formatting_patterns +
    foundry_core_patterns +
    dice_patterns +
    document_patterns +
    action_patterns +
    visibility_patterns +
    setting_categories
)

# Mapping of keywords to pattern sets
# Keys are tuples of lowercase substrings to search for in 'label' or filename
# Values are the pattern sets to use
PATTERN_MAPPING = {
    'default': default_patterns
}
