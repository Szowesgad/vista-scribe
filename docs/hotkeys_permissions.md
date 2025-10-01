# Skróty klawiaturowe i uprawnienia - Vista Scribe

## TL;DR - Szybka pomoc

1. Jeśli skróty klawiaturowe (⌃, ⇧⌘/ lub podwójny ⌥) nie działają:
   - Kliknij ikonę w pasku menu
   - Wybierz "Open System Accessibility Settings..."
   - Dodaj aplikację do listy dozwolonych programów
   - Wróć do Vista Scribe i wybierz "Enable Hotkeys"

2. Jeśli aplikacja "rozjebała użytkowość klawiatury":
   - Zamknij aplikację (Quit)
   - Uruchom ponownie z wyłączonymi skrótami: `HOTKEYS_ENABLED=0 uv run python main.py`

## Wymagane uprawnienia

Vista Scribe używa systemowych funkcji macOS do przechwytywania globalnych skrótów klawiaturowych, które działają w całym systemie. Wymaga to specjalnych uprawnień:

1. **Accessibility (Dostępność)** - Pozwala aplikacji na monitorowanie naciśnięć klawiszy

Uprawnienia te są wymagane tylko dla funkcji skrótów klawiaturowych - aplikacja może działać bez nich, ale skróty nie będą działać.

## Tryb bezpieczny

Jeśli masz problemy z klawiaturą, możesz uruchomić aplikację w trybie bezpiecznym (bez skrótów klawiaturowych):

```bash
HOTKEYS_ENABLED=0 uv run python main.py
```

Możesz też użyć menu aplikacji, aby wyłączyć skróty w dowolnym momencie.

## Funkcje bezpieczeństwa

Wprowadziliśmy liczne zabezpieczenia, aby skróty klawiaturowe nie powodowały problemów:

1. **Bezpieczne inicjowanie** - Jeśli skróty nie mogą być zainicjowane, aplikacja nadal działa
2. **Kontrola w menu** - Możesz włączyć/wyłączyć skróty z menu aplikacji
3. **Wizualne wskaźniki** - Ikona 🚫 pokazuje, gdy skróty są wyłączone
4. **Bezpieczne zamykanie** - Aplikacja zawsze zwalnia zasoby klawiatury przy zamykaniu
5. **Obsługa błędów** - Wewnętrzne błędy w obsłudze zdarzeń klawiatury nie blokują systemu

## Dostępne skróty klawiaturowe

Vista Scribe oferuje trzy sposoby aktywacji nagrywania:

1. **Przytrzymaj Control (⌃)** - Naciśnij i przytrzymaj klawisz Control, aby nagrywać. Zwolnij, aby zatrzymać i przetworzyć.

2. **Shift+Command+Slash (⇧⌘/)** - Naciśnij raz, aby rozpocząć nagrywanie, naciśnij ponownie, aby zatrzymać i przetworzyć.

3. **Podwójne naciśnięcie Option (⌥⌥)** - Szybko naciśnij Option dwa razy, aby przełączyć nagrywanie.

## Rozwiązywanie problemów

Jeśli masz problemy ze skrótami klawiaturowymi:

1. **Skróty nie działają w ogóle:**
   - Sprawdź, czy w menu aplikacji jest status "Hotkeys Enabled"
   - Jeśli nie, użyj opcji "Enable Hotkeys"
   - Upewnij się, że przyznano uprawnienia dostępności

2. **Klawiatura zachowuje się dziwnie:**
   - Natychmiast zamknij aplikację (Quit)
   - Uruchom ponownie w trybie bezpiecznym: `HOTKEYS_ENABLED=0 uv run python main.py`
   - Zgłoś problem

3. **Problemy po przyznaniu uprawnień:**
   - Wyłącz i włącz skróty ponownie przez menu
   - Uruchom aplikację ponownie

4. **Zawieszenie przy zamykaniu:**
   - Jeśli aplikacja nie zamyka się normalnie, użyj Terminal:
   - `pkill -f "python main.py"`

## Uwagi techniczne

- Vista Scribe używa Quartz Event Tap do monitorowania zdarzeń klawiatury
- Domyślne opóźnienie dla podwójnego naciśnięcia Option: 350 ms (konfigurowalne przez `DOUBLE_OPTION_INTERVAL_MS`)
- Obsługa zdarzeń klawiatury jest w module hotkeys.py
- Debugowanie można włączyć przez zmienną środowiskową: `HOTKEYS_DEBUG=1`