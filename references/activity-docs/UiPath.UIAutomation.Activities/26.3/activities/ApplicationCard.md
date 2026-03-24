# Use Application/Browser

`UiPath.UIAutomationNext.Activities.NApplicationCard`

Opens a desktop application or web browser page to use in your automation.

**Package:** `UiPath.UIAutomation.Activities`
**Category:** UI Automation.Application

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `TargetApp` | Target application | Property | [`TargetApp`](common/Target.md#targetapp) |  |  |  | Expand for more options. |
| `OpenMode` | Open | InArgument | `NAppOpenMode` |  |  |  | Defines whether to open the target application before executing the activities in it. |
| `CloseMode` | Close | InArgument | `NAppCloseMode` |  |  |  | Defines whether to close the target application after executing the activities in it. The default value is same as 'If opened by Use App/Browser'. |
| `UserDataFolderMode` | User data folder mode | InArgument | `BrowserUserDataFolderMode` |  |  |  | The user data folder mode you want to set. It is used for starting the browser with a specific user data folder. |
| `UserDataFolderPath` | User data folder path | InArgument | `string` |  |  |  | The user data folder that the browser will use. Defaults to "%localappdata%\UiPath\PIP Browser Profiles\BrowserType" if not set. |
| `IsIncognito` | Incognito/private window | InArgument | `bool` |  |  |  | Opens the new browser session in Incognito/private mode. |
| `WebDriverMode` | Browser automation mode | InArgument | `NWebDriverMode` |  |  |  | Specifies the automation method used when opening a new browser session. |
| `HealingAgentBehavior` | Healing Agent mode | InArgument | `NHealingAgentBehavior` |  |  |  | Configures the Healing Agent actions if they are allowed by Governance or Orchestrator process/job/trigger level settings |
| `InUiElement` | Input element | InArgument | `UiElement` |  |  |  | The Input UI Element defines the screen element that the activity will be executed on. |
| `FilePath` | File path | InArgument | `string` |  |  |  | The full path to the executable file that starts the application. Property is used only when opening a new application instance. |
| `Arguments` | Arguments | InArgument | `string` |  |  |  | Parameters to pass to the target application at startup. Property is used only when opening a new application or browser instance. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InteractionMode` | Input mode | `NInteractionMode` | `Constants.DefaultInteractionMode` | The method used to generate keyboard and mouse input. |
| `AttachMode` | Window attach mode | `NAppAttachMode` | `NAppAttachMode.ByInstance` | Defines where inner activities search for their target elements. |
| `WindowResize` | Resize window | `NWindowResize` | `NWindowResize.None` | Defines whether the application/browser is resized when initialized. |
| `DialogHandling` | Dialog Handling | `DialogHandling` |  | Configure auto-dismissal of JavaScript dialogs. |
| `IsExactTitleEnabled` | Match exact title | `bool` |  | When ON, only apps that exactly match the current app title will be used in the automation. When OFF, the window with the closest matching title will be used in the automation. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutUiElement` | Output element | `UiElement` | Output a UI Element to use in other activities as an Input UI Element. |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` |  | Continue executing the activities in the automation if this activity fails. The default value is False. |
| `Timeout` | Timeout | InArgument | `double` |  | The amount of time (in seconds) to wait for the operation to be performed before generating an error. The default value is 30 seconds. |

## Sub-Objects

### DialogHandling

Configure auto-dismissal of JavaScript dialogs.

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `DismissAlerts` | Dismiss Alerts | InArgument | `bool` |  | Enable auto-dismissal of JavaScript alert dialogs. |
| `DismissConfirms` | Dismiss Confirms | InArgument | `bool` |  | Enable auto-dismissal of JavaScript confirm dialogs. |
| `DismissPrompts` | Dismiss Prompts | InArgument | `bool` |  | Enable auto-dismissal of JavaScript prompt dialogs. |
| `ConfirmDialogResponse` | Confirm dialog response | InArgument | `NBrowserDialogResponse` |  | Response to the JavaScript confirm dialogs. |
| `PromptDialogResponse` | Prompt dialog response | InArgument | `NBrowserDialogResponse` |  | Response to the JavaScript prompt dialog. |
| `PromptDialogResponseText` | Prompt response text | InArgument | `string` |  | Text response for for JavaScript prompt dialogs. |

**XAML nested element syntax:**

```xml
<uix:NApplicationCard.DialogHandling>
  <uix:DialogHandling
      DismissAlerts="{x:Null}"
      DismissConfirms="{x:Null}"
      DismissPrompts="{x:Null}"
      ConfirmDialogResponse="{x:Null}"
      PromptDialogResponse="{x:Null}"
      PromptDialogResponseText="{x:Null}" />
</uix:NApplicationCard.DialogHandling>
```

## XAML Example

Child activities must be placed inside the `Body > ActivityAction > Sequence` structure. The `OCREngine` and `TargetApp` sub-objects are also required.

```xml
<uix:NApplicationCard
    xmlns:uix="http://schemas.uipath.com/workflow/activities/uix"
    xmlns:sd="clr-namespace:System.Drawing;assembly=System.Drawing.Common"
    xmlns:sd1="clr-namespace:System.Drawing;assembly=System.Drawing.Primitives"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
    AttachMode="ByInstance"
    DisplayName="Use Application/Browser"
    HealingAgentBehavior="Job"
    Version="V2">
  <uix:NApplicationCard.Body>
    <ActivityAction x:TypeArguments="x:Object">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:Object" Name="WSSessionData" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- Child activities (Click, Type Into, Get Text, etc.) go here -->
      </Sequence>
    </ActivityAction>
  </uix:NApplicationCard.Body>
  <uix:NApplicationCard.OCREngine>
    <ActivityFunc x:TypeArguments="sd:Image, scg:IEnumerable(scg:KeyValuePair(sd1:Rectangle, x:String))">
      <ActivityFunc.Argument>
        <DelegateInArgument x:TypeArguments="sd:Image" Name="Image" />
      </ActivityFunc.Argument>
    </ActivityFunc>
  </uix:NApplicationCard.OCREngine>
  <uix:NApplicationCard.TargetApp>
    <uix:TargetApp
        Selector="&lt;wnd app='myapp.exe' title='My App' /&gt;"
        Version="V2" />
  </uix:NApplicationCard.TargetApp>
</uix:NApplicationCard>
```

## Notes

- This activity is a scope/container activity. Child activities must be placed inside `Body > ActivityAction > Sequence`.
- The `Body` property wraps child activities in an `ActivityAction<object>` with a `DelegateInArgument` named `WSSessionData`.
- The `OCREngine` `ActivityFunc` is required even if OCR is not used — omitting it causes validation errors.
- The `Version` attribute is mandatory and must be set to `V2`.
- Assembly: `UiPath.UIAutomationNext.Activities`
