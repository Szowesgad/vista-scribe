# vista-scribe-Py Development Checklist

## Usage Instructions

- Use "- [ ]" for uncompleted tasks
- Use "- [x]" for completed tasks
- Only mark tasks as complete when they are fully tested and verified
- Each major component should be tested with the user before proceeding
- Update this checklist as new requirements or tasks are discovered

## Development Checklist

### Initial Setup

- [x] Create checklist.md
- [x] Initialize project structure
  - [x] Create main project directory
  - [x] Create all required subdirectories (packaging/, tests/)
- [x] Create and document core files
  - [x] Create all primary Python files
  - [x] Add detailed header documentation to each file:
    - [x] main.py - App entry point and state machine
    - [x] hotkeys.py - Hotkey detection and event handling
    - [x] audio.py - Audio recording and silence detection
    - [x] stt.py - Speech-to-text integration
    - [x] llm.py - Text formatting with GPT
    - [x] ui.py - Menu bar and clipboard management
  - [x] Header documentation must include:
    - [x] File purpose and role
    - [x] Dependencies on other project files
    - [x] Key classes and functions
    - [x] Design decisions and rationale
    - [x] Usage examples where applicable
- [x] Set up Python environment
  - [x] Install Python via brew
  - [x] Create virtual environment
  - [x] Activate virtual environment
  - [x] Upgrade pip
- [x] Install dependencies
  - [x] Install all required packages
  - [x] Create requirements.txt
- [x] Environment Configuration
  - [x] Create .env file
  - [x] Add .env to .gitignore
  - [x] Set up OpenAI API key configuration
- [x] 👤 USER CHECKPOINT: Verify environment setup is complete

### Core Modules Development

- [x] Implement hotkeys.py
  - [x] Create basic structure
  - [x] Implement event tap
  - [ ] Test key detection
  - [ ] 👤 USER CHECKPOINT: Test hotkey detection
- [x] Implement audio.py
  - [x] Create Recorder class
  - [x] Implement audio capture
  - [x] Add silence detection
  - [x] Test audio saving
  - [x] 👤 USER CHECKPOINT: Test audio recording
- [x] Implement stt.py
  - [x] Set up OpenAI client
  - [x] Implement transcription function
  - [x] 👤 USER CHECKPOINT: Test transcription with sample audio
- [x] Implement llm.py
  - [x] Set up GPT-4o-mini integration
  - [x] Implement text formatting
  - [x] 👤 USER CHECKPOINT: Test text formatting
- [x] Implement ui.py
  - [x] Create MenuIcon class
  - [x] Implement status updates
  - [x] Add clipboard/paste functionality
  - [x] 👤 USER CHECKPOINT: Test UI elements

### Main Application

- [x] Implement main.py
  - [x] Create vista-scribe class
  - [x] Implement state machine
  - [x] Add event handling
  - [x] Integrate all modules
  - [x] 👤 USER CHECKPOINT: Test basic app functionality

### Integration Testing

- [ ] Manual Testing Phase
  - [ ] Test hold-to-record
  - [ ] Test toggle recording
  - [ ] Test transcription flow
  - [ ] Test formatting
  - [ ] Test paste functionality
  - [ ] 👤 USER CHECKPOINT: Full flow testing

### Packaging

- [x] Create packaging files
  - [x] Create setup.py
  - [x] Create LaunchAgent plist
- [x] Build .app bundle
  - [x] Test build process
  - [ ] Verify app bundle
  - [ ] 👤 USER CHECKPOINT: Test installed application

### System Integration

- [ ] Set up permissions
  - [ ] Test Microphone access
  - [ ] Test Input Monitoring
  - [ ] Test Accessibility
  - [ ] 👤 USER CHECKPOINT: Verify all permissions
- [ ] Configure auto-start
  - [ ] Install LaunchAgent
  - [ ] Test startup behavior
  - [ ] 👤 USER CHECKPOINT: Verify auto-start

### Documentation and Polish

- [x] Complete documentation
  - [x] Update README.md (local-first, backend, Quick Action, Tray icon, Ruff)
  - [x] Add inline documentation where needed
  - [x] Document setup process and one-click scripts
- [ ] Final testing
  - [ ] Perform end-to-end testing
  - [ ] 👤 USER CHECKPOINT: Final review and sign-off

### Quality & CI

- [x] Add Ruff config (pyproject.toml)
- [x] Add CI pipeline for Ruff (.github/workflows/lint.yml)
- [ ] Consider adding unit-test workflow (pytest) on macOS

### Future Improvements

- [ ] Track potential improvements here
- [ ] Add user-requested features
