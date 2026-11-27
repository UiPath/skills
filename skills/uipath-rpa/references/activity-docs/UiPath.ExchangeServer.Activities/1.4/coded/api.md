# Exchange Server — Full API Reference

Complete API reference for the Exchange Server service. For general info see [exchange-server.md](exchange-server.md).

---

## Exchange Server Service (`IExchangeServerService`)

Accessed via the `exchangeserver` service accessor.

### ExchangeService

Creates an `IExchangeService` instance connected to an Exchange Server via PowerShell remoting.

```csharp
IExchangeService ExchangeService(IPowerShellRemoteService powerShellRemoteService);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `powerShellRemoteService` | `IPowerShellRemoteService` | Yes | PowerShell remote session to the Exchange Server |

**Returns:** `IExchangeService` — Service for performing mailbox operations.

---

## Exchange Service (`IExchangeService`)

Provides mailbox management operations. Obtained from `exchangeserver.ExchangeService(...)`.

### CreateMailbox

Creates a new mailbox on the Exchange Server.

```csharp
void CreateMailbox(
    string alias,
    string userPrincipalName,
    string mailboxDatabase,
    string addressBookPolicy,
    bool archive,
    string archiveDatabase
);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `alias` | `string` | Yes | Mailbox alias (short name used in email addresses) |
| `userPrincipalName` | `string` | Yes | User principal name (e.g., `user@domain.com`) |
| `mailboxDatabase` | `string` | Yes | Name of the mailbox database to host the mailbox |
| `addressBookPolicy` | `string` | Yes | Address book policy to assign to the mailbox |
| `archive` | `bool` | Yes | Whether to enable an archive mailbox |
| `archiveDatabase` | `string` | Yes | Name of the database for the archive mailbox (used when `archive` is `true`) |

---

### EnableMailboxArchive

Enables the archive for an existing mailbox.

```csharp
void EnableMailboxArchive(string userPrincipalName, string archiveDatabase);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `userPrincipalName` | `string` | Yes | User principal name of the mailbox owner |
| `archiveDatabase` | `string` | Yes | Name of the database to host the archive |

---

### DeleteMailbox

Deletes a mailbox from the Exchange Server.

```csharp
void DeleteMailbox(string userPrincipalName);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `userPrincipalName` | `string` | Yes | User principal name of the mailbox to delete |

---

### DisableMailboxArchive

Disables the archive for an existing mailbox.

```csharp
void DisableMailboxArchive(string userPrincipalName);
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `userPrincipalName` | `string` | Yes | User principal name of the mailbox owner |
