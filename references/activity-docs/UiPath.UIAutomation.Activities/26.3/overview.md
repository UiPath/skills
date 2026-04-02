# UiPath UI Automation Activities

`UiPath.UIAutomation.Activities`

Modern UI automation activities for desktop, web, and SAP applications.

## Documentation

- [XAML Activities Reference](activities/) - Per-activity documentation for XAML workflows
- [Coded Workflow API Reference](coded/coded-api.md) - Service API for coded C# workflows

## Activities

### UI Automation.Application

| Activity | Description |
|----------|-------------|
| [Use Application/Browser](activities/ApplicationCard.md) | Opens a desktop application or web browser page to use in your automation. |
| [Click](activities/Click.md) | Clicks a specified UI element. |
| [Type Into](activities/TypeInto.md) | Enters text in a specified UI element, for example a text box. |
| [Get Text](activities/GetText.md) | Extracts the text from a specified UI element. |
| [Select Item](activities/SelectItem.md) | Selects an item from a drop-down list. |
| [Check/Uncheck](activities/CheckUncheck.md) | Used to check, uncheck, or toggle a checkbox. |
| [Accessibility Check](activities/AccessibilityCheck.md) | Check for the accessibility issues |
| [Get Attribute](activities/GetAttribute.md) | Retrieves the value of a specified attribute of the indicated UI element. |
| [Check Element](activities/CheckElement.md) | Checks if an element is enabled or disabled. |
| [Hover](activities/Hover.md) | Hovers the mouse over a specified UI element. |
| [Highlight](activities/Highlight.md) | Visually highlights a specified UI element by surrounding it in a box. |
| [Keyboard Shortcuts](activities/KeyboardShortcuts.md) | Sends one or more keyboard shortcuts to a UI element. |
| [Check App State](activities/CheckAppState.md) | Ensures the automated app is in a specific state, by verifying if a UI element exists or not. A set of user-defined actions are executed based on the detected state. |
| [Take Screenshot](activities/TakeScreenshot.md) | Takes a screenshot of an application or UI element. |
| [Mouse Scroll](activities/MouseScroll.md) | Sends mouse scroll events to the specified UI element. |
| [Extract Table Data](activities/ExtractData.md) | Extracts tabular data from a specified web page or application. |
| [ScreenPlay](activities/UITasksWithAI.md) | Performs a given UI task, using AI, on the attached application. |
| [Window Operation](activities/WindowOperations.md) | Perform various operations on the specified window element. |
| [Element Scope](activities/ElementScope.md) | A container that enables you to attach to an existing UI element and perform multiple actions within it. |
| [Block User Input](activities/BlockUserInput.md) | Suppress keyboard/mouse input until the set key combination is pressed, or timeout exceeded. |
| [Unblock User Input](activities/UnblockUserInput.md) | Unblock keyboard/mouse input that has been previously blocked by a 'Block User Input' activity. |
| [Set Focus](activities/SetFocus.md) | Sets keyboard focus to the specified UI element. |
| [Get Clipboard](activities/GetClipboard.md) | Gets the system's Clipboard data. |
| [Set Clipboard](activities/SetClipboard.md) | Sets the system's Clipboard data to the given text. |
| [Find Elements](activities/FindElements.md) | Gets the child elements of the specified UI element |
| [For Each UI Element](activities/ForEachUiElement.md) | Iterates over a structured set of UiElements. |
| [Set Text](activities/SetText.md) | Enters text in a specified UI element, for example a text box. |
| [Drag and Drop](activities/DragAndDrop.md) | Executes a drag and drop operation from the source UI element to the destination UI element. |
| [Keypress Event Trigger](activities/KeyboardTrigger.md) | Setup a key pressed event trigger on the indicated UI Element. |
| [Click Event Trigger](activities/ClickTrigger.md) | Setup a click event trigger on the indicated UI Element. |
| [Application Event Trigger](activities/ApplicationEventTrigger.md) | Setup a trigger on a given event on the indicated UI Element. |

### UI Automation.Browser

