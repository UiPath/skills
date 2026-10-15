<!-- pdd:doc header="Automated Network Fault Detection and Remediation {{RUN_TOKEN}} | Process Definition Document" footer="Confidential | VastNet Communications" client="VastNet Communications" author="VastNet Communications — Process Automation Team" date="29 September 2026" version="1.0" process="Automated Network Fault Detection and Remediation {{RUN_TOKEN}}" -->

# Automated Network Fault Detection and Remediation {{RUN_TOKEN}}


<!-- pdd:section id=business-context sources=as-is/overview.md,as-is/pain-points.md,to-be/overview.md,to-be/benefits.md reproj=g0 -->
# 1. Business Context

## 1.1 Problem Statement
VastNet’s NOC handles unplanned network-fault alerts through a manual, tool-fragmented process. Analysts pivot between **SolarWinds NPM**, **Dynatrace**, **Infosim StableNet**, a jump host, SSH, and separate dashboards; initial triage takes 8–12 minutes and can reach 15 minutes when faults overlap overnight. The current delay is the stated primary driver of approximately 23% SLA misses across the previous two quarters.

## 1.2 Objectives
- Reduce the 8–12-minute manual triage path toward an automated path of under three minutes through normalization, classification, and parallel diagnostics.
- Reach the 15-minute contractual resolution-or-escalation commitment and create operational headroom through the 12-minute internal alert.
- Automatically resolve 80% of overnight faults without analyst involvement while retaining mandatory escalation and compliance controls.
- Enforce customer communication, change-control, and audit obligations consistently.

## 1.3 Expected Value
The future process removes avoidable system pivots, makes high-risk suppression and escalation deterministic, and delivers a complete evidence package when human intervention is required. It also frees analysts for proactive network-health work and complex incidents; measured targets are defined in Section 10.

[Refine section](delegate:refine-section?section=business-context)


<!-- pdd:section id=scope sources=as-is/scope.md,entities/applications/ reproj=g0 -->
# 2. Scope

## 2.1 Process Identity

*Table 1. Process identity*

| Field | Value |
|---|---|
| Process name | Automated Network Fault Detection and Remediation |
| Process group | Network Operations |
| Process identifier | VN-NOC-AFDR-001 |
| Industry | Telecommunications |

## 2.2 Scope Boundaries

*Table 2. Scope boundaries*

| In Scope | Out of Scope |
|---|---|
| Unplanned, reactively detected network faults | Planned maintenance windows |
| Dallas-anchored core and regional edge infrastructure | Change Advisory Board governed maintenance |
| Alert ingestion through resolution or active engineer escalation | Manual remediation after engineer takeover |
| ServiceNow incident, change-control, and audit updates | Customer Success internal communication execution |

## 2.3 Systems and Applications

*Table 3. Systems and applications*

| System | Role in Process | Access Type |
|---|---|---|
| **SolarWinds NPM** | Network alert source and interface evidence | Read |
| **Dynatrace** | Software-layer problem-event source | Read |
| **VastNet Integration Bus** | Alert webhook ingestion and normalization endpoint | Both |
| **Infosim StableNet** | Circuit-to-customer and topology enrichment | Read |
| **ServiceNow** | Incident and change system of record | Both |
| **AWX / Ansible Tower** | Configuration rollback execution | Write |
| **Kubernetes** | Routing-daemon restart execution | Write |
| **VastNet Path Controller** | MPLS failover execution | Write |
| **GitLab** | Golden configuration baseline | Read |
| **Splunk Enterprise** | Central audit-log retention | Write |

[Refine section](delegate:refine-section?section=scope)


<!-- pdd:section id=current-state sources=as-is/overview.md,as-is/process.bpmn,as-is/steps/,as-is/metrics-and-volumes.md,as-is/pain-points.md reproj=g0 -->
# 3. Current State

## 3.1 Overview
The current process is a manual NOC-led response to SolarWinds and Dynatrace alerts. An analyst investigates customer impact in StableNet, gathers diagnostic observations through disconnected tools, determines a response, and coordinates remediation or on-call escalation.

## 3.2 Current Flow

*Table 4. Current flow*

| # | Current step |
|---|---|
| 1 | Receive and manually triage monitoring alert. |
| 2 | Map the alerted device to affected circuits and customers in StableNet. |
| 3 | Run ping, BGP-state, and interface-counter checks sequentially. |
| 4 | Determine likely fault type and response. |
| 5 | Coordinate remediation or escalate to the on-call engineer. |

## 3.3 Metrics

*Table 5. Current-state metrics*

| Metric | Current signal | Measurement method |
|---|---|---|
| Initial triage time | 8–12 minutes; up to 15 minutes during concurrent overnight faults | NOC operations narrative |
| End-to-end SLA | 15 minutes | Enterprise Services Agreement / NOC policy |
| Internal target | 12 minutes | NOC policy |
| SLA miss rate | Approximately 23% over the prior two quarters | NOC operations narrative |
| Fault volume / backlog | Not supplied | Not confirmed |

