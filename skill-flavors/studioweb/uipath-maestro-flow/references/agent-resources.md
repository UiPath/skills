<!--skill-flavor:voice-conversational-resources-sdk-version:start-->
**Needs the `@uipath/maestro-builder-sdk` release that ships UiPath/builder-sdk#1716.**
Check that `grep -rlw AgentResources <sdk>/dist`, run on the SDK that Studio Web
ships, finds a file. If not, do not give these options: an SDK where it finds no file accepts them with no finding and
compiles the agent with no tool, context or escalation nodes.
<!--skill-flavor:voice-conversational-resources-sdk-version:end-->