| Activity | Description |
|----------|-------------|
| [Go To URL](activities/GoToURL.md) | Navigates to the specified URL in the indicated web browser. |
| [Navigate Browser](activities/NavigateBrowser.md) | Allows basic navigation of the browser, like Go back, Go forward, Close, Refresh, Home. |
| [Get URL](activities/GetURL.md) | Returns the URL from the current browser. |
| [Inject Js Script](activities/InjectJsScript.md) | Executes JavaScript code in the context of the web page corresponding to a UiElement. |
| [Browser Dialog Scope](activities/BrowserDialogScope.md) | Captures and handles browser dialogs such as alert, confirm and prompt. |
| [Browser File Picker Scope](activities/BrowserFilePickerScope.md) | Captures and handles a browser file picker dialog. |
| [Set Runtime Browser](activities/SetRuntimeBrowser.md) | Sets the currently active runtime browser. |
| [Get Browser Data](activities/GetBrowserData.md) | Exports the session data from the specified browser instance. |
| [Set Browser Data](activities/SetBrowserData.md) | Imports the session data into a specified browser instance. |

### UI Automation.OCR.Engine

| Activity | Description |
|----------|-------------|
| [Google Cloud Vision OCR](activities/GoogleCloudOCR.md) | Extracts a string and its information from an indicated UI element using the Google Cloud Vision OCR engine. It can be used with other OCR activities (Click OCR Text, Hover OCR Text, Double Click OCR Text, Get OCR Text, Find OCR Text Position). |
| [Tesseract OCR](activities/TesseractOCR.md) | Extracts a string and its information from an indicated UI element using Tesseract OCR Engine. It can be used with other OCR activities (Click OCR Text, Hover OCR Text, Double Click OCR Text, Get OCR Text, Find OCR Text Position). |
| [Microsoft Azure Computer Vision OCR](activities/MicrosoftAzureComputerVisionOCR.md) | Microsoft Azure Computer Vision OCR |

### UI Automation.SAP

| Activity | Description |
|----------|-------------|
| [Call Transaction](activities/SAPCallTransaction.md) | Executes a transaction code or program in the current SAP GUI window. |
| [SAP Login](activities/SAPLogin.md) | Use the activity to log into an SAP system. |
| [Read Status Bar](activities/SAPReadStatusbar.md) | Reads the message displayed in the Status Bar on the bottom of the SAP GUI window. |
| [Click Toolbar Button](activities/SAPClickToolbarButton.md) | Clicks a button from the system or application SAP toolbars. After indicating the SAP Toolbar on the screen, the list with all available buttons is displayed in the activity. |
| [Select Menu Item](activities/SAPSelectMenuItem.md) | Select a Menu Item from the main SAP GUI window. After indicating the window, the list with all available Menu Items is displayed in the activity. |
| [Expand Tree](activities/SAPExpandTree.md) | Expand parent tree to an active node or an active item. After indicating the SAP Tree element from the SAP GUI window, the Tree list with all available nodes and items is displayed in the activity. |
| [Table Cell Scope](activities/SAPTableCellScope.md) | A container that enables you to attach to an existing Table UI element and perform multiple actions within it. |
| [Click Picture on Screen](activities/SAPClickPictureOnScreen.md) | Clicks the picture displayed on a SAP GUI screen. |
| [Select Dates In Calendar](activities/SAPSelectDatesInCalendar.md) | Select Dates in Calendar. The activity can be used to select single dates or periods of time. |
| [Expand ALV Tree](activities/SAPExpandALVTree.md) | Expand parent ALV tree to the selected node. After indicating the SAP node element from the SAP GUI window, the selected node path will be displayed in the activity. |
| [Expand ALV Hierarchical Table](activities/SAPExpandALVHierarchicalTable.md) | Use the activity to identify any cell inside SAP ALV Hierarchical Table. After the identification of the cell all typical UI activities can be performed, such as Click, Double Click, Get Text and others. |
| [SAP Logon](activities/SAPLogon.md) | Use the activity to directly log on to an SAP system. Provide the exact SAP connection name from the SAP Logon or the SAP Logon Pad window used to log on to your SAP system. |

### UI Automation.Semantic

| Activity | Description |
|----------|-------------|
| [Fill Form](activities/FillFormUsingAI.md) | Uses AI to seamlessly populate the designated form with information extracted from the provided data source. |
| [Update UI Element](activities/UpdateUIElementUsingAI.md) | Uses AI to seamlessly update an UI element’s state/value. |
| [Close Popup](activities/ClosePopup.md) | Dismisses all popups that are on top of the application and block a target, using the configured close buttons. |
| [Extract Form Data](activities/ExtractFormData.md) | Uses AI to seamlessly extract form data. |
| [Extract UI Data](activities/ExtractUIData.md) | Leverages AI to facilitate the extraction of form data. |
