# Feature specification: optional MCP and chat access

Status: future requirement, approved for specification; no transport, dependency or deployment selected.

## Purpose
Let a user interact with ShabbatFlow from a compatible chat client: inspect a period, explain a schedule, prepare a future draft, record post-observance feedback and review evidence-backed adjustments. The dashboard and deterministic local planner continue to work without AI or MCP.

## Functional requirements
- CHAT-FR-001: Expose planner operations through an optional MCP adapter using the same application services, schemas, validation and permission checks as the dashboard. Do not implement a second scheduler in prompts or tool handlers.
- CHAT-FR-002: Provide read operations for plan versions, calendar coverage/source status, dated room/meal choices, proposed events and reasons, feedback summaries and adjustment proposals. Return actual dates, timezone, source/version and completeness, not ambiguous “next Friday” identifiers alone.
- CHAT-FR-003: Support separately authorized draft operations: create/update a future plan, preview changes, submit/correct feedback and create/accept/reject/defer adjustment proposals. Use expected revisions to reject stale writes; return the saved revision and before/after differences. Retryable requests require idempotency protection so a repeated chat call does not duplicate feedback or edits.
- CHAT-FR-004: Draft edits and accepting a proposal do not activate a plan. Initial chat scope excludes device control, changes to HA automations, activation and mutation of frozen plans. Any future activation tool needs a separately reviewed requirement, explicit capability authorization and exact plan/digest confirmation; a prompt is not an enforcement mechanism.
- CHAT-FR-005: Map authenticated identities to planner read/draft/feedback/review permissions. Enforce authorization server-side. Minimize returned/exported household data, never return credentials, and record meaningful write audit events. Treat user notes and imported history as data, not tool instructions.
- CHAT-FR-006: Explain uncertain relative dates, incomplete inputs, overlap conflicts, missing calendar coverage, unavailable providers and unsupported actions. Ask for material ambiguities before saving; offer a preview of the concrete change. Do not infer individuals or occupancy from device usage.
- CHAT-FR-007: Support English/Hebrew interaction by default within the multilingual architecture. Tool schemas, IDs, units, timestamps and errors remain language-neutral; localized descriptions and human summaries preserve identical semantics.
- CHAT-FR-008: Document supported clients, transport/authentication, discovery, permissions, compatibility versions and network reachability. Running in HA is supported as a deployment target subject to adapter verification; an HA-hosted endpoint must be reachable from the actual MCP client. Local-only use must not require public exposure. Cloud-hosted clients require an explicitly configured authenticated remote path; never silently open ports or enable remote access.
- CHAT-FR-009: Evaluate exposing planner tools through HA's existing MCP/LLM API infrastructure before introducing a separate server. Select the approach only after confirming supported extension APIs, scoped permissions and version compatibility. HA's built-in tools do not automatically provide ShabbatFlow-specific draft/feedback operations. Any extra package or integration requires dependency review.
- CHAT-FR-010: Support a guided “review last observance” flow: choose the exact period, inspect available evidence, collect optional ratings and exceptions, propose a future revision and show its preview for owner review. Missing history does not block manual feedback and never becomes evidence of success/failure.

## Nonfunctional requirements
- CHAT-NFR-001: Dashboard and chat calls against identical revisions yield identical validation and schedule results. Model-generated prose is advisory and cannot override deterministic checks.
- CHAT-NFR-002: Validate bounded typed payloads; reject unknown fields/actions. No arbitrary code, templates, shell commands or generic unchecked HA service calls. Apply authentication and transport protections appropriate to the selected deployment.
- CHAT-NFR-003: Automated contract tests cover unauthorized calls, stale revisions, repeated requests, frozen-plan edits, unknown tools, malicious instruction-like note text and equivalent dashboard/chat results before enabling writes.
- CHAT-NFR-004: Optional adapter failure must not stop an approved local schedule or require AI during observance. Avoid logging credentials or full free-text feedback; define audit retention before production deployment.

## Proposed tool families (illustrative, not an API commitment)
Read: list periods, get plan, explain schedule, inspect coverage, summarize feedback.
Draft: create/update draft, preview plan, submit feedback, propose adjustment, review proposal.
No initial activate-plan, control-device or modify-HA-automation tools.

## Acceptance scenarios
A user asks which rooms are planned for recreation on day two and receives that segment's choices, not guessed occupancy. A feedback submission interrupted and retried creates one record. A stale draft update returns a conflict and current revision. An adjustment accepted in chat creates a future draft but leaves the frozen plan unchanged. A read-only user cannot submit edits. Network loss stops chat access without changing the household schedule. Equivalent English/Hebrew requests pass the same typed validation.

## Research references and pending decision
Official HA MCP documentation: https://www.home-assistant.io/integrations/mcp_server/
Official MCP server transport documentation: https://ts.sdk.modelcontextprotocol.io/server
These are research references, not adopted code/dependencies. Inspect the installed HA version and extension contract before promising compatibility. Do not convert the unauthenticated loopback preview harness into a remotely exposed production server.