## 3.4 Pain Points

*Table 6. Current-state pain points*

| Where | What breaks | Impact |
|---|---|---|
| NOC triage | Disconnected tools and manual data gathering | 8–12-minute triage period |
| Diagnostics | Sequential terminal and dashboard checks | Delay consumes most of 15-minute SLA window |
| Concurrent overnight queue | One analyst may hold multiple faults | Triage can reach 15 minutes |

```bpmn
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_CurrentFaultResponse" targetNamespace="https://vastnet.example/process/current-fault-response">
  <bpmn:collaboration id="Collaboration_CurrentFaultResponse">
    <bpmn:participant id="Participant_NOC" name="NOC Operations" processRef="Process_CurrentFaultResponse" />
  </bpmn:collaboration>
  <bpmn:process id="Process_CurrentFaultResponse" name="Current Network Fault Response" isExecutable="false">
    <bpmn:laneSet id="LaneSet_Current">
      <bpmn:lane id="Lane_NOC" name="NOC Analyst">
        <bpmn:flowNodeRef>Start_AlertReceived</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_TriageAlert</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_MapImpact</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_RunDiagnostics</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_CanResolve</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_CoordinateRemediation</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>End_Resolved</bpmn:flowNodeRef>
      </bpmn:lane>
      <bpmn:lane id="Lane_Engineer" name="On-Call Engineer">
        <bpmn:flowNodeRef>Task_EscalateEngineer</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>End_EngineerEngaged</bpmn:flowNodeRef>
      </bpmn:lane>
    </bpmn:laneSet>
    <bpmn:startEvent id="Start_AlertReceived" name="Monitoring alert received" />
    <bpmn:manualTask id="Task_TriageAlert" name="Manually triage alert" />
    <bpmn:manualTask id="Task_MapImpact" name="Map circuit impact" />
    <bpmn:manualTask id="Task_RunDiagnostics" name="Run sequential diagnostics" />
    <bpmn:exclusiveGateway id="Gateway_CanResolve" name="Can NOC resolve?" />
    <bpmn:manualTask id="Task_CoordinateRemediation" name="Coordinate remediation" />
    <bpmn:manualTask id="Task_EscalateEngineer" name="Escalate to on-call engineer" />
    <bpmn:endEvent id="End_Resolved" name="Service restored" />
    <bpmn:endEvent id="End_EngineerEngaged" name="Engineer actively engaged" />
    <bpmn:sequenceFlow id="Flow_01" sourceRef="Start_AlertReceived" targetRef="Task_TriageAlert" />
    <bpmn:sequenceFlow id="Flow_02" sourceRef="Task_TriageAlert" targetRef="Task_MapImpact" />
    <bpmn:sequenceFlow id="Flow_03" sourceRef="Task_MapImpact" targetRef="Task_RunDiagnostics" />
    <bpmn:sequenceFlow id="Flow_04" sourceRef="Task_RunDiagnostics" targetRef="Gateway_CanResolve" />
    <bpmn:sequenceFlow id="Flow_05" name="Yes" sourceRef="Gateway_CanResolve" targetRef="Task_CoordinateRemediation" />
    <bpmn:sequenceFlow id="Flow_06" name="No" sourceRef="Gateway_CanResolve" targetRef="Task_EscalateEngineer" />
    <bpmn:sequenceFlow id="Flow_07" sourceRef="Task_CoordinateRemediation" targetRef="End_Resolved" />
    <bpmn:sequenceFlow id="Flow_08" sourceRef="Task_EscalateEngineer" targetRef="End_EngineerEngaged" />
  </bpmn:process>
</bpmn:definitions>
```

*Figure: Current-state BPMN 2.0 process model.*

[Open AS-IS diagram](delegate:open-diagram?which=as-is&anchor=current-state)

[Refine section](delegate:refine-section?section=current-state)


<!-- pdd:section id=target-state sources=to-be/overview.md,to-be/process.bpmn,to-be/bpmn-details.md,to-be/transformation-decisions.md,to-be/participants-and-lanes.md,to-be/events-and-triggers.md,to-be/activities.md,to-be/gateways-and-routes.md,to-be/message-and-timer-flows.md,to-be/data-objects.md,to-be/exception-handling.md,to-be/benefits.md reproj=g0 -->
# 4. Future State

## 4.1 Vision
The future state is a deterministic, event-driven orchestration that normalizes and enriches alerts, creates or updates ServiceNow incidents, classifies impact, runs diagnostics in parallel, selects governed playbooks, verifies recovery, and closes or escalates each incident. Human engineers remain responsible for suppressed, failed, P1, hardware, and unsupported responses; the process model is business BPMN and does not prescribe a specific implementation product.

