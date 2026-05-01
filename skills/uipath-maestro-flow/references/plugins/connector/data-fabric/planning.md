# Data Fabric Activity Nodes — Planning

Data Fabric connector nodes (`uipath-uipath-dataservice`) give a Flow direct read/write access to UiPath Data Fabric entities via an Integration Service connection.

## Activity Selection

| User says | Activity | Node type suffix |
|---|---|---|
| "query" / "list" / "search" / "find records" | Query Entity Records | `query-entity-records` |
| "create" / "insert" / "add a record" | Create Entity Record | `create-entity-record` |
| "update" / "modify" / "edit field" | Update Entity Record | `update-entity-record` |
| "delete" / "remove" | Delete Entity Record | `delete-entity-record` |
| "get by id" / "fetch one record" | Get Entity Record by ID | `get-entity-record-by-id` |

"Get all records matching X" → Query. "Get the record with ID Y" → Get by ID.

## Pre-Build Checklist

**1. Entity name** — `uip df entities list --native-only`. Use the exact CamelCase `Name` (e.g. `BankDetails`). For Create/Update, also `uip df entities get <entity-ID>` for field names — skip system fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`).

**2. Connection** — `uip is connections list`, filter `ConnectorKey = "uipath-uipath-dataservice"` and `State = "Enabled"`. Capture `Id` (→ `connectionId`), `FolderKey`, and `Name` (→ binding name). No connection found → stop: *"Create a Data Fabric connection in Integration Service first."* See [connector/impl.md](../impl.md).

**3. Project name** — use what the user specifies; suggest `<EntityName>Flow` if they don't provide one.

## Activity Parameter Defaults

| Activity | Defaults |
|---|---|
| Query Entity Records | `start=0`, `limit=100`, `expansionLevel="3"`, `isAscending=false` |
| Create / Update / GetById | `expansionLevel="3"` |
| Delete | _(none)_ |

No body fields provided for Create → ask the user (field names are entity-specific). `expansionLevel` is always a **string** `"3"`, not a number.

**Paging:** To retrieve more than `limit=100` records, increment `start` by `limit` on each pass (e.g. `start=0`, then `start=100`, etc.) and repeat the Query node until the result count is less than `limit`. Use a Script node to accumulate results across pages.

## CEQL Filter Reference

Add `"queryExpression": "<filter>"` to `queryParameters` on a Query node. For CEQL operator syntax and filter tree structure see [uipath-platform — Filter Trees (CEQL)](../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

| Pattern | Example |
|---|---|
| Equality | `AccountNumber = '788'` |
| Numeric compare | `Amount > 1000` |
| AND / OR | `BankName = 'HDFC' AND IsActive = true` |
| Date range | `CreateTime >= '2025-01-01' AND CreateTime <= '2025-12-31'` |
| Contains | `AccountHolderName LIKE '%Kumar%'` |
| NULL check | `BankName IS NULL` |

