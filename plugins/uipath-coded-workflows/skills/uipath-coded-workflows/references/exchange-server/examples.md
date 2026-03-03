# Exchange Server Examples

Examples using the `exchangeserver` service from `UiPath.ExchangeServer.Activities` package.

**Required package:** `"UiPath.ExchangeServer.Activities": "[1.0.0]"`

---

## Create a Mailbox with Archive

```csharp
namespace MyProject
{
    public class CreateMailboxWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(IPowerShellRemoteService powerShellRemoteService)
        {
            var exchangeService = exchangeserver.ExchangeService(powerShellRemoteService);

            // Create a new mailbox with archive enabled
            exchangeService.CreateMailbox(
                alias: "jdoe",
                userPrincipalName: "john.doe@contoso.com",
                mailboxDatabase: "MailboxDB01",
                addressBookPolicy: "Default Global Address List",
                archive: true,
                archiveDatabase: "ArchiveDB01");

            Log("Mailbox created for john.doe@contoso.com with archive enabled");
        }
    }
}
```

## Create a Mailbox without Archive

```csharp
namespace MyProject
{
    public class CreateMailboxNoArchiveWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(IPowerShellRemoteService powerShellRemoteService)
        {
            var exchangeService = exchangeserver.ExchangeService(powerShellRemoteService);

            // Create a mailbox without archive
            exchangeService.CreateMailbox(
                alias: "asmith",
                userPrincipalName: "alice.smith@contoso.com",
                mailboxDatabase: "MailboxDB02",
                addressBookPolicy: "Default Global Address List",
                archive: false,
                archiveDatabase: null);

            Log("Mailbox created for alice.smith@contoso.com");
        }
    }
}
```

## Enable Archive on an Existing Mailbox

```csharp
namespace MyProject
{
    public class EnableArchiveWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(IPowerShellRemoteService powerShellRemoteService)
        {
            var exchangeService = exchangeserver.ExchangeService(powerShellRemoteService);

            // Enable archive for an existing mailbox
            exchangeService.EnableMailboxArchive(
                userPrincipalName: "alice.smith@contoso.com",
                archiveDatabase: "ArchiveDB01");

            Log("Archive enabled for alice.smith@contoso.com");
        }
    }
}
```

## Disable Mailbox Archive

```csharp
namespace MyProject
{
    public class DisableArchiveWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(IPowerShellRemoteService powerShellRemoteService)
        {
            var exchangeService = exchangeserver.ExchangeService(powerShellRemoteService);

            // Disable archive for a mailbox
            exchangeService.DisableMailboxArchive(
                userPrincipalName: "alice.smith@contoso.com");

            Log("Archive disabled for alice.smith@contoso.com");
        }
    }
}
```

## Delete a Mailbox

```csharp
namespace MyProject
{
    public class DeleteMailboxWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(IPowerShellRemoteService powerShellRemoteService)
        {
            var exchangeService = exchangeserver.ExchangeService(powerShellRemoteService);

            // Delete a mailbox
            exchangeService.DeleteMailbox(
                userPrincipalName: "john.doe@contoso.com");

            Log("Mailbox deleted for john.doe@contoso.com");
        }
    }
}
```

## Batch Mailbox Provisioning

```csharp
using System.Data;

namespace MyProject
{
    public class BatchProvisionWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(
            IPowerShellRemoteService powerShellRemoteService,
            DataTable usersTable)
        {
            var exchangeService = exchangeserver.ExchangeService(powerShellRemoteService);

            // Iterate over a DataTable of users to provision mailboxes
            foreach (DataRow row in usersTable.Rows)
            {
                string alias = row["Alias"].ToString();
                string upn = row["UserPrincipalName"].ToString();
                string database = row["MailboxDatabase"].ToString();
                bool enableArchive = Convert.ToBoolean(row["EnableArchive"]);
                string archiveDb = row["ArchiveDatabase"]?.ToString();

                exchangeService.CreateMailbox(
                    alias: alias,
                    userPrincipalName: upn,
                    mailboxDatabase: database,
                    addressBookPolicy: "Default Global Address List",
                    archive: enableArchive,
                    archiveDatabase: archiveDb);

                Log($"Provisioned mailbox for {upn}");
            }

            Log($"Batch provisioning complete: {usersTable.Rows.Count} mailboxes created");
        }
    }
}
```
