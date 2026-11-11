# Docko

Darmowy program do zamiany plików PDF na dokumenty Word (`.docx`) dla Windows. Nie trzeba instalować Pythona: pobierasz jeden plik `Docko.exe` i go uruchamiasz.

**Strona pobierania:** [https://premiumzadaszenia.github.io/docko/](https://premiumzadaszenia.github.io/docko/)

**Bezpośredni plik:** [Docko.exe](https://github.com/PremiumZadaszenia/docko/releases/latest/download/Docko.exe)

## Jak używać

1. Pobierz `Docko.exe` (Windows 10 lub 11).
2. Uruchom program i kliknij **Wybierz PDF**. Możesz zaznaczyć kilka plików naraz.
3. Dokument `.docx` pojawi się w tym samym folderze, obok oryginalnego PDF, pod tą samą nazwą.

Zamiana dzieje się na Twoim komputerze. Pliki nie są wysyłane do internetu, a po pobraniu program działa offline.

Z wiersza poleceń (bez okienka):

```bat
Docko.exe dokument.pdf
Docko.exe pierwszy.pdf drugi.pdf
```

## Ostrzeżenie Windows (SmartScreen)

`Docko.exe` nie jest podpisany cyfrowo, więc przy pierwszym uruchomieniu Windows może pokazać komunikat **„System Windows ochronił ten komputer”**. To filtr SmartScreen, a nie komunikat o wirusie.

1. Kliknij **„Więcej informacji”**.
2. Kliknij **„Uruchom mimo to”**.

## Ograniczenia

- Skanowane PDF (same zdjęcia stron, bez warstwy tekstu) nie dadzą edytowalnego tekstu. Program nie ma OCR — strona trafi do dokumentu jako obraz. Jeśli w PDF-ie da się zaznaczyć tekst, wynik będzie tekstem.
- Skomplikowany układ (tabele, kolumny, przypisy) może wymagać ręcznej poprawki w Wordzie.
- Wynik to zawsze `.docx` (Word 2007 i nowszy). Starszy format `.doc` nie jest zapisywany.

## Wydania

Gotowy program jest dołączany do wydania GitHub przy znaczniku `v*` (na przykład `v1.0.0`). Nazwa pliku to dokładnie `Docko.exe`, stąd działa link `releases/latest/download/Docko.exe`.

Budowanie odbywa się w GitHub Actions na `windows-latest` (PyInstaller `--onefile --windowed`). Źródło programu to `docko.py`.