```bpmn
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_AutomatedFaultRemediation" targetNamespace="https://vastnet.example/process/automated-fault-remediation">
  <bpmn:collaboration id="Collaboration_AutomatedFaultRemediation">
    <bpmn:participant id="Participant_FaultRemediation" name="Automated Network Fault Detection and Remediation" processRef="Process_AutomatedFaultRemediation" />
  </bpmn:collaboration>
  <bpmn:process id="Process_AutomatedFaultRemediation" name="Automated Network Fault Detection and Remediation" isExecutable="false">
    <bpmn:laneSet id="LaneSet_Future">
      <bpmn:lane id="Lane_Orchestrator" name="Fault Remediation Orchestrator">
        <bpmn:flowNodeRef>Start_AlertReceived</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_NormalizeAlert</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_OpenIncident</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_ClassifyFault</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_NotifyCustomers</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_CommunicationsMerge</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_DiagnosticSplit</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_RunDiagnostics</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_DiagnosticJoin</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_SelectResponse</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_PageP1IfRequired</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_AutomatedAllowed</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_ConfigChange</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_CreateChange</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_ChangeReady</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_ExecutePlaybook</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_VerifyRecovery</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_VerificationPass</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_ResolveIncident</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>End_AutoResolved</bpmn:flowNodeRef>
      </bpmn:lane>
      <bpmn:lane id="Lane_CustomerSuccess" name="Customer Success Systems">
        <bpmn:flowNodeRef>Task_StartCustomerComms</bpmn:flowNodeRef>
      </bpmn:lane>
      <bpmn:lane id="Lane_Engineer" name="On-Call Engineer">
        <bpmn:flowNodeRef>Task_EscalateEngineer</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>End_Escalated</bpmn:flowNodeRef>
      </bpmn:lane>
    </bpmn:laneSet>
    <bpmn:startEvent id="Start_AlertReceived" name="Alert received" />
    <bpmn:serviceTask id="Task_NormalizeAlert" name="Normalize and enrich alert" />
    <bpmn:serviceTask id="Task_OpenIncident" name="Open or update incident" />
    <bpmn:businessRuleTask id="Task_ClassifyFault" name="Classify fault and impact" />
    <bpmn:exclusiveGateway id="Gateway_NotifyCustomers" name="100 or more accounts?" />
    <bpmn:sendTask id="Task_StartCustomerComms" name="Start customer communications" />
    <bpmn:exclusiveGateway id="Gateway_CommunicationsMerge" name="Communications complete" />
    <bpmn:parallelGateway id="Gateway_DiagnosticSplit" name="Start parallel diagnostics" />
    <bpmn:subProcess id="Task_RunDiagnostics" name="Run five diagnostics" />
    <bpmn:parallelGateway id="Gateway_DiagnosticJoin" name="Diagnostics complete" />
    <bpmn:businessRuleTask id="Task_SelectResponse" name="Select response playbook" />
    <bpmn:serviceTask id="Task_PageP1IfRequired" name="Page on-call if P1" />
    <bpmn:exclusiveGateway id="Gateway_AutomatedAllowed" name="Automated response allowed?" />
    <bpmn:exclusiveGateway id="Gateway_ConfigChange" name="Configuration change required?" />
    <bpmn:serviceTask id="Task_CreateChange" name="Create pre-execution change" />
    <bpmn:exclusiveGateway id="Gateway_ChangeReady" name="CHG in Implement status?" />
    <bpmn:serviceTask id="Task_ExecutePlaybook" name="Execute remediation playbook" />
    <bpmn:serviceTask id="Task_VerifyRecovery" name="Verify remediation" />
    <bpmn:exclusiveGateway id="Gateway_VerificationPass" name="Verification passed?" />
    <bpmn:serviceTask id="Task_ResolveIncident" name="Resolve incident and log evidence" />
    <bpmn:sendTask id="Task_EscalateEngineer" name="Escalate with evidence package" />
    <bpmn:endEvent id="End_AutoResolved" name="Resolved auto-closed" />
    <bpmn:endEvent id="End_Escalated" name="Escalated to on-call engineer" />
    <bpmn:sequenceFlow id="Flow_01" sourceRef="Start_AlertReceived" targetRef="Task_NormalizeAlert" />
    <bpmn:sequenceFlow id="Flow_02" sourceRef="Task_NormalizeAlert" targetRef="Task_OpenIncident" />
    <bpmn:sequenceFlow id="Flow_03" sourceRef="Task_OpenIncident" targetRef="Task_ClassifyFault" />
    <bpmn:sequenceFlow id="Flow_04" sourceRef="Task_ClassifyFault" targetRef="Gateway_NotifyCustomers" />
    <bpmn:sequenceFlow id="Flow_05" name="Yes" sourceRef="Gateway_NotifyCustomers" targetRef="Task_StartCustomerComms" />
    <bpmn:sequenceFlow id="Flow_06" name="No" sourceRef="Gateway_NotifyCustomers" targetRef="Gateway_CommunicationsMerge" />
    <bpmn:sequenceFlow id="Flow_07" sourceRef="Task_StartCustomerComms" targetRef="Gateway_CommunicationsMerge" />
    <bpmn:sequenceFlow id="Flow_08" sourceRef="Gateway_CommunicationsMerge" targetRef="Gateway_DiagnosticSplit" />
    <bpmn:sequenceFlow id="Flow_09" sourceRef="Gateway_DiagnosticSplit" targetRef="Task_RunDiagnostics" />
    <bpmn:sequenceFlow id="Flow_10" sourceRef="Task_RunDiagnostics" targetRef="Gateway_DiagnosticJoin" />
    <bpmn:sequenceFlow id="Flow_11" sourceRef="Gateway_DiagnosticJoin" targetRef="Task_SelectResponse" />
    <bpmn:sequenceFlow id="Flow_12" sourceRef="Task_SelectResponse" targetRef="Task_PageP1IfRequired" />
    <bpmn:sequenceFlow id="Flow_13" sourceRef="Task_PageP1IfRequired" targetRef="Gateway_AutomatedAllowed" />
    <bpmn:sequenceFlow id="Flow_14" name="No: peak, hardware, or unsupported" sourceRef="Gateway_AutomatedAllowed" targetRef="Task_EscalateEngineer" />
    <bpmn:sequenceFlow id="Flow_15" name="Yes" sourceRef="Gateway_AutomatedAllowed" targetRef="Gateway_ConfigChange" />
    <bpmn:sequenceFlow id="Flow_16" name="Yes" sourceRef="Gateway_ConfigChange" targetRef="Task_CreateChange" />
    <bpmn:sequenceFlow id="Flow_17" name="No" sourceRef="Gateway_ConfigChange" targetRef="Task_ExecutePlaybook" />
    <bpmn:sequenceFlow id="Flow_18" sourceRef="Task_CreateChange" targetRef="Gateway_ChangeReady" />
    <bpmn:sequenceFlow id="Flow_19" name="Yes" sourceRef="Gateway_ChangeReady" targetRef="Task_ExecutePlaybook" />
    <bpmn:sequenceFlow id="Flow_20" name="No" sourceRef="Gateway_ChangeReady" targetRef="Task_EscalateEngineer" />
    <bpmn:sequenceFlow id="Flow_21" sourceRef="Task_ExecutePlaybook" targetRef="Task_VerifyRecovery" />
    <bpmn:sequenceFlow id="Flow_22" sourceRef="Task_VerifyRecovery" targetRef="Gateway_VerificationPass" />
    <bpmn:sequenceFlow id="Flow_23" name="Pass" sourceRef="Gateway_VerificationPass" targetRef="Task_ResolveIncident" />
    <bpmn:sequenceFlow id="Flow_24" name="Fail" sourceRef="Gateway_VerificationPass" targetRef="Task_EscalateEngineer" />
    <bpmn:sequenceFlow id="Flow_25" sourceRef="Task_ResolveIncident" targetRef="End_AutoResolved" />
    <bpmn:sequenceFlow id="Flow_26" sourceRef="Task_EscalateEngineer" targetRef="End_Escalated" />
  </bpmn:process>
</bpmn:definitions>
```

