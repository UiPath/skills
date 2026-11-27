# UiPath Mobile Automation Activities - Legacy Reference

## Overview
Mobile device automation for iOS/Android via Appium server. Package: `UiPath.MobileAutomation.Activities`.

---

## Key Components

| Component | Purpose |
|-----------|---------|
| `MobileService` | Runtime service managing connections |
| `Device` / `DeviceBuilder` | Target mobile device configuration |
| `Application` / `ApplicationBuilder` | App to automate |
| `Connection` | Connection settings (Appium URL, capabilities) |
| `MobileTarget` / `SelectorTarget` | UI element selector types |

## Connection Methods
- `ConnectAsync(Device, Application, ConnectOptions)`
- `GetDevices()` / `GetApplications()`

---

## Critical Gotchas

1. **Requires running Appium server** (local or cloud like SauceLabs/BrowserStack)
2. **Device farm credentials needed** for cloud-hosted devices
3. **Selector creation complex** for cross-platform (iOS vs Android selectors differ)
4. **Live Run requires MDM** (Mobile Device Manager) process running
5. **Design-time only shows in MDM** - headless at runtime
6. **Hybrid web/native apps** require switching context (internal Driver scripts)
7. **IPC communication** for MDM integration
8. **Session timeouts** vary by cloud provider - keep-alive may be needed
9. **Screen resolution differences** affect coordinate-based actions
10. **iOS requires XCUITest driver**, Android requires UIAutomator2/Espresso
