# Dependency Audit — 2025-10-01

This report covers all Python dependencies resolved via uv.lock and declared in pyproject.toml/requirements.txt.

## Overview

- Total resolved packages (uv.lock): 370
- Packages with known vulnerabilities (via OSV): 5
- Total vulnerability entries: 9

## Vulnerabilities

### future==1.0.0

- GHSA-xqrq-4mgf-ff32 — Unknown
  - Fixed in: (no fixed version listed)

### gradio==5.3.0

- GHSA-5cpq-9538-jm2j — Unknown
  - Fixed in: (no fixed version listed)
- GHSA-8jw3-6x8j-v96g — Unknown
  - Fixed in: (no fixed version listed)
- GHSA-j2jg-fq62-7c3h — Unknown
  - Fixed in: (no fixed version listed)
- GHSA-rhm9-gp5p-5248 — Unknown
  - Fixed in: (no fixed version listed)
- GHSA-wmjh-cpqj-4v6x — Unknown
  - Fixed in: (no fixed version listed)

### h11==0.14.0

- GHSA-vqfr-h8mv-ghfj — Unknown
  - Fixed in: (no fixed version listed)

### python-multipart==0.0.9

- GHSA-59g5-xgcq-4qw3 — Unknown
  - Fixed in: (no fixed version listed)

### starlette==0.41.3

- GHSA-2c2j-9gv5-cj73 — Unknown
  - Fixed in: (no fixed version listed)

## Available Updates

### Patch/Minor updates (safe to apply; run tests)

