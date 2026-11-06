<!--skill-flavor:voice-conversational-resources-sdk-version:start-->
**Needs the `@uipath/maestro-builder-sdk` release that ships UiPath/builder-sdk#1716.**
Check that `dist/flow-sdk.d.ts` of the SDK that Studio Web ships declares
`AgentResources`. If not, do not give these options: an SDK without it accepts them with no finding and
compiles the agent with no tool, context or escalation nodes.
<!--skill-flavor:voice-conversational-resources-sdk-version:end-->
