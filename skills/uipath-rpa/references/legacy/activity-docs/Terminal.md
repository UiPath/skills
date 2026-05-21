# UiPath Terminal Activities - Legacy Reference

## Overview
Terminal emulation for mainframe/AS400/UNIX systems. Supports 9 emulation types and 10 providers. Package: `UiPath.Terminal.Activities`.

---

## Terminal Types
| Type | Use Case |
|------|----------|
| Terminal3270 | IBM Mainframe |
| Terminal5250 | IBM AS/400 |
| TerminalVT | UNIX/VT100/VT220 |
| TerminalHP | HP Terminals |
| TerminalANSI | ANSI Standard |
| TerminalSCOANSI | SCO ANSI |
| TerminalLinux | Linux Console |
| TerminalT653X | Televideo 653X |
| TerminalWYSE | Wyse Terminals |

## Providers
| Provider | Connection Modes | Notes |
|----------|-----------------|-------|
| Attachmate Reflection | Profile + Host | Most common |
| IBM Personal Communications | Profile only | Legacy |
| Micro Focus Rumba | Profile only | |
| Rocket BlueZone | Profile + Host | |
| IBM EHLLAPI (Generic) | Low-Level only | Raw API, requires DLL |
| Attachmate EXTRA | Profile only | |
| Reflection for UNIX | Profile only | |
| Reflection for IBM | Profile + Host | |
| UiPath (New) | Host only | Current default |

---

## Activities (22 total)

### Session Management
| Activity | Key Arguments |
|----------|---------------|
| `TerminalSession` | ConnectionString (JSON), ExistingConnection, SSHUserName, SSHPassword, CloseConnection (default true) |

### Basic Screen Operations
| Activity | In/Out | Defaults |
|----------|--------|----------|
| `GetText` | -> Text (full screen) | Timeout: 5000ms, Delay: 300ms |
| `SendControlKey` | Key (enum) -> | Delay: 1000ms |
| `GetCursorPosition` | -> Row, Column (1-based) | |

### Field-Based (by Index, LabeledBy, or FollowedBy)
| Activity | In/Out |
|----------|--------|
| `GetField` | Criteria -> Text |
| `SetField` | Criteria, Text -> |
| `WaitFieldText` | Criteria, Text, MatchCase -> | Timeout: 30,000ms |
| `WaitScreenText` | Text, MatchCase -> | Timeout: 30,000ms |

### Coordinate-Based (row/column, 1-based)
| Activity | In/Out |
|----------|--------|
| `GetTextAtPosition` | Row, Col, Length -> Text |
| `GetFieldAtPosition` | Row, Col -> Text |
| `SetFieldAtPosition` | Row, Col, Text -> |
| `GetScreenArea` | Row, Col, EndRow, EndCol -> Text |
| `GetColorAtPosition` | Row, Col -> Color |
| `MoveCursor` | Row, Col -> |
| `MoveCursorToText` | Text -> Row, Col |
| `FindTextInScreen` | Text -> Row, Col |
| `WaitTextAtPosition` | Row, Col, Text -> | Timeout: 30,000ms |
| `WaitScreenReady` | -> | Timeout: 30,000ms |

### Advanced
| Activity | In/Out |
|----------|--------|
| `SendKeys` | Keys (string) -> |
| `SendKeysSecure` | SecureText (SecureString) -> |

---

## Critical Gotchas

### Session Management
1. **All activities MUST be inside TerminalSession** body - constraint enforced
2. **ConnectionString is JSON** with single quotes (apostrophes) instead of double quotes
3. **CloseConnection=true (default)** - auto-closes on exit
4. **OutputConnection** allows reusing connection across multiple TerminalSession scopes
5. **SSH support** via SSHUserName + SSHPassword (SecureString) arguments

### Coordinates
6. **1-based indexing** for all row/column coordinates (NOT 0-based)
7. **SetFieldAtPosition has BackwardsCompatible flag** - auto-detected from StackTrace for new activities

### Field Identification Priority
8. **Index takes precedence** if provided
9. **LabeledBy/FollowedBy** used only when Index not set
10. **InvalidIndex = -1**, BackwardsCompatibleIndex = -999

### Keyboard & Screen
11. **KeyboardLocked state** - WaitScreenReady throws when terminal is locked by application
12. **SendKeysSecure** unmarshals SecureString temporarily, zeros memory after use
13. **WaitMode**: NONE (no wait), READY (wait for screen ready, default), COMPLETE (wait for full idle)

### Encoding
14. **44 character encodings supported** (42 IBM EBCDIC variants + UTF-8 + ASCII)
15. **InternalEncoding** must match mainframe code page (e.g., IBM037 for US English)

### Timing
16. **Default delay 300ms** (post-action pause) - critical for terminal sync
17. **SendControlKey delay 1000ms** - higher because function keys cause screen transitions
18. **Connection timeout 50,000ms** (50 seconds)
19. **Wait timeouts 30,000ms** (30 seconds)

### COM Interop
20. **Attachmate, BlueZone, IBM providers use COM Interop** - require software installed
21. **TurboSoft (TTerm)** is the modern native provider with managed wrapper
22. **Proxy support**: Tunnel, SOCKS4, SOCKS4A, SOCKS5

### Double-Width Characters
23. **DBCS (Double-Byte Character Set)** support for Chinese/Japanese
24. **TerminalField.DoubleWidth flag** indicates DBCS field
