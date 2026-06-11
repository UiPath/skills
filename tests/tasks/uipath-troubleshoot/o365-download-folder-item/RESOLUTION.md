**Root Cause:** The Download File activity (legacy `DownloadFile`) in `O365_DownloadConversion.xaml` was given a OneDrive **folder** as its DriveItem input. The activity only downloads files and rejects folders by design with `Office365Exception: Folders cannot be downloaded with this activity. Please input a different DriveItem.`

**What went wrong:** The last job in folder Shared — process **ERN_O365_DownloadConversion** (job 64580780-4aa1-4ec2-b5f2-abd5439ea200, started 2026-06-10 19:09:03 UTC, machine MOCK-HOST) — faulted 6 seconds in when Download File threw on a folder input.

**Why:** Inside the Microsoft 365 Scope, the upstream activity "Find a folder by name" (`FindFilesAndFolders`, Query = `Documents`) stored the OneDrive folder 'Documents' in variable `foundFolder`; "Download File on a folder item" (`DownloadFile`) was invoked with `File = foundFolder`, `LocalFilePath = C:\Temp`. A folder was bound where a file is required — the folder-input cause branch of the download playbook. The scope and the find activity completed normally; this is the originating error. Stack ends in `UiPath.MicrosoftOffice365.Activities.Files.DownloadFile.ExecuteAsync`.

**Immediate fix:** Point Download File at a file DriveItem; to download a folder's contents, iterate with For Each File/Folder and download per file. Source: `references/activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md` § Resolution branch 1.

**Preventive fix:** Guard the download — branch on whether the found DriveItem is a file before calling Download File, or query files only.
