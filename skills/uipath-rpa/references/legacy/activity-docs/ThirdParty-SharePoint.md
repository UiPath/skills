# UiPathTeam SharePoint Activities - Legacy Reference

## Overview
Community SharePoint integration (Online + On-Premises) via REST API. Package: `UiPathTeam.SharePoint.Activities`. **#14 by adoption (4.9%)**. Source: [GitHub](https://github.com/UiPath-Services/UiPathTeam.SharePoint.Activities). Community-supported (not official UiPath enterprise support).

---

## All Activities (33 total, from source code)

### SharePoint Application Scope (REQUIRED parent)
All activities must be inside this scope. Authentication container.

**Authentication Types:**
- **Online** - SharePoint Online with user credentials (Username + Password)
- **AppOnly** - Client ID + Client Secret (app-only auth, no user credentials)
- **AzureApp** - Azure App Registration to impersonate user (AzureApplicationID + AzureAppPermissions + Username + Password). SharePoint Online only.
- **WebLogin** - Browser popup for 3rd-party IdP or MFA (prompts user first run)
- **Windows** - On-prem NTLM/Kerberos (Domain + Username + Password)
- **ADFS** - On-prem Active Directory Federation Services

**Key Properties:** Url (site URL, required), AuthMode, Username, Password/SecurePassword, ClientId, ClientSecret, Domain, AzureApplicationID, QueryGrouping (batch queries)

### Library Activities (13)
| Activity | Key Arguments | Notes |
|----------|---------------|-------|
| `Upload File` | RelativeUrl (req), LocalPath (req), PropertiesToAdd (dict), AllowOperationsOnASPXFiles | Blocks ASPX upload by default |
| `Upload Large File` | RelativeUrl, LocalPath | For files >250MB |
| `Get File` (Download) | RelativeUrl (req), LocalPath | If LocalPath empty, saves to project root |
| `Create Folder` | LibraryName (req), RelativeUrl (req) | |
| `Delete` | RelativeUrl (req) | Deletes file or folder |
| `Check In File` | RelativeUrl | Version control checkin |
| `Check Out File` | RelativeUrl | Version control checkout |
| `Discard Checkout` | RelativeUrl | Cancel checkout |
| `Get Children Names` | RelativeUrl | List folder contents |
| `Move Item` | SourceUrl, DestinationUrl | Move file/folder |
| `Rename Item` | RelativeUrl, NewName | |
| `Create File` | (base class for Upload) | |

### List Activities (7)
| Activity | Key Arguments | Notes |
|----------|---------------|-------|
| `Get List Items` (ReadListItems) | ListName (req), CAMLQuery | Output: Dictionary[] OR DataTable (overload groups) |
| `Add List Item` | ListName (req), PropertiesToAdd (dict) | |
| `Update List Items` | ListName, ItemId, PropertiesToUpdate | |
| `Delete List Items` | ListName, ItemIds | |
| `Add List Item Attachments` | ListName, ItemId, FilePaths | |
| `Get List Item Attachments` | ListName, ItemId | |
| `Delete List Item Attachments` | ListName, ItemId, FileNames | |

### Permission Activities (3)
| Activity | Key Arguments | Notes |
|----------|---------------|-------|
| `Add Permission` | RelativeUrl, PrincipalId, RoleDefinition | |
| `Get Permissions` | RelativeUrl | Returns permission list |
| `Remove Permission` | RelativeUrl, PrincipalId | |

### User/Group Activities (6)
| Activity | Key Arguments | Notes |
|----------|---------------|-------|
| `Get User` | Username | Output: SharePointUser |
| `Get All Users From Group` | GroupName | Output: List\<User\> |
| `Add User To Group` | Username, GroupName | |
| `Remove User From Group` | Username, GroupName | |
| `Create Group` | GroupName, Description | |
| `Remove Group` | GroupName | |

### Utility Activities (3)
| Activity | Purpose |
|----------|---------|
| `Get TimeZone` | Get SharePoint site timezone |
| `Get Web Login User` | Get current authenticated user |
| `Sign Out` | End authentication session |

---

## Critical Gotchas (Source-Code Verified + Community Reports)

### Authentication (MAJOR ISSUES)
1. **Microsoft deprecating legacy auth** - App-Only with client secret may stop working for SharePoint Online. Consider Azure AD certificate auth or Microsoft Graph.
2. **401 Unauthorized common** - [Forum reports](https://forum.uipath.com/t/uipathteam-sharepoint-activities-sharepoint-application-scope-401-unauthorized/515006): check tenant settings, app permissions, and auth mode compatibility
3. **Windows auth failure on robots** - [Forum](https://forum.uipath.com/t/windows-authentication-failure-uipathteam-sharepoint-activities/332491): service account must have SharePoint access
4. **"Sign-in name or password does not match"** - [Forum](https://forum.uipath.com/t/uipathteam-sharepoint-activities-authentication-exception/578289): common with MFA-enabled tenants; use WebLogin or AzureApp auth instead
5. **WebLogin prompts user** on first run - not suitable for unattended robots

### QueryGrouping / Batch Queries
6. **QueryGrouping was NOT implemented** - README explicitly states this. Activities that don't support batch queries validate against this setting.
7. **Activities check parent scope** - Every activity validates it's inside SharePointApplicationScope via constraint

### CAML Queries (NOT SQL!)
8. **CAML is XML-based** - NOT SQL syntax. Example:
```xml
<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>MyDoc</Value></Eq></Where></Query></View>
```
9. **5000-item list view threshold** - SharePoint blocks queries returning >5000 items. Use indexed columns + CAML paging with `<RowLimit>` element.

### File Operations
10. **RelativeUrl is site-relative** (e.g., `/sites/MySite/Shared Documents/file.docx`) - NOT absolute URL
11. **ASPX files blocked by default** - `AllowOperationsOnASPXFiles` must be explicitly enabled
12. **Upload Large File** required for files >250MB - regular Upload File has size limit
13. **V2.0 uses REST API** (not legacy CSOM) - breaking change from v1.x

### General
14. **Community package** - no UiPath enterprise support; community forum only
15. **Url must be SITE URL** (e.g., `https://tenant.sharepoint.com/sites/MySite`) not page/library URL
16. **Get List Items returns Dictionary[] OR DataTable** - overload groups, pick one output type