*Figure: Future-state BPMN 2.0 process model.*

[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=target-state)

## 4.2 Target Flow

*Table 7. BPMN target flow*

| # | BPMN element | Participant / lane | Element type | Input / message | Output / route |
|---|---|---|---|---|---|
| 1 | Alert received | Orchestrator | Start event | SolarWinds or Dynatrace event | Starts Fault Record lifecycle |
| 2 | Normalize and enrich alert | Orchestrator | Activity | Source alert and StableNet data | FRS v3.2 Fault Record |
| 3 | Open or update incident | Orchestrator | Activity | Fault Record | ServiceNow INC |
| 4 | Classify fault and impact | Orchestrator | Activity | Fault Record | Priority, category, service impact, account count |
| 5 | 100 or more accounts? | Orchestrator | Gateway | Account count | Customer communication or continue |
| 6 | Run five diagnostics | Orchestrator | Subprocess | Affected segment | DSR after concurrent probes |
| 7 | Automated response allowed? | Orchestrator | Gateway | DSR and decision table | Playbook route or escalation |
| 8 | CHG in Implement status? | Orchestrator / ServiceNow | Gateway | Standard Change result | Execute configuration rollback or escalate |
| 9 | Verify remediation | Orchestrator | Activity | Synthetic probe | Pass or failure evidence |
| 10 | Resolve or escalate | Orchestrator / Engineer | End route | Verification and evidence package | Resolved Auto-Closed or Escalated |

## 4.2.1 Future Work Details

### Fault Remediation Orchestrator
> Receives faults, applies decision rules, controls remediation, and preserves the audit trail.

