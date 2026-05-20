# UiPath Google Speech Activities - Community Reference

## Overview
Google Cloud Speech-to-Text and Text-to-Speech integration. Package: `UiPath.Google.Activities` (from Community.Activities Integrations).

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `GoogleSpeechToText` | Convert speech to text | Confidence (0-1, required), Language (required), ServiceAccountFile (required) -> Text (string) |
| `GoogleTextToSpeech` | Convert text to speech | Text (required), LanguageCode (required), Gender (Male/Female), ServiceAccountFile (required) |

---

## Critical Gotchas

1. **Google Cloud Platform service account required** - ServiceAccountFile is path to JSON key file
2. **Confidence threshold (0-1)** - lower values accept more uncertain transcriptions
3. **Language codes** in BCP-47 format (e.g., "en-US", "fr-FR", "ja-JP")
4. **GenderType enum** maps to Google's SsmlVoiceGender (Male/Female)
5. **SpeechToText uses microphone input** - has WPF SpeechControl UI element
6. **Billing required** on Google Cloud project for API access
7. **Network connectivity required** - cloud-only, no offline mode