- antlr4-python3-runtime 4.9.3 → 4.13.2 (minor)
- anyio 4.9.0 → 4.11.0 (minor)
- certifi 2025.1.31 → 2025.8.3 (minor)
- cryptography 46.0.0 → 46.0.2 (patch)
- fastapi 0.115.6 → 0.118.0 (minor)
- gradio 5.3.0 → 5.47.2 (minor)
- gradio-client 1.4.2 → 1.13.3 (minor)
- h11 0.14.0 → 0.16.0 (minor)
- httpcore 1.0.8 → 1.0.9 (patch)
- jiter 0.9.0 → 0.11.0 (minor)
- multiprocess 0.70.16 → 0.70.18 (patch)
- numpy 2.2.4 → 2.3.3 (minor)
- nvidia-cublas-cu12 12.8.4.1 → 12.9.1.4 (minor)
- nvidia-cuda-cupti-cu12 12.8.90 → 12.9.79 (minor)
- nvidia-cuda-nvrtc-cu12 12.8.93 → 12.9.86 (minor)
- nvidia-cuda-runtime-cu12 12.8.90 → 12.9.79 (minor)
- nvidia-cudnn-cu12 9.10.2.21 → 9.13.1.26 (minor)
- nvidia-cufft-cu12 11.3.3.83 → 11.4.1.4 (minor)
- nvidia-cufile-cu12 1.13.1.3 → 1.14.1.1 (minor)
- nvidia-curand-cu12 10.3.9.90 → 10.3.10.19 (patch)
- nvidia-cusolver-cu12 11.7.3.90 → 11.7.5.82 (patch)
- nvidia-cusparse-cu12 12.5.8.93 → 12.5.10.65 (patch)
- nvidia-cusparselt-cu12 0.7.1 → 0.8.1 (minor)
- nvidia-nccl-cu12 2.27.3 → 2.28.3 (minor)
- nvidia-nvjitlink-cu12 12.8.93 → 12.9.86 (minor)
- nvidia-nvtx-cu12 12.8.90 → 12.9.79 (minor)
- pycparser 2.22 → 2.23 (minor)
- pydantic 2.11.3 → 2.11.9 (patch)
- pydantic-core 2.33.1 → 2.39.0 (minor)
- pyobjc 11.0 → 11.1 (minor)
- pyobjc-core 11.0 → 11.1 (minor)
- pyobjc-framework-accessibility 11.0 → 11.1 (minor)
- pyobjc-framework-accounts 11.0 → 11.1 (minor)
- pyobjc-framework-addressbook 11.0 → 11.1 (minor)
- pyobjc-framework-adservices 11.0 → 11.1 (minor)
- pyobjc-framework-adsupport 11.0 → 11.1 (minor)
- pyobjc-framework-applescriptkit 11.0 → 11.1 (minor)
- pyobjc-framework-applescriptobjc 11.0 → 11.1 (minor)
- pyobjc-framework-applicationservices 11.0 → 11.1 (minor)
- pyobjc-framework-apptrackingtransparency 11.0 → 11.1 (minor)
- pyobjc-framework-audiovideobridging 11.0 → 11.1 (minor)
- pyobjc-framework-authenticationservices 11.0 → 11.1 (minor)
- pyobjc-framework-automaticassessmentconfiguration 11.0 → 11.1 (minor)
- pyobjc-framework-automator 11.0 → 11.1 (minor)
- pyobjc-framework-avfoundation 11.0 → 11.1 (minor)
- pyobjc-framework-avkit 11.0 → 11.1 (minor)
- pyobjc-framework-avrouting 11.0 → 11.1 (minor)
- pyobjc-framework-backgroundassets 11.0 → 11.1 (minor)
- pyobjc-framework-browserenginekit 11.0 → 11.1 (minor)
- pyobjc-framework-businesschat 11.0 → 11.1 (minor)
- pyobjc-framework-calendarstore 11.0 → 11.1 (minor)
- pyobjc-framework-callkit 11.0 → 11.1 (minor)
- pyobjc-framework-carbon 11.0 → 11.1 (minor)
- pyobjc-framework-cfnetwork 11.0 → 11.1 (minor)
- pyobjc-framework-cinematic 11.0 → 11.1 (minor)
- pyobjc-framework-classkit 11.0 → 11.1 (minor)
- pyobjc-framework-cloudkit 11.0 → 11.1 (minor)
- pyobjc-framework-cocoa 11.0 → 11.1 (minor)
- pyobjc-framework-collaboration 11.0 → 11.1 (minor)
- pyobjc-framework-colorsync 11.0 → 11.1 (minor)
- pyobjc-framework-contacts 11.0 → 11.1 (minor)
- pyobjc-framework-contactsui 11.0 → 11.1 (minor)
- pyobjc-framework-coreaudio 11.0 → 11.1 (minor)
- pyobjc-framework-coreaudiokit 11.0 → 11.1 (minor)
- pyobjc-framework-corebluetooth 11.0 → 11.1 (minor)
- pyobjc-framework-coredata 11.0 → 11.1 (minor)
- pyobjc-framework-corehaptics 11.0 → 11.1 (minor)
- pyobjc-framework-corelocation 11.0 → 11.1 (minor)
- pyobjc-framework-coremedia 11.0 → 11.1 (minor)
- pyobjc-framework-coremediaio 11.0 → 11.1 (minor)
- pyobjc-framework-coremidi 11.0 → 11.1 (minor)
- pyobjc-framework-coreml 11.0 → 11.1 (minor)
- pyobjc-framework-coremotion 11.0 → 11.1 (minor)
- pyobjc-framework-coreservices 11.0 → 11.1 (minor)
- pyobjc-framework-corespotlight 11.0 → 11.1 (minor)
- pyobjc-framework-coretext 11.0 → 11.1 (minor)
- pyobjc-framework-corewlan 11.0 → 11.1 (minor)
- pyobjc-framework-cryptotokenkit 11.0 → 11.1 (minor)
- pyobjc-framework-datadetection 11.0 → 11.1 (minor)
- pyobjc-framework-devicecheck 11.0 → 11.1 (minor)
- pyobjc-framework-devicediscoveryextension 11.0 → 11.1 (minor)
- pyobjc-framework-dictionaryservices 11.0 → 11.1 (minor)
- pyobjc-framework-discrecording 11.0 → 11.1 (minor)
- pyobjc-framework-discrecordingui 11.0 → 11.1 (minor)
- pyobjc-framework-diskarbitration 11.0 → 11.1 (minor)
- pyobjc-framework-dvdplayback 11.0 → 11.1 (minor)
- pyobjc-framework-eventkit 11.0 → 11.1 (minor)
- pyobjc-framework-exceptionhandling 11.0 → 11.1 (minor)
- pyobjc-framework-executionpolicy 11.0 → 11.1 (minor)
- pyobjc-framework-extensionkit 11.0 → 11.1 (minor)
- pyobjc-framework-externalaccessory 11.0 → 11.1 (minor)
- pyobjc-framework-fileprovider 11.0 → 11.1 (minor)
- pyobjc-framework-fileproviderui 11.0 → 11.1 (minor)
- pyobjc-framework-findersync 11.0 → 11.1 (minor)
- pyobjc-framework-fsevents 11.0 → 11.1 (minor)
- pyobjc-framework-gamecenter 11.0 → 11.1 (minor)
- pyobjc-framework-gamecontroller 11.0 → 11.1 (minor)
- pyobjc-framework-gamekit 11.0 → 11.1 (minor)
- pyobjc-framework-gameplaykit 11.0 → 11.1 (minor)
- pyobjc-framework-healthkit 11.0 → 11.1 (minor)
- pyobjc-framework-imagecapturecore 11.0 → 11.1 (minor)
- pyobjc-framework-inputmethodkit 11.0 → 11.1 (minor)
- pyobjc-framework-installerplugins 11.0 → 11.1 (minor)
- pyobjc-framework-instantmessage 11.0 → 11.1 (minor)
- pyobjc-framework-intents 11.0 → 11.1 (minor)
- pyobjc-framework-intentsui 11.0 → 11.1 (minor)
- pyobjc-framework-iobluetooth 11.0 → 11.1 (minor)
- pyobjc-framework-iobluetoothui 11.0 → 11.1 (minor)
- pyobjc-framework-iosurface 11.0 → 11.1 (minor)
- pyobjc-framework-ituneslibrary 11.0 → 11.1 (minor)
- pyobjc-framework-kernelmanagement 11.0 → 11.1 (minor)
- pyobjc-framework-latentsemanticmapping 11.0 → 11.1 (minor)
- pyobjc-framework-launchservices 11.0 → 11.1 (minor)
- pyobjc-framework-libdispatch 11.0 → 11.1 (minor)
- pyobjc-framework-libxpc 11.0 → 11.1 (minor)
- pyobjc-framework-linkpresentation 11.0 → 11.1 (minor)
- pyobjc-framework-localauthentication 11.0 → 11.1 (minor)
- pyobjc-framework-localauthenticationembeddedui 11.0 → 11.1 (minor)
- pyobjc-framework-mailkit 11.0 → 11.1 (minor)
- pyobjc-framework-mapkit 11.0 → 11.1 (minor)
- pyobjc-framework-mediaaccessibility 11.0 → 11.1 (minor)
- pyobjc-framework-mediaextension 11.0 → 11.1 (minor)
- pyobjc-framework-medialibrary 11.0 → 11.1 (minor)
- pyobjc-framework-mediaplayer 11.0 → 11.1 (minor)
- pyobjc-framework-mediatoolbox 11.0 → 11.1 (minor)
- pyobjc-framework-metal 11.0 → 11.1 (minor)
- pyobjc-framework-metalfx 11.0 → 11.1 (minor)
- pyobjc-framework-metalkit 11.0 → 11.1 (minor)
- pyobjc-framework-metalperformanceshaders 11.0 → 11.1 (minor)
- pyobjc-framework-metalperformanceshadersgraph 11.0 → 11.1 (minor)
- pyobjc-framework-metrickit 11.0 → 11.1 (minor)
- pyobjc-framework-mlcompute 11.0 → 11.1 (minor)
- pyobjc-framework-modelio 11.0 → 11.1 (minor)
- pyobjc-framework-multipeerconnectivity 11.0 → 11.1 (minor)
- pyobjc-framework-naturallanguage 11.0 → 11.1 (minor)
- pyobjc-framework-netfs 11.0 → 11.1 (minor)
- pyobjc-framework-network 11.0 → 11.1 (minor)
- pyobjc-framework-networkextension 11.0 → 11.1 (minor)
- pyobjc-framework-notificationcenter 11.0 → 11.1 (minor)
- pyobjc-framework-opendirectory 11.0 → 11.1 (minor)
- pyobjc-framework-osakit 11.0 → 11.1 (minor)
- pyobjc-framework-oslog 11.0 → 11.1 (minor)
- pyobjc-framework-passkit 11.0 → 11.1 (minor)
- pyobjc-framework-pencilkit 11.0 → 11.1 (minor)
- pyobjc-framework-phase 11.0 → 11.1 (minor)
- pyobjc-framework-photos 11.0 → 11.1 (minor)
- pyobjc-framework-photosui 11.0 → 11.1 (minor)
- pyobjc-framework-preferencepanes 11.0 → 11.1 (minor)
- pyobjc-framework-pushkit 11.0 → 11.1 (minor)
- pyobjc-framework-quartz 11.0 → 11.1 (minor)
- pyobjc-framework-quicklookthumbnailing 11.0 → 11.1 (minor)
- pyobjc-framework-replaykit 11.0 → 11.1 (minor)
- pyobjc-framework-safariservices 11.0 → 11.1 (minor)
- pyobjc-framework-safetykit 11.0 → 11.1 (minor)
- pyobjc-framework-scenekit 11.0 → 11.1 (minor)
- pyobjc-framework-screencapturekit 11.0 → 11.1 (minor)
- pyobjc-framework-screensaver 11.0 → 11.1 (minor)
- pyobjc-framework-screentime 11.0 → 11.1 (minor)
- pyobjc-framework-scriptingbridge 11.0 → 11.1 (minor)
- pyobjc-framework-searchkit 11.0 → 11.1 (minor)
- pyobjc-framework-security 11.0 → 11.1 (minor)
- pyobjc-framework-securityfoundation 11.0 → 11.1 (minor)
- pyobjc-framework-securityinterface 11.0 → 11.1 (minor)
- pyobjc-framework-sensitivecontentanalysis 11.0 → 11.1 (minor)
- pyobjc-framework-servicemanagement 11.0 → 11.1 (minor)
- pyobjc-framework-sharedwithyou 11.0 → 11.1 (minor)
- pyobjc-framework-sharedwithyoucore 11.0 → 11.1 (minor)
- pyobjc-framework-shazamkit 11.0 → 11.1 (minor)
- pyobjc-framework-social 11.0 → 11.1 (minor)
- pyobjc-framework-soundanalysis 11.0 → 11.1 (minor)
- pyobjc-framework-speech 11.0 → 11.1 (minor)
- pyobjc-framework-spritekit 11.0 → 11.1 (minor)
- pyobjc-framework-storekit 11.0 → 11.1 (minor)
- pyobjc-framework-symbols 11.0 → 11.1 (minor)
- pyobjc-framework-syncservices 11.0 → 11.1 (minor)
- pyobjc-framework-systemconfiguration 11.0 → 11.1 (minor)
- pyobjc-framework-systemextensions 11.0 → 11.1 (minor)
- pyobjc-framework-threadnetwork 11.0 → 11.1 (minor)
- pyobjc-framework-uniformtypeidentifiers 11.0 → 11.1 (minor)
- pyobjc-framework-usernotifications 11.0 → 11.1 (minor)
- pyobjc-framework-usernotificationsui 11.0 → 11.1 (minor)
- pyobjc-framework-videosubscriberaccount 11.0 → 11.1 (minor)
- pyobjc-framework-videotoolbox 11.0 → 11.1 (minor)
- pyobjc-framework-virtualization 11.0 → 11.1 (minor)
- pyobjc-framework-vision 11.0 → 11.1 (minor)
- pyobjc-framework-webkit 11.0 → 11.1 (minor)
- pytest 8.3.3 → 8.4.2 (minor)
- python-dotenv 1.1.0 → 1.1.1 (patch)
- python-multipart 0.0.9 → 0.0.20 (patch)
- sounddevice 0.5.1 → 0.5.2 (patch)
- starlette 0.41.3 → 0.48.0 (minor)
- tomlkit 0.12.0 → 0.13.3 (minor)
- typing-extensions 4.13.2 → 4.15.0 (minor)
- typing-inspection 0.4.0 → 0.4.2 (patch)
- uvicorn 0.30.6 → 0.37.0 (minor)