| Trigger/event | Activities | Key gateway | Owner/participant | Flows From | Flows To | Inputs/messages | Outputs/messages |
|---|---|---|---|---|---|---|---|
| Monitoring alert | Normalize, incident creation, classify, diagnostics, playbook selection, remediation, verification | 100-or-more accounts; remediation allowed; CHG ready; verification passed | Fault Remediation Orchestrator | SolarWinds / Dynatrace | ServiceNow, Customer Success, on-call engineer | Alert payload, StableNet enrichment, DSR | FRS, INC/CHG updates, action log, terminal state |

| # | BPMN element | Element type | System(s) / participant | Description |
|---|---|---|---|---|
| 1 | Normalize and enrich alert | Activity | VIB, StableNet | Convert alerts to FRS v3.2 and populate impact. |
| 2 | Run five diagnostics | Subprocess | ICMP, traceroute, SSH, SNMP, RESTCONF, GitLab | Complete probe battery within 120 seconds. |
| 3 | Select response playbook | Activity | Decision table | First matching rule determines response. |
| 4 | Create pre-execution change | Activity | ServiceNow | Return CHG number in Implement status before AWX call. |
| 5 | Execute remediation playbook | Activity | AWX, Kubernetes, Path Controller | Run authorized rollback, restart, failover, or protective action. |
| 6 | Verify remediation | Activity | Synthetic probe | Sample for 60 seconds; delivery >99.5% and latency within 5% baseline. |

### Customer Success Systems
> Sends customer notification independently of fault remediation when the contractual account threshold is met.

| Trigger/event | Activities | Key gateway | Owner/participant | Flows From | Flows To | Inputs/messages | Outputs/messages |
|---|---|---|---|---|---|---|---|
| 100 or more affected accounts | Status-page and contact notification | Account count is 100 or more | Customer Success Systems | Classification | Parallel diagnostic/remediation flow | Fault summary, account list, impact estimate | Communication status |

### On-Call Engineer
> Takes responsibility for high-risk, failed, P1, hardware, and non-automatable faults.

| Trigger/event | Activities | Key gateway | Owner/participant | Flows From | Flows To | Inputs/messages | Outputs/messages |
|---|---|---|---|---|---|---|---|
| Suppression, failed CHG, failed verification, or unsupported response | Review evidence and remediate manually | Escalation condition | On-call Engineer | Orchestrator | Escalated terminal state | DSR, action log, verification output | Active engineer engagement |

## 4.3 What Changes

*Table 8. Transformation summary*

| Area | AS-IS | TO-BE | Why | How |
|---|---|---|---|---|
| Alert intake | Manual queue pickup | Normalized FRS ingestion | Reduce delay | VIB webhook and enrichment |
| Diagnostics | Sequential analyst checks | Five concurrent probes | Compress evidence-gathering time | Parallel diagnostic subprocess |
| Response | Analyst judgement | Ordered decision table | Consistent, auditable routing | Rule-driven gateway selection |
| Change control | Risk of after-the-fact logging | Pre-execution CHG gate | Prevent policy violation | ServiceNow confirmation before AWX |
| Escalation | Potentially incomplete context | Evidence package and terminal escalation state | Protect SLA and engineer efficiency | DSR, logs, and probe output attached |

## 4.4 BPMN Work Summary
The model contains two event types, multiple service and business-rule activities, one diagnostic subprocess, and explicit gateway routes for communications, automation eligibility, pre-change approval, and verification. The unresolved implementation decision is the final choice of orchestration components and connector authentication, deferred to solution design.

[Refine section](delegate:refine-section?section=target-state)


<!-- pdd:section id=business-rules sources=as-is/business-rules.md,to-be/business-rules.md reproj=g0 -->
# 5. Business Rules

*Table 9. Business rules*

| Rule ID | Description |
|---|---|
| BR-001 | The process covers unplanned, reactively detected network faults; planned maintenance is excluded. |
| BR-002 | Tier 2 and Tier 3 faults must be restored or have active human-engineer engagement within 15 minutes of VIB alert receipt; internal alerting begins at 12 minutes. |
| BR-003 | P1 faults always page the on-call engineer through PagerDuty. |
| BR-004 | A service-affecting fault during 07:00–21:00 CST bypasses automated remediation and escalates. |
| BR-005 | Customer communication begins immediately and in parallel when 100 or more accounts are affected. |
| BR-006 | Configuration rollback requires a ServiceNow Standard Change in Implement status and a returned CHG number before AWX submission. |
| BR-007 | A failed or timed-out ServiceNow change call blocks the configuration action and escalates. |
| BR-008 | Every automated action is logged to ServiceNow and Splunk and retained for at least 24 months. |

[Refine section](delegate:refine-section?section=business-rules)


<!-- pdd:section id=data-model sources=entities/artifacts/,as-is/data-inputs-outputs.md reproj=g0 -->
# 6. Data Model

## 6.1 Entities

