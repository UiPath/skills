# Agent Prompting Guide

Robust prompts for low-code agents. This guide contains shared prompting details for autonomous and conversational agents, and then references the specific prompting guides for both variants.

## Shared

This guide owns prompt **quality**; [agent-definition.md](../agent-definition.md#contenttokens-construction) owns the `contentTokens` **mechanics** (keep `content` ↔ `contentTokens` in sync after every edit here).

Name every tool in the prompt as `@{tools.<Name>}`, where `<Name>` is the tool resource's `name` field, and mirror it as an `expression` contentToken. A bare tool name in prose is not linked to the resource.

> Default scaffolds ship toy or empty prompts ("You are a helpful agentic assistant" / "What is the current date?" / ""). Replace them. A placeholder system prompt is the single biggest quality gap in a scaffolded agent.

## Autonomous Agents

When building a low-code autonomous agent, refer to [autonomous-agent-prompting-guide.md](autonomous-agent-prompting-guide.md) for the autonomous-specific prompting guide.

## Conversational Agents

When building a low-code conversational agent, refer to [conversational-agent-prompting-guide.md](conversational-agent-prompting-guide.md) for the conversational-specific prompting guide.
