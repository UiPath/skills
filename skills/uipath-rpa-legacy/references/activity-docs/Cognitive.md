# UiPath Cognitive Activities - Legacy Reference

## Overview
AI/ML text analysis and translation via cloud cognitive services. Package: `UiPath.Cognitive.Activities`.

---

## Activities

| Activity | Service | Key I/O |
|----------|---------|---------|
| `GoogleTextAnalysis` | Google Cloud NLP | Text, Key -> Sentiment, Magnitude, Entities, KeyPhrases |
| `GoogleTextTranslate` | Google Translate | Text, Key, SourceLanguage, TargetLanguage -> TranslatedText |
| `MicrosoftTextAnalysis` | Azure Text Analytics | Text, Key -> Sentiment, KeyPhrases |
| `IbmWatsonTextAnalysis` | IBM Watson NLU | Text, Key -> Sentiment, Entities |
| `IbmWatsonNluTextAnalysis` | IBM Watson NLU v2 | Text, Key -> Detailed NLU analysis |
| `StanfordCoreNlpTextAnalysis` | Stanford CoreNLP | Text -> Sentiment, Entities, Components |
| `StanfordCoreNlpGetComponents` | Stanford CoreNLP | Text -> Parsed components |
| `StanfordCoreNlpGetOpenIE` | Stanford CoreNLP | Text -> Open IE triples |
| `StanfordCoreNlpGetSentenceSentiment` | Stanford CoreNLP | Text -> Per-sentence sentiment |

---

## Critical Gotchas

1. **API keys required** for each cloud service (Google, Microsoft, IBM) - not bundled
2. **Network connectivity mandatory** for all cloud services
3. **Different result structures** per provider - not normalized
4. **Legacy .NET 4.5.2 package** - consider modern AI activities for new projects
5. **Stanford CoreNLP** can run locally (no API key needed) but requires Java runtime
6. **Rate limiting** applies per cloud provider - handle 429 responses
7. **Sentiment scores range differently**: Google (-1 to 1), Azure (0 to 1), Watson (varies)