| Entity | Description |
|---|---|
| Fault Record | Canonical FRS v3.2 representation of a monitoring alert and its enriched impact. |
| Diagnostic Summary Record | Consolidated result of the five diagnostic probes. |
| ServiceNow Incident | System-of-record incident lifecycle and evidence. |
| ServiceNow Change | Pre-execution authorization for configuration rollback. |
| Audit Log | Immutable action evidence retained in ServiceNow and Splunk. |

## 6.2 Data Inputs and Outputs

*Table 10. Data inputs and outputs*

| Artifact | Source / Destination | Format | Consumed / Produced By |
|---|---|---|---|
| **Fault Record** | VIB to orchestration and ServiceNow | FRS v3.2 | Ingestion and classification |
| **Diagnostic Summary Record** | Diagnostics to response selection and escalation | Structured record | Diagnostic subprocess |
| **INC / CHG records** | ServiceNow | ServiceNow records | Lifecycle, control, and evidence |
| **Audit Log** | ServiceNow and Splunk | Structured action record | Every automated action |

## 6.3 Field-Level Data Dictionary

| Field | Type | Format / Pattern | Valid values / range | Mandatory | Privacy class |
|---|---|---|---|---|---|
| deviceId | String | Monitoring-platform identifier | Valid inventory device | Yes | Internal |
| alertSeverity | Integer | 1–5 | 1 through 5 | Yes | Internal |
| affectedAccountCount | Integer | Whole number | 0 or greater | Yes | Customer-impact data |
| faultPriority | String | P1–P4 | P1, P2, P3, P4 | Yes | Internal |
| CHG number | String | ServiceNow identifier | Existing Implement-status record | Conditional | Internal |

==TBD: confirm the privacy classification and handling controls for customer account and contact data at solution design==

## 6.4 Data Flow and Lineage

| # | Data movement |
|---|---|
| 1 | SolarWinds or Dynatrace emits an alert to VIB. |
| 2 | VIB normalizes payload, converts timestamp to UTC, and enriches circuits/accounts through StableNet. |
| 3 | Orchestration creates or updates ServiceNow INC and produces classification and DSR evidence. |
| 4 | Controlled playbooks return action outcomes; ServiceNow and Splunk receive audit evidence. |
| 5 | Verification produces the final resolution or escalation evidence package. |

## 6.5 Integrations

| Integration (System → System) | Fields passed | Connector / type | Endpoint + Auth |
|---|---|---|---|
| SolarWinds / Dynatrace → VIB | Alert identifiers, severity, entities, timestamps | Webhook | Not confirmed |
| VIB → StableNet | Device and circuit identifiers | API | Not confirmed |
| Orchestrator → ServiceNow | INC/CHG data, work notes, evidence | REST API | Not confirmed |
| Orchestrator → AWX / Kubernetes / Path Controller | Playbook parameters and action metadata | REST API / operator | Not confirmed |
| Orchestrator → Splunk | Audit fields | Logging API | Not confirmed |

==TBD: confirm the integration endpoint and authentication at SDD==

[Refine section](delegate:refine-section?section=data-model)


<!-- pdd:section id=people sources=entities/people/ reproj=g0 -->
# 7. People

## 7.1 Roles & Personas

*Table 11. Roles and personas*

| Stakeholder | Responsibility |
|---|---|
| NOC Analyst | Owns the current manual alert investigation and coordinates the present-day response. |
| Fault Remediation Orchestrator | System persona that executes the future-state lifecycle and control gates. |
| On-Call Engineer | Takes responsibility for P1, suppressed, failed, hardware, and unsupported incidents. |
| On-Call Field Engineer | Receives verification-failure escalation where field action is needed. |
| Customer Success Systems | Sends status-page and customer-contact communications for qualifying faults. |
| NOC Leadership | Receives 12-minute SLA-risk alerting. |
| ServiceNow | System-of-record persona for incidents, changes, work notes, and terminal states. |

## 7.2 RACI

*Table 12. RACI*

| Activity / Stage | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Alert intake, classification, and diagnostics | Fault Remediation Orchestrator | NOC Operations | Network Engineering | ServiceNow |
| Customer communication trigger | Customer Success Systems | Customer Success | NOC Operations | Affected account contacts |
| Configuration change authorization | ServiceNow / Fault Remediation Orchestrator | Change Control | Network Engineering | NOC Operations |
| Manual escalation and remediation | On-Call Engineer | Network Engineering | NOC Operations | NOC Leadership |
| SLA-risk oversight | NOC Leadership | NOC Operations | Network Engineering | Process Owner |

[Refine section](delegate:refine-section?section=people)


<!-- pdd:section id=raci sources=entities/people/ reproj=g0 -->
# 7.2 RACI

*Table 12. RACI*

