#!/usr/bin/env bash
# run_transcription.sh - Skrypt do uruchomienia backendu vista-scribe i wykonania transkrypcji
# Użycie: ./run_transcription.sh [ścieżka/do/pliku/audio.mp3]

set -euo pipefail

# Kolory dla lepszej czytelności
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Ustaw katalog repozytorium
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"

# Funkcja normalizująca ścieżki /Users na /users
lower_users() {
  local p="$1"
  if [[ "$p" == /Users/* ]]; then
    local fixed="/users/${p#*/Users/}"
    if [[ -e "$fixed" ]]; then
      echo "$fixed"; return
    fi
  fi
  echo "$p"
}

# Funkcja czekająca na uruchomienie backendu
wait_for_backend() {
  local max_attempts=20
  local attempt=1
  echo -e "${YELLOW}[*] Czekam na uruchomienie backendu...${NC}"
  
  while [ $attempt -le $max_attempts ]; do
    if curl -s "http://127.0.0.1:8237/healthz" | grep -q '"ok":true'; then
      echo -e "${GREEN}[✓] Backend działa!${NC}"
      return 0
    fi
    echo -n "."
    sleep 1
    ((attempt++))
  done
  
  echo -e "\n${RED}[!] Nie udało się połączyć z backendem po $max_attempts próbach.${NC}"
  echo -e "${YELLOW}[*] Sprawdź logi w: $LOG_DIR/backend.err.log${NC}"
  return 1
}

# Sprawdź czy uv jest zainstalowane
if ! command -v uv >/dev/null 2>&1; then
  echo -e "${RED}[!] Nie znaleziono 'uv'. Zainstaluj i uruchom ponownie powłokę:${NC}"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "  exec -l \$SHELL"
  exit 1
fi

echo -e "${BLUE}==> Synchronizuję środowisko (uv sync)...${NC}"
cd "$REPO_DIR"
uv sync

# Określ ścieżki modeli
WHISPER_VARIANT="${WHISPER_VARIANT:-large-v3-turbo}"
FORMAT_ENABLED="${FORMAT_ENABLED:-1}"
MODEL_DIR="$REPO_DIR/models"

# Automatyczne wykrywanie Whisper
if [[ -d "$MODEL_DIR/whisper-$WHISPER_VARIANT" ]]; then
  WHISPER_DIR="$MODEL_DIR/whisper-$WHISPER_VARIANT"
else
  # fallback do large lub medium
  if [[ -d "$MODEL_DIR/whisper-large-v3-turbo" ]]; then
    WHISPER_DIR="$MODEL_DIR/whisper-large-v3-turbo"
    WHISPER_VARIANT="large-v3-turbo"
  elif [[ -d "$MODEL_DIR/whisper-medium" ]]; then
    WHISPER_DIR="$MODEL_DIR/whisper-medium"
    WHISPER_VARIANT="medium"
  else
    echo -e "${RED}[!] Nie znaleziono modelu Whisper. Zainstaluj go najpierw:${NC}"
    echo "uv run python scripts/get_models.py --whisper large-v3-turbo"
    exit 1
  fi
fi

# Normalizacja ścieżki dla MLX
WHISPER_DIR="$(lower_users "$WHISPER_DIR")"
echo -e "${GREEN}[✓] Znaleziono model Whisper: $WHISPER_DIR${NC}"

# Wykryj model LLM jeśli FORMAT_ENABLED=1
LLM_ID="${LLM_ID:-}"
if [[ "$FORMAT_ENABLED" == "1" && -z "$LLM_ID" ]]; then
  # Sprawdź domyślny model Bielik-4.5B
  if [[ -d "$MODEL_DIR/bielik-4.5b-mxfp4-mlx" ]]; then
    LLM_ID="$MODEL_DIR/bielik-4.5b-mxfp4-mlx"
  else
    # Szukaj innych modeli MLX-LM
    for d in "$MODEL_DIR"/*; do
      if [[ -d "$d" && "$(basename "$d")" != whisper-* ]]; then
        if [[ -f "$d/tokenizer.json" || -f "$d/config.json" ]]; then
          LLM_ID="$d"
          break
        fi
      fi
    done
  fi
  
  if [[ -n "$LLM_ID" ]]; then
    LLM_ID="$(lower_users "$LLM_ID")"
    echo -e "${GREEN}[✓] Znaleziono model LLM: $LLM_ID${NC}"
  else
    echo -e "${YELLOW}[!] Nie znaleziono modelu LLM. Formatowanie będzie wyłączone.${NC}"
    FORMAT_ENABLED="0"
  fi
fi

# Uruchom backend w tle
echo -e "${BLUE}==> Uruchamiam backend vista-scribe w tle...${NC}"

# Sprawdź czy port 8237 jest wolny
if lsof -i:8237 -sTCP:LISTEN -t &>/dev/null; then
  echo -e "${YELLOW}[*] Backend już działa na porcie 8237. Pomijam uruchamianie.${NC}"
else
  # Uruchom backend w tle
  export_vars="WHISPER_DIR=\"$WHISPER_DIR\" FORMAT_ENABLED=\"$FORMAT_ENABLED\" HOST=\"127.0.0.1\" PORT=\"8237\""
  if [[ -n "$LLM_ID" ]]; then
    export_vars="$export_vars LLM_ID=\"$LLM_ID\""
  fi

  echo -e "${YELLOW}[*] Uruchamiam backend: $export_vars uv run python backend.py${NC}"
  
  # Uruchom backend i przekieruj logi
  eval "nohup $export_vars uv run python backend.py > \"$LOG_DIR/backend.out.log\" 2> \"$LOG_DIR/backend.err.log\" &"
  BACKEND_PID=$!
  echo -e "${GREEN}[✓] Backend uruchomiony jako PID: $BACKEND_PID${NC}"
  
  # Poczekaj na uruchomienie backendu
  wait_for_backend || exit 1
fi

# Sprawdź healthcheck
echo -e "${BLUE}==> Sprawdzam status backendu...${NC}"
HEALTH_RESULT=$(curl -s http://127.0.0.1:8237/healthz)
echo -e "${GREEN}[✓] Status backendu: $HEALTH_RESULT${NC}"

# Utwórz plik testowy jeśli nie podano ścieżki
INPUT_FILE="${1:-}"

if [[ -z "$INPUT_FILE" ]]; then
  echo -e "${BLUE}==> Nie podano pliku audio. Szukam przykładowego pliku...${NC}"
  
  # Sprawdź czy istnieje katalog przykładowych plików
  if [[ -d "$REPO_DIR/tests/audio" ]]; then
    # Użyj przykładowego pliku z katalogu testów
    for audio_file in "$REPO_DIR"/tests/audio/*.{mp3,wav,m4a}; do
      if [[ -f "$audio_file" ]]; then
        INPUT_FILE="$audio_file"
        break
      fi
    done
  fi
  
  # Jeśli nadal nie mamy pliku, spróbuj użyć message-from-user.m4a
  if [[ -z "$INPUT_FILE" ]]; then
    for possible_path in "/Users/maciejgad/Library/Containers/com.apple.VoiceMemos/Data/tmp/.com.apple.uikit.itemprovider.temporary."*"/message-from-user.m4a"; do
      if [[ -f "$possible_path" ]]; then
        INPUT_FILE="$possible_path"
        echo -e "${GREEN}[✓] Znaleziono plik głosowy: $INPUT_FILE${NC}"
        break
      fi
    done
  fi
  
  # Jeśli nadal nie mamy pliku, zaproponuj nagranie z mikrofonu
  if [[ -z "$INPUT_FILE" ]]; then
    echo -e "${YELLOW}[!] Nie znaleziono przykładowego pliku audio.${NC}"
    echo -e "${YELLOW}[*] Możesz:"
    echo -e " 1) Uruchomić skrypt z konkretnym plikiem: ./run_transcription.sh /ścieżka/do/pliku.m4a"
    echo -e " 2) Nagrać audio bezpośrednio z mikrofonu.${NC}"
    
    # Zapytaj użytkownika, czy chce nagrać audio
    echo -e "${BLUE}Czy chcesz nagrać audio bezpośrednio z mikrofonu? (t/n)${NC}"
    read -r answer
    
    if [[ "$answer" == "t" || "$answer" == "T" || "$answer" == "tak" ]]; then
      echo -e "${BLUE}==> Uruchamiam nagrywanie z mikrofonu...${NC}"
      # Użyj tych samych zmiennych środowiskowych co dla backendu
      FORMAT_OPT=""
      if [[ "$FORMAT_ENABLED" == "0" ]]; then
        FORMAT_OPT="--no-format"
      fi
      # Uruchom przez uv, aby mieć dostęp do wszystkich zależności
      WHISPER_DIR="$WHISPER_DIR" FORMAT_ENABLED="$FORMAT_ENABLED" \
        ${LLM_ID:+LLM_ID="$LLM_ID"} uv run python record_and_transcribe.py $FORMAT_OPT
      exit $?
    else
      echo -e "${YELLOW}[*] Aby transkrybować plik audio, uruchom skrypt ponownie z jego ścieżką:${NC}"
      echo "./run_transcription.sh /ścieżka/do/pliku.m4a"
      exit 1
    fi
  fi
fi

# Normalizuj ścieżkę pliku audio
INPUT_FILE="$(lower_users "$INPUT_FILE")"
echo -e "${BLUE}==> Transkrybuję plik: $INPUT_FILE${NC}"

# Sprawdź czy plik istnieje
if [[ ! -f "$INPUT_FILE" ]]; then
  echo -e "${RED}[!] Plik $INPUT_FILE nie istnieje!${NC}"
  exit 1
fi

# Wyślij plik do transkrypcji
if [[ "$FORMAT_ENABLED" == "1" ]]; then
  echo -e "${BLUE}==> Wysyłam plik do transkrypcji i formatowania...${NC}"
  RESULT=$(curl -s -F "audio=@$INPUT_FILE" http://127.0.0.1:8237/stt_and_format)
else
  echo -e "${BLUE}==> Wysyłam plik do transkrypcji (bez formatowania)...${NC}"
  RESULT=$(curl -s -F "audio=@$INPUT_FILE" http://127.0.0.1:8237/transcribe)
fi

# Wyodrębnij tekst z odpowiedzi JSON
TEXT=$(echo "$RESULT" | python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('text', 'Błąd podczas transkrypcji'))")

echo -e "${GREEN}==> WYNIK TRANSKRYPCJI:${NC}"
echo -e "${BLUE}$TEXT${NC}"

# Zapisz transkrypcję do pliku
OUTPUT_FILE="${INPUT_FILE}.transkrypcja.txt"
echo "$TEXT" > "$OUTPUT_FILE"
echo -e "${GREEN}[✓] Transkrypcja zapisana do: $OUTPUT_FILE${NC}"

echo -e "${GREEN}==> Gotowe. Backend nadal działa w tle na PID: $BACKEND_PID${NC}"
echo -e "${YELLOW}[*] Aby zatrzymać backend: kill $BACKEND_PID${NC}"
echo -e "${YELLOW}[*] Aby zweryfikować działanie: curl -s http://127.0.0.1:8237/healthz${NC}"