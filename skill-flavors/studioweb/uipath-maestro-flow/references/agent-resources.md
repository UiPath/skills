<!--skill-flavor:voice-conversational-resources-sdk-version:start-->
**Needs `@uipath/maestro-builder-sdk` newer than 6.85.2.** Check that
`dist/flow-sdk.d.ts` of the SDK that Studio Web ships declares `AgentResources`.
If not, do not give these options: an older SDK accepts them with no finding and
compiles the agent with no tool, context or escalation nodes.
<!--skill-flavor:voice-conversational-resources-sdk-version:end-->