| Activity / Stage | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Alert intake, classification, and diagnostics | Fault Remediation Orchestrator | NOC Operations | Network Engineering | ServiceNow |
| Customer communication trigger | Customer Success Systems | Customer Success | NOC Operations | Affected account contacts |
| Configuration change authorization | ServiceNow / Fault Remediation Orchestrator | Change Control | Network Engineering | NOC Operations |
| Manual escalation and remediation | On-Call Engineer | Network Engineering | NOC Operations | NOC Leadership |
| SLA-risk oversight | NOC Leadership | NOC Operations | Network Engineering | Process Owner |

[Refine section](delegate:refine-section?section=raci)


<!-- pdd:section id=exceptions sources=as-is/exception-handling.md,to-be/exception-handling.md reproj=g0 -->
# 8. Exceptions and Error Handling

## 8.1 Known Exceptions

| Exception | Trigger | AS-IS Handling | TO-BE Handling |
|---|---|---|---|
| Concurrent faults | Analyst handles multiple alerts | Queue delay and sequential triage | Event-driven processing; capacity baseline remains open |
| Peak-hour service impact | Service-affecting fault during 07:00–21:00 CST | Manual judgement | Suppress remediation, add work note, and page engineer |
| Hardware fault | Hardware/transceiver/line-card condition | Engineer escalation | No in-band playbook; escalate with DSR and field action where required |
| CHG failure | ServiceNow error or timeout | Not consistently defined | Block configuration change, log reason, and escalate |
| Verification failure | Synthetic probe does not meet thresholds | Manual follow-up | Escalate with DSR, attempt log, and probe output |

## 8.2 Exception Data State Transitions

| Exception | Affected record | State on entry | State on resolution | State on terminal failure |
|---|---|---|---|---|
| Peak-hours suppression | INC | Classified | In Progress — Escalated | In Progress — Escalated |
| CHG failure | INC / CHG | Pending controlled action | Configuration action released only with CHG confirmation | In Progress — Escalated |
| Verification failure | INC / DSR | Remediation attempted | Resolved — Auto-Closed when probe passes | In Progress — Escalated |

## 8.3 HITL & Action Center Task Form Specifications

*Table 13. Human escalation requirements*

| Escalation point | Trigger | Fields surfaced | Available actions → resulting state | Task SLA | Assignee role |
|---|---|---|---|---|---|
| On-call escalation | Peak suppression, unsupported/hardware route, CHG failure, or verification failure | INC, classification, DSR, remediation log, verification output, suppression reason | Acknowledge / take ownership → In Progress — Escalated; resolve manually → resolved per policy | Must support 15-minute terminal SLA | On-Call Engineer |

<!-- doc:placeholder kind="screenshot" -->
> [!NOTE]
> **Screenshot Placeholder**
> Insert screenshot: engineer escalation task showing incident evidence, diagnostic summary, and available ownership actions.

[Refine section](delegate:refine-section?section=exceptions)


<!-- pdd:section id=compliance sources=as-is/compliance.md,to-be/business-rules.md reproj=g0 -->
# 9. Compliance and Regulatory

## 9.1 Compliance Traceability Matrix

| Requirement / Rule | Enforced at | Evidence retained |
|---|---|---|
| BR-001 Scope restriction | Intake classification | Incident classification and process context |
| BR-002 15-minute SLA / 12-minute alert | ServiceNow lifecycle and Performance Analytics | Alert timestamp, terminal transition timestamp, SLA alert |
| BR-003 P1 page | Classification / PagerDuty action | Priority, page event, incident work note |
| BR-004 Peak-hour suppression | Automated-response gateway | Suppression reason and timestamp in work note |
| BR-005 Customer notification threshold | Account-count gateway | Trigger payload and communication status |
| BR-006 Pre-execution CHG | Change-control gateway | CHG number, Implement status, AWX metadata |
| BR-007 Failed-CHG escalation | Change-control exception | API failure record and escalation work note |
| BR-008 Audit retention | Every automated action | ServiceNow work notes and Splunk log for 24 months |

## 9.2 Audit & Traceability
Every action records action type, initiating system, target, UTC timestamp, outcome, and automated service-account identity in ServiceNow and Splunk. The incident and change references connect the response evidence to the contractual timing window and change-control obligations; retention is at least 24 months under DR-2022-01.

[Refine section](delegate:refine-section?section=compliance)


<!-- pdd:section id=kpis sources=to-be/benefits.md reproj=g0 -->
# 10. KPIs and Acceptance Criteria

## 10.1 KPIs

*Table 14. KPI targets*

| KPI | Target / acceptance signal |
|---|---|
| Automated triage duration | Under three minutes target, compared with current 8–12 minutes |
| Resolution or active engineer engagement | 100% within 15 minutes of VIB alert receipt |
| Internal SLA-risk alert | Leadership alerted at 12 minutes for in-flight incidents |
| Overnight automated resolution | 80% of overnight faults without analyst involvement |
| Diagnostic execution | Five probes complete within 120 seconds |
| Ingestion | Complete within 30 seconds |
| Verification | Packet delivery over 99.5% and latency within 5% of seven-day baseline |

