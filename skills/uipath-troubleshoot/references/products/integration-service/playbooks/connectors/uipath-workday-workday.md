---
confidence: medium
---

# Workday SOAP Connector Diagnostics

Use only for connector key `uipath-workday-workday`. This is the static
SOAP/WSDL-based Workday connector. For OAuth, REST APIs, WQL, absence management,
or Invoice PDF behavior, use
[uipath-workday-workdayrest.md](./uipath-workday-workdayrest.md).

Start with the shared routing and evidence contract in
[connector.md](./connector.md).

## Context

This connector uses Workday integration system user credentials and static SOAP
resources. It does not implement OAuth, REST/WQL discovery, or Workday REST
activities.
Do not match this file on an HTTP status alone; the connector key is a required
Context precondition.

### What can cause it

- The workflow selected the Workday SOAP connector when it requires the Workday REST connector, or vice versa.
- The Workday web-services host, tenant, SOAP service version, ISU username, or password is incorrect.
- The Workday ISU lacks the domain security or business-process permission required by the SOAP operation.
- The response group, includes, excludes, object ID, page, or request envelope omits or misidentifies the required data.
- An accepted asynchronous Workday business process has not completed yet.
- The PST polling window, paging, watermark, event mapping, or dedupe logic omitted the expected event.
- The connector dropped or mis-mapped a valid Workday SOAP response or event.

## Investigation

### Fast Symptom Router

| Symptom | Connector-specific meaning | First check |
|---|---|---|
| Connection form asks for OAuth URLs/client ID | Wrong connector selected | Confirm key is not `uipath-workday-workdayrest` |
| `The WSDL should not contain anything after the domain...` | Connector validation did not find Workday server timestamp in the SOAP response | Supply only the Workday web-services host and inspect the validation response |
| `401`/SOAP authentication fault | ISU username/password, tenant, or Workday security | Test the exact SOAP service/version as the integration system user |
| SOAP service/version not found | Wrong WSDL host, tenant, service version, or enabled service | Compare constructed base URL and configured `workday.version` |
| Records are missing | Domain security, response-group/includes/excludes, or paging | Run the same SOAP request as the ISU and capture page/results metadata |
| Position lookup returns `417` and says creation is in progress | Expected asynchronous position creation | Retry the lookup after the Workday business process completes |
| Worker/supplier/position event delayed | Five-minute PST transaction-window poll | Inspect exact updated-from/through window and every result page |
| Expected REST/WQL activity is absent | Expected connector boundary | Use the Workday REST connector |

### Authentication and Connection

This connector uses Workday integration system user credentials, not OAuth.
Required inputs are:

- **WSDL URL/host**;
- **Tenant**;
- **Username**;
- **Password**.

The connector builds:

```text
https://<workday.hostname>/ccx/service/<workday.tenant>
```

It also carries a SOAP service version, defaulting to `v39.2`. Record the version
actually configured on the connection.

The WSDL field is misleadingly named: the validation hook expects the Workday
web-services domain/host rather than a complete service path. If validation cannot
find `wd:Server_Timestamp_Data` in the SOAP envelope, it returns:

```text
The WSDL should not contain anything after the domain. Please provide a valid
WSDL. Ex:- impl-services1.workday.com
```

Unblock:

1. remove `/ccx/service/...`, `?wsdl`, and other paths/query strings;
2. confirm the host belongs to the intended implementation/production tenant;
3. confirm tenant ID and ISU username/password;
4. verify the ISU can call the relevant SOAP service/version;
5. retain the underlying SOAP fault if validation still fails.

### Activities and Permissions

The connector exposes static activities/resources for workers, employees,
applicants, positions, organizations, suppliers, purchase items, pre-hire, hire,
and employee/position events. It does not perform REST/WQL object discovery.

Workday domain security is operation-specific. A successful connection validation
does not prove that the ISU can read workers, create a pre-hire, hire an employee,
manage positions, or read suppliers. Capture the SOAP fault and check the security
domain and business-process policy for the exact operation.

List operations can also apply connector response-group parameters such as
`includes` and `excludes`. If fields are missing:

1. compare the selected activity/resource and SOAP service;
2. capture final response-group/includes/excludes;
3. verify domain security for the field group;
4. inspect the raw SOAP response before activity output mapping.

### Asynchronous Position Creation

Position creation can complete asynchronously. The position-event lookup hook maps
an unfinished result to HTTP `417`:

```text
Position creation is currently in progress, and your position has not been created
yet due to its asynchronous nature. Please retry after sometime
```

This means the original create request was accepted but its Workday business
process has not produced the position yet. Retain the event ID, inspect the
Workday business process, and retry the lookup with bounded delay. Do not submit a
second create unless Workday proves the first request failed.

### Triggers

Workers, employees, positions, organizations, suppliers, and purchase items use
five-minute polling definitions. The verified source builds PST windows using
updated-from and updated-through parameters. For example, worker-family polling
queries Workday transaction-log date ranges.

For a missing event:

1. record the Workday object/reference ID and transaction/update timestamp;
2. capture the literal PST poll window;
3. run the corresponding SOAP list operation as the same ISU;
4. capture every page and response-group selection;
5. trace event classification, dedupe/watermark, and downstream execution.

### UiPath Surface Compatibility

Apply the common project-type rules from [connector.md](./connector.md). Live
`compatibleProjectTypes` and tenant feature flags are authoritative. An event wait
activity may be excluded from Agent Builder and API Workflows even when the
Integration Service trigger exists.

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then use only the
matching action-map row. If the evidence does not isolate one cause, stop at the
missing discriminator.

Resolve the smallest proven connector-specific branch: correct the WSDL host,
tenant, SOAP version, ISU security, response group, asynchronous event handling, or
poll window. Verify with the same ISU and operation before changing the connection.

### Diagnosis-to-Action Map

| Proven finding | Owner and unblock | Healing decision |
|---|---|---|
| WSDL host, tenant, SOAP version, ISU credential, or security policy is wrong | Workday connection owner/admin: correct the exact connection/security value and retest the same SOAP service | Human action; never print or replace the password |
| Response group/includes/excludes omit data needed by the workflow | Workflow developer or Workday admin: request the minimum required data and confirm domain access | Source/configuration recommendation only |
| Asynchronous position request was accepted and is still processing | Workflow owner: follow the documented event/status path using the returned business-process ID | Wait/poll according to the provider contract; do not resubmit blindly |
| SOAP response contains the data/event but the connector drops or misclassifies it | Connector team: fix envelope, paging, event, or transformation handling | Escalate with redacted SOAP and transformed evidence |
| PST poll window excludes the expected record | Workflow/connection owner: correct the proven timezone/window configuration | Do not widen or reset the window without checking duplicate risk |

### Escalation Bundle

Include the common connector evidence plus WSDL host, tenant, SOAP version,
connected ISU identity, service/operation, redacted SOAP request/fault/envelope
shape, response-group/includes/excludes, page information, and Workday business
process/event ID. For triggers include the PST window, object ID, returned pages,
watermark, emitted event, and downstream job/process ID.
