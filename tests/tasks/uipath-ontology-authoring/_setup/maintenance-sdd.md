# Solution Design Document: Equipment Maintenance

## 1. Purpose

The plant maintenance team tracks equipment, the work orders raised against it,
and the technicians who carry them out. Agents answer questions such as "which
high-priority work orders are open on line 2?" over this data.

## 2. Business concepts

| Concept | Meaning | One record per |
|---|---|---|
| Asset | A piece of plant equipment with a tag number | asset |
| Work order | A maintenance job raised against one asset | work order |
| Technician | A maintenance technician who carries out work orders | technician |

## 3. Data

### Asset (entity `Asset`)

| Field | Type | Required | Notes |
|---|---|---|---|
| assetTag | Text (up to 32 characters) | Yes | Unique tag painted on the equipment |
| assetName | Text | Yes | |
| productionLine | Text | No | Line the asset sits on, for example "Line 2" |

### Work order (entity `WorkOrder`)

| Field | Type | Required | Notes |
|---|---|---|---|
| workOrderNumber | Text (up to 20 characters) | Yes | |
| priority | One of: Low, Medium, High | Yes | Choice set `WorkOrderPriority` |
| estimatedHours | Decimal | No | |
| asset | Reference to Asset | Yes | Each work order is for exactly one asset |
| assignedTo | Reference to Technician | No | At most one technician per work order |

### Technician (entity `Technician`)

| Field | Type | Required | Notes |
|---|---|---|---|
| fullName | Text | Yes | |
| certified | Yes/No | No | Holds the plant safety certification |

## 4. Rules

- A work order's priority is always one of Low, Medium or High.
- Every work order names exactly one asset.
- "Open work orders" means work orders with no completion recorded; completion is
  out of scope for this release.

## 5. Out of scope

- Spare-parts inventory.
- Any external system: all data lives in Data Fabric.
