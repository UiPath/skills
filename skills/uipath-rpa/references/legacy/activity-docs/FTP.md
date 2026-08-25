# UiPath FTP Activities - Community Reference

## Overview
FTP/FTPS/SFTP file transfer activities. Package: `UiPath.FTP.Activities` (from Community.Activities repo).

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `WithFtpSession` | FTP connection scope (container) | Host (required), Port, Username, Password/SecurePassword, FtpsMode (None/Explicit/Implicit), SftpMode (bool), ClientCertificatePath/Password, AcceptAllCertificates, Body |
| `DownloadFiles` | Download files from FTP | RemotePath (required), LocalPath (required), Recursive, Create (create local dirs), Overwrite |
| `UploadFiles` | Upload files to FTP | LocalPath (required), RemotePath (required), Recursive, Create (create remote dirs) |
| `Delete` | Delete remote file/folder | RemotePath (required) |
| `MoveItem` | Move/rename remote file | RemotePath (required), NewPath (required) |
| `DirectoryExists` | Check if remote dir exists | RemotePath -> Exists (bool) |
| `FileExists` | Check if remote file exists | RemotePath -> Exists (bool) |
| `EnumerateObjects` | List remote directory contents | RemotePath -> Files (FtpObjectInfo[]) |

---

## WithFtpSession Properties

### Connection
- `Host` (string, required) - FTP server hostname
- `Port` (int) - Server port (default: 21 for FTP, 22 for SFTP)
- `Username` (string) - Login username
- `Password` (string) OR `SecurePassword` (SecureString) - Login password

### Protocol
- `FtpsMode` (enum): None, Explicit (FTPES), Implicit (FTPS)
- `SftpMode` (bool) - Use SFTP (SSH-based) instead of FTP
- `UseBinaryMode` (bool) - Binary vs ASCII transfer mode

### Security
- `ClientCertificatePath` (string) - Client certificate file
- `ClientCertificatePassword` (string/SecureString) - Certificate password
- `AcceptAllCertificates` (bool) - Skip certificate validation (INSECURE)

---

## Critical Gotchas

### Connection
1. **All FTP activities MUST be inside WithFtpSession** - constraint enforced
2. **FTP vs FTPS vs SFTP are different protocols** - FtpsMode controls FTP/FTPS, SftpMode switches to SFTP entirely
3. **Port defaults**: FTP=21, FTPS/Explicit=21, FTPS/Implicit=990, SFTP=22
4. **AcceptAllCertificates=true is a security risk** - bypasses SSL certificate validation

### File Operations
5. **DownloadFiles Overwrite flag** - if false, existing local files are skipped (not error)
6. **DownloadFiles/UploadFiles Recursive** - recurse into subdirectories
7. **DownloadFiles/UploadFiles Create** - create target directories if they don't exist
8. **RemotePath uses forward slashes** (/) regardless of server OS
9. **LocalPath uses system path separators**

### Transfer Mode
10. **UseBinaryMode=true recommended** for non-text files - ASCII mode can corrupt binary data
11. **ASCII mode converts line endings** between platforms (CRLF <-> LF)

### SFTP Specific
12. **SFTP uses SSH protocol** - completely different from FTP/FTPS
13. **SFTP may require SSH key authentication** (not just username/password)
14. **SFTP doesn't support FtpsMode** - setting both SftpMode=true and FtpsMode is ignored

### Error Handling
15. **ContinueOnError** inherited from base - suppresses exceptions
16. **File permission errors** common on remote servers - check server-side permissions
17. **Timeout issues** on large file transfers - ensure network stability

### Known Community Issues
18. **Passive mode vs Active mode** - some firewalls block active FTP; passive mode is default
19. **UTF-8 filename encoding** - some servers don't support UTF-8 filenames
20. **EnumerateObjects returns FtpObjectInfo[]** with Name, FullName, Type (File/Directory), Size, LastModified