### Major updates (batched — may include breaking changes)

- aiofiles 23.2.1 → 24.1.0 (major) — potential breaking changes; grouped for later review.
- av 14.4.0 → 15.1.0 (major) — potential breaking changes; grouped for later review.
- cffi 1.17.1 → 2.0.0 (major) — potential breaking changes; grouped for later review.
- curated-tokenizers 0.0.9 → 2.0.0 (major) — potential breaking changes; grouped for later review.
- curated-transformers 0.1.1 → 2.0.1 (major) — potential breaking changes; grouped for later review.
- markupsafe 2.1.5 → 3.0.3 (major) — potential breaking changes; grouped for later review.
- openai 1.75.0 → 2.0.0 (major) — potential breaking changes; grouped for later review.
- packaging 24.2 → 25.0 (major) — potential breaking changes; grouped for later review.
- pillow 10.4.0 → 11.3.0 (major) — potential breaking changes; grouped for later review.
- quickmachotkey 2023.11.17 → 2025.7.28 (major) — potential breaking changes; grouped for later review.
- rfc3986 1.5.0 → 2.0.0 (major) — potential breaking changes; grouped for later review.
- spacy-curated-transformers 0.3.1 → 2.1.2 (major) — potential breaking changes; grouped for later review.
- thinc 8.3.6 → 9.1.1 (major) — potential breaking changes; grouped for later review.
- websockets 12.0 → 15.0.1 (major) — potential breaking changes; grouped for later review.

## Methodology

- Dependencies collected from pyproject.toml, requirements.txt, and uv.lock (resolved).
- Vulnerabilities queried via OSV.dev (ecosystem: PyPI).
- Latest versions fetched via PyPI JSON API; pre-releases and yanked releases excluded.
- Major updates are batched due to potential breaking changes; patch/minor are safe candidates pending tests.