## 10.2 Acceptance Criteria
- A qualifying alert is normalized, enriched, and linked to a ServiceNow INC within 30 seconds.
- All five diagnostic probes run concurrently and their results form one DSR within 120 seconds.
- A service-affecting peak-hours fault creates an escalation without executing automated remediation.
- Ansible rollback cannot be submitted until ServiceNow returns a CHG number in Implement status.
- A fault affecting 100 or more accounts starts the Customer Success trigger without waiting for remediation.
- Every automated action writes the required audit fields to ServiceNow and Splunk.

[Refine section](delegate:refine-section?section=kpis)


<!-- pdd:section id=assumptions-risks sources=queries/,as-is/scope.md reproj=g0 -->
# 11. Assumptions, Constraints, Dependencies and Risks

## 11.1 Assumptions

| Assumption | Detail |
|---|---|
| Contractual threshold precedence | 100 or more affected accounts is used because it is stricter than the conflicting operational wording. |
| Notification ownership | Customer Success systems own execution after receiving the trigger. |

## 11.2 Constraints

| Constraint | Detail |
|---|---|
| Peak-hours safety | 07:00–21:00 CST service-affecting faults bypass automated remediation. |
| Change control | Configuration actions require prior CHG confirmation in Implement status. |
| Audit retention | Action evidence retained for at least 24 months. |
| Privacy classification | Not confirmed. |

==TBD: confirm privacy classification and handling requirements for customer circuit and contact data==

## 11.3 Dependencies

| Dependency | Type (hard/soft) | Detail |
|---|---|---|
| Monitoring alert delivery | Hard | SolarWinds and Dynatrace must deliver complete events to VIB. |
| StableNet inventory | Hard | Must provide circuit-to-customer and topology enrichment. |
| ServiceNow APIs | Hard | Must support INC/CHG creation, status, work notes, and evidence. |
| AWX, Kubernetes, and Path Controller | Hard | Must execute approved remediation actions. |
| Customer Success workflow | Hard | Must accept immediate notification trigger and payload. |
| Integration endpoint and authentication design | Hard | Not confirmed; required for solution design. |

## 11.4 Risks

| Risk | Mitigation |
|---|---|
| Incomplete inventory or alert payload corrupts impact assessment | Validate enrichment outcomes and escalate incomplete records. |
| CHG API outage blocks configuration recovery | Escalate rather than bypass change control. |
| Automation executes during a high-risk service window | Enforce peak-hours gateway and audit suppression. |
| Fault volume exceeds orchestration capacity | Capture volume, backlog, and peak profile before sizing. |

[Refine section](delegate:refine-section?section=assumptions-risks)


<!-- pdd:section id=glossary sources=entities/ reproj=g0 -->
# 12. Glossary

*Table 15. Glossary*

| Term | Definition |
|---|---|
| AWX | Ansible Tower platform used for configuration rollback. |
| CHG | ServiceNow Change Management record. |
| DSR | Diagnostic Summary Record containing the parallel-probe results. |
| FRS v3.2 | VastNet canonical Fault Record Schema. |
| INC | ServiceNow Incident record. |
| LDP | Label Distribution Protocol used in MPLS environments. |
| MPLS | Multiprotocol Label Switching network transport technology. |
| NOC | Network Operations Center. |
| P1–P4 | Fault-priority classification scale. |
| VIB | VastNet Integration Bus. |

[Refine section](delegate:refine-section?section=glossary)


<!-- pdd:section id=next-steps sources=queries/open-questions.md reproj=g0 -->
# 13. Next Steps

*Table 16. Next steps*

| # | Action item |
|---|---|
| 1 | Confirm daily/weekly fault volume, backlog, aging, and peak profile for capacity sizing. |
| 2 | Confirm privacy classification and data-handling controls for customer circuit and contact data. |
| 3 | Validate ServiceNow, monitoring, inventory, execution-platform, and Splunk endpoint/authentication designs. |
| 4 | Define the engineer escalation task form and operational ownership model. |
| 5 | Load-test the complete path against the 15-minute terminal-state SLA. |
| 6 | Obtain Network Engineering, NOC Operations, Change Control, and Customer Success sign-off. |

[Refine section](delegate:refine-section?section=next-steps)


<!-- pdd:section id=appendix-a sources=derived reproj=g0 -->
# Appendix A: Process Map and Diagrams

The BPMN model embedded in Section 4.1 is the future process model of record. It represents the source-controlled sequence, gateway routes, handoffs, and terminal outcomes for the automated network-fault process.

<!-- doc:placeholder kind="integration-diagram" -->
> [!NOTE]
> **Integration Diagram Placeholder**
> Insert integration diagram: monitoring platforms, VIB, StableNet, ServiceNow, remediation platforms, Customer Success systems, PagerDuty, and Splunk; show incident, change, audit, and escalation messages.

[Refine section](delegate:refine-section?section=appendix-a)
