# AOCS Omega MCP - UML Statechart

This file is the visual twin of `docs/000_AOCS_OMEGA_TASK_AND_DECISION_LOG.md`.

Use this when you want to see the whole project as states instead of paragraphs.

Beginner explanation:

- A state is a condition the project can be in.
- A transition is movement from one state to another.
- A composite state is a big state that contains smaller states.
- An orthogonal region means several areas are true at the same time. For example, the architecture, provider strategy, testing strategy, and documentation strategy all exist in parallel.

Rule for future updates: do not delete old diagram sections without recording why. Add new states or add a new dated diagram section.

## 2026-06-14 - Current Project Statechart

```plantuml
@startuml AOCS_Omega_MCP_Current_State

title AOCS Omega MCP - Current System And Decision State - 2026-06-14
hide empty description

skinparam shadowing false
skinparam state {
  BackgroundColor White
  BorderColor #333333
  FontColor #111111
}

[*] --> ProjectAlive

state "ProjectAlive: AOCS Omega MCP version before GitHub push" as ProjectAlive {

  state "UserGoalAndConstraints" as UserGoalAndConstraints {
    [*] --> NeedDeterministicEngine
    NeedDeterministicEngine : AOCS must be code-enforced, not only a skill prompt.
    NeedDeterministicEngine --> NeedPortableAdapters
    NeedPortableAdapters : Must work across OpenCode, Claude Code, Cursor, Codex, and future agents.
    NeedPortableAdapters --> NeedSimpleTrigger
    NeedSimpleTrigger : User should trigger with slash command, button, MCP tool, or CLI.
    NeedSimpleTrigger --> NeedNoHostDamage
    NeedNoHostDamage : Do not silently rewrite global host-agent settings.
    NeedNoHostDamage --> NeedSecretSafety
    NeedSecretSafety : API keys and tokens stay out of repo files.
    NeedSecretSafety --> NeedLivingDocs
    NeedLivingDocs : Preserve context in text and statechart after every chat.
  }

  --

  state "ArchitectureRegion" as ArchitectureRegion {
    [*] --> SkillOnlyRejected
    SkillOnlyRejected : Markdown skill alone is not deterministic enough.
    SkillOnlyRejected --> CoreRuntimeChosen

    state "CoreRuntimeChosen" as CoreRuntimeChosen {
      [*] --> RuntimeOwnsWorkflow
      RuntimeOwnsWorkflow : AOCSRuntime owns phase order, model calls, artifacts, and final result.
      RuntimeOwnsWorkflow --> AdaptersAreButtons
      AdaptersAreButtons : MCP, CLI, and slash commands trigger runtime only.
      AdaptersAreButtons --> OuterAgentReceivesResult
      OuterAgentReceivesResult : Host coding agent receives final AOCS output.
    }

    CoreRuntimeChosen --> OnePublicMCPToolChosen

    state "OnePublicMCPToolChosen" as OnePublicMCPToolChosen {
      [*] --> PublicAocsRunFull
      PublicAocsRunFull : aocs_run_full is the canonical MCP entrypoint.
      PublicAocsRunFull --> PublicAocsAnalyzeAlias
      PublicAocsAnalyzeAlias : aocs_analyze remains as compatibility alias.
      PublicAocsAnalyzeAlias --> DebugToolsHidden
      DebugToolsHidden : Internal phase tools hidden unless expose_debug_tools is true.
    }

    OnePublicMCPToolChosen --> CLIFallbackChosen

    state "CLIFallbackChosen" as CLIFallbackChosen {
      [*] --> AocsRunCommand
      AocsRunCommand : aocs run "problem" runs AOCS without a host app.
      AocsRunCommand --> UniversalBackup
      UniversalBackup : Any agent that can run terminal commands can call AOCS.
    }
  }

  --

  state "RuntimeExecutionRegion" as RuntimeExecutionRegion {
    [*] --> RequestCreated
    RequestCreated : AOCSRunRequest carries problem, domain, risk, context, depth, budget, and metadata.
    RequestCreated --> RunIdCreated
    RunIdCreated : Runtime creates timestamp plus hash run id.
    RunIdCreated --> ArtifactsPrepared
    ArtifactsPrepared : .aocs/runs/<run-id>/ stores request, status, trace, result, summary.
    ArtifactsPrepared --> RouterPrepared
    RouterPrepared : LLMRouter resets trace and call budget.
    RouterPrepared --> OrchestratorRuns

    state "OrchestratorRuns" as OrchestratorRuns {
      [*] --> DirectLowRiskCheck
      DirectLowRiskCheck --> DirectLowRiskAnswer : low risk plus simple arithmetic
      DirectLowRiskCheck --> Phase0 : otherwise
      DirectLowRiskAnswer : one direct-answer model call, accept result.
      DirectLowRiskAnswer --> FinalResult

      Phase0 : Parse, multi-frame, map assumptions, quantify uncertainty, find root, deep test.
      Phase0 --> Phase1
      Phase1 : Score sub-problems.
      Phase1 --> Classification
      Classification : Choose Type 1, Type 2, or Type 3.
      Classification --> Type1Route : known problem
      Classification --> Type2Route : partially known / high-stakes problem
      Classification --> Type3Route : unknown / discovery problem
      Type1Route --> QualitySubject
      Type2Route --> QualitySubject
      Type3Route --> QualitySubject
      QualitySubject --> QualityGates
      QualityGates --> Observer
      Observer --> ShadowOrchestrator
      ShadowOrchestrator --> MemoryAudit
      MemoryAudit --> FinalResult
    }

    OrchestratorRuns --> ArtifactsWritten
    ArtifactsWritten : trace.json, result.json, summary.md, and final status.json are written.
    ArtifactsWritten --> RuntimeReturns
    RuntimeReturns : MCP or CLI receives structured AnalysisResult.
  }

  --

  state "ProviderStrategyRegion" as ProviderStrategyRegion {
    [*] --> DirectApiBaseline
    DirectApiBaseline : Reliable baseline uses explicit provider APIs.

    state "DirectApiBaseline" as DirectApiBaseline {
      [*] --> OpenCodeGoDirect
      OpenCodeGoDirect : Preferred current test path. Uses OPENCODE_API_KEY and hosted HTTPS.
      OpenCodeGoDirect --> OpenAIFamily
      OpenAIFamily : OpenAI provider supported.
      OpenAIFamily --> AnthropicFamily
      AnthropicFamily : Anthropic provider and claude alias supported.
      AnthropicFamily --> OpenRouterFamily
      OpenRouterFamily : OpenRouter provider supported with OPENROUTER_API_KEY.
      OpenRouterFamily --> GeminiFamily
      GeminiFamily : Gemini and google alias supported with GEMINI_API_KEY or GOOGLE_API_KEY.
      GeminiFamily --> NvidiaFamily
      NvidiaFamily : NVIDIA and nvidia-nim alias supported with NVIDIA_API_KEY.
    }

    DirectApiBaseline --> HostCliKeptAsFallback
    HostCliKeptAsFallback : Host CLI can exist, but it is fragile and not primary.
    HostCliKeptAsFallback --> MCPSamplingDeferred
    MCPSamplingDeferred : MCP Sampling researched, promising, but deferred for this version.
  }

  --

  state "AdapterRegion" as AdapterRegion {
    [*] --> OpenCodeAdapter

    state "OpenCodeAdapter" as OpenCodeAdapter {
      [*] --> OpenCodeProjectConfig
      OpenCodeProjectConfig : opencode.jsonc starts python -m aocs_mcp as local MCP server.
      OpenCodeProjectConfig --> OpenCodeSlashCommand
      OpenCodeSlashCommand : .opencode/commands/aocs-run.md is a thin trigger.
    }

    OpenCodeAdapter --> ClaudeAdapter

    state "ClaudeAdapter" as ClaudeAdapter {
      [*] --> ClaudeSlashCommand
      ClaudeSlashCommand : .claude/commands/aocs-run.md is a thin trigger.
      ClaudeSlashCommand --> ClaudeMCPExample
      ClaudeMCPExample : README documents python -m aocs_mcp MCP config pattern.
    }

    ClaudeAdapter --> FutureAdapters
    FutureAdapters : Cursor, Codex, and future agents should use MCP or CLI without core rewrites.
  }

  --

  state "SafetyAndConfigRegion" as SafetyAndConfigRegion {
    [*] --> ProjectScopedFirst
    ProjectScopedFirst : Prefer project configs over global host-agent edits.
    ProjectScopedFirst --> SecretsInEnv
    SecretsInEnv : Keys use environment variables, never committed files.
    SecretsInEnv --> RunStorageIsolated
    RunStorageIsolated : AOCS stores artifacts in .aocs/runs, not host agent databases.
    RunStorageIsolated --> SmallMcpSurface
    SmallMcpSurface : Only main tools visible by default to reduce context load and misuse.
  }

  --

  state "TestingAndEvidenceRegion" as TestingAndEvidenceRegion {
    [*] --> ProviderSmokeTestPassed
    ProviderSmokeTestPassed : OpenCode Go direct HTTPS returned TEST_OK.
    ProviderSmokeTestPassed --> RuntimeSimpleTestPassed
    RuntimeSimpleTestPassed : what is 2+2 returned 4 through direct-low-risk route.
    RuntimeSimpleTestPassed --> MCPProtocolTestPassed
    MCPProtocolTestPassed : MCP listed aocs_run_full and aocs_analyze and tool call worked.
    MCPProtocolTestPassed --> OpenCodeMCPIsolatedConnected
    OpenCodeMCPIsolatedConnected : Isolated OpenCode config showed aocs-omega connected.
    OpenCodeMCPIsolatedConnected --> ScriptTestsPassed
    ScriptTestsPassed : Runtime, router, provider, direct HTTP, orchestrator, config, phase0, scorer tests passed.
    ScriptTestsPassed --> SecretScanClean
    SecretScanClean : No obvious committed API key or server password found.
  }

  --

  state "DocumentationAndPublishingRegion" as DocumentationAndPublishingRegion {
    [*] --> LivingDocsCreated
    LivingDocsCreated : Create text decision log and UML statechart docs.
    LivingDocsCreated --> AppendOnlyPolicy
    AppendOnlyPolicy : Future chats append instead of deleting historical context.
    AppendOnlyPolicy --> ReadyForGitCommit
    ReadyForGitCommit : Commit current runtime, adapters, providers, tests, and docs.
    ReadyForGitCommit --> ReadyForGitHubPush
    ReadyForGitHubPush : Push version to budhasantosh010/AOCS-OmegaMCP.
  }
}

ProjectAlive --> VersionPublished : after successful git commit and push
VersionPublished : Remote repository contains this documented AOCS runtime version.

@enduml
```

## 2026-06-15 - Shadow Reroute Promotion Delta

```plantuml
@startuml AOCS_Omega_Shadow_Reroute_Promotion_2026_06_15

title AOCS Omega MCP - Shadow Reroute Promotion - 2026-06-15
hide empty description

[*] --> UserTranscriptChecked
UserTranscriptChecked : User transcript shows doctor OK, 2+2 direct-answer OK, and AGI deep run completed.

UserTranscriptChecked --> AGIRunAnalyzed
AGIRunAnalyzed : AGI run route=type2, verdict=flag_for_review, confidence=88, total_llm_calls=11.

AGIRunAnalyzed --> ShadowFindsCriticalType3
ShadowFindsCriticalType3 : Shadow orchestrator safe_path=Use shadow: type3 (risk critical).

ShadowFindsCriticalType3 --> GapFound
GapFound : Shadow warning was recorded but not promoted strongly enough into final recommendations.

GapFound --> OrchestratorUpdated
OrchestratorUpdated : _build_recommendations now includes conservative shadow reroute when safe_path uses shadow.

OrchestratorUpdated --> AcceptDowngradeRule
AcceptDowngradeRule : _apply_shadow_escalation downgrades accept to flag_for_review when shadow says safer route.

AcceptDowngradeRule --> RegressionTestAdded
RegressionTestAdded : Test asserts Type 3 critical shadow reroute appears in recommendations.

RegressionTestAdded --> TestsPassed
TestsPassed : orchestrator, runtime, and router tests passed.

TestsPassed --> [*]

@enduml
```

## 2026-06-15 - Beginner Arithmetic Smoke Test Fix Delta

```plantuml
@startuml AOCS_Omega_Beginner_Arithmetic_Smoke_Fix_2026_06_15

title AOCS Omega MCP - Beginner Arithmetic Smoke Test Fix - 2026-06-15
hide empty description

[*] --> UserRunsDefaultArithmetic
UserRunsDefaultArithmetic : User runs python -m aocs_mcp.cli run "what is 2+2?"

UserRunsDefaultArithmetic --> DeepPipelineBug
DeepPipelineBug : CLI defaults risk=medium and fractal_depth=1 send trivial arithmetic into Type 2 pipeline.

DeepPipelineBug --> JsonFailureObserved
JsonFailureObserved : Model returns prose for a structured phase; runtime reports Could not extract JSON.

JsonFailureObserved --> DeterministicArithmeticDecision
DeterministicArithmeticDecision : Obvious two-number arithmetic should be solved by code before any LLM call.

DeterministicArithmeticDecision --> OrchestratorUpdated
OrchestratorUpdated : _solve_simple_arithmetic handles +, -, *, x, X, and / safely.

OrchestratorUpdated --> ExactCommandRetested
ExactCommandRetested : python -m aocs_mcp.cli run "what is 2+2?" --no-store

ExactCommandRetested --> SmokeTestPasses
SmokeTestPasses : route=direct-arithmetic; answer=4; total_llm_calls=0; verdict=accept.

SmokeTestPasses --> RegressionTestsPassed
RegressionTestsPassed : orchestrator, doctor, router, runtime, provider, OpenCode direct HTTP tests passed.

RegressionTestsPassed --> [*]

@enduml
```

## 2026-06-15 - Correction: Direct Arithmetic Still Uses LLM Delta

```plantuml
@startuml AOCS_Omega_Direct_Arithmetic_Uses_LLM_2026_06_15

title AOCS Omega MCP - Direct Arithmetic Uses LLM Correction - 2026-06-15
hide empty description

[*] --> UserRejectsCodeAnswer
UserRejectsCodeAnswer : User states AOCS answers should be delivered by LLM reasoning, not hidden code computation.

UserRejectsCodeAnswer --> DesignPrincipleRestated
DesignPrincipleRestated : Code enforces rails and routing; LLM roles perform reasoning and produce answers.

DesignPrincipleRestated --> DeterministicAnswerRemoved
DeterministicAnswerRemoved : Code no longer computes 2+2 = 4 itself.

DeterministicAnswerRemoved --> SimpleProblemRouted
SimpleProblemRouted : Code detects simple arithmetic only to avoid the deep JSON pipeline.

SimpleProblemRouted --> DirectAnswerRoleCalled
DirectAnswerRoleCalled : router.call(role="direct-answer") produces the answer.

DirectAnswerRoleCalled --> CorrectedResultShape
CorrectedResultShape : route=direct-answer; total_llm_calls=1; specialist_proposal comes from LLM.

CorrectedResultShape --> RegressionTestUpdated
RegressionTestUpdated : Tests assert direct-answer role is called and call count is 1.

RegressionTestUpdated --> [*]

@enduml
```

## 2026-06-15 - No-Install Test Confusion And Doctor Encoding Fix Delta

```plantuml
@startuml AOCS_Omega_NoInstall_Doctor_Fix_2026_06_15

title AOCS Omega MCP - No-Install Test Confusion And Doctor Fix - 2026-06-15
hide empty description

[*] --> UserRunsNoInstallDoctor
UserRunsNoInstallDoctor : User runs python -m aocs_mcp.cli doctor from PowerShell.

UserRunsNoInstallDoctor --> UnicodeDecodeCrash
UnicodeDecodeCrash : Python subprocess decodes OpenCode output with cp1252 and crashes on Unicode byte.

UnicodeDecodeCrash --> StdoutNoneCrash
StdoutNoneCrash : subprocess stdout becomes None and doctor calls .strip() on None.

StdoutNoneCrash --> DoctorFixed
DoctorFixed : _run_command uses UTF-8, errors=replace, and (stdout or '').strip().

DoctorFixed --> UserRunsDefaultTwoPlusTwo
UserRunsDefaultTwoPlusTwo : User runs python -m aocs_mcp.cli run "what is 2+2?"

UserRunsDefaultTwoPlusTwo --> DeepDefaultRoute
DeepDefaultRoute : Default risk=medium and fractal_depth=1 cause Type 2 over-analysis.

DeepDefaultRoute --> CorrectSmokeCommand
CorrectSmokeCommand : Use --risk low --fractal-depth 0 --max-sub-agents 1 for simple smoke tests.

CorrectSmokeCommand --> SecurityReminder
SecurityReminder : Pasted API keys in chat/transcripts should be rotated.

SecurityReminder --> [*]

@enduml
```

## 2026-06-15 - Setup Hardening And Coauthor Check Delta

```plantuml
@startuml AOCS_Omega_Setup_Hardening_And_Coauthors_2026_06_15

title AOCS Omega MCP - Setup Hardening And Coauthor Check - 2026-06-15
hide empty description

[*] --> UserAsksNext
UserAsksNext : User asks what is next and asks to remove Claude as GitHub coauthor.

UserAsksNext --> GitHistoryInspected
GitHistoryInspected : Recent and full git history inspected for authors, committers, and Co-authored-by trailers.

GitHistoryInspected --> NoClaudeCoauthorFound
NoClaudeCoauthorFound : Only budhasantosh010 appears as author and committer; no Claude coauthor metadata found.

NoClaudeCoauthorFound --> NoHistoryRewrite
NoHistoryRewrite : Decision: do not rewrite Git history because there is no coauthor metadata to remove.

NoHistoryRewrite --> DoctorCommandAdded
DoctorCommandAdded : aocs doctor added as beginner-facing setup diagnostic.

state "DoctorCommandAdded" as DoctorCommandAdded {
  [*] --> ChecksPython
  ChecksPython --> ChecksPackages
  ChecksPackages --> ChecksConfigFiles
  ChecksConfigFiles --> ChecksProviderEnvNames
  ChecksProviderEnvNames --> ChecksOpenCodeConfig
  ChecksOpenCodeConfig --> ChecksOpenCodeBinary
  ChecksOpenCodeBinary --> ChecksOpenCodeMCP
}

DoctorCommandAdded --> DoctorJsonAdded
DoctorJsonAdded : aocs doctor --json added for automation.

DoctorJsonAdded --> DoctorNoOpenCodeAdded
DoctorNoOpenCodeAdded : aocs doctor --no-opencode added for non-OpenCode hosts.

DoctorNoOpenCodeAdded --> WindowsCmdFix
WindowsCmdFix : Doctor now resolves opencode and opencode.cmd.

WindowsCmdFix --> VerificationPassed
VerificationPassed : doctor CLI, JSON output, doctor tests, and router regression test passed.

VerificationPassed --> CurrentDoctorState
CurrentDoctorState : Full doctor reports OpenCode MCP connected; only warning is missing provider API env var.

CurrentDoctorState --> [*]

@enduml
```

## Future Update Template

Add a new dated section with either a full replacement statechart or a small delta diagram.

```plantuml
@startuml AOCS_Omega_MCP_Delta_YYYY_MM_DD

title AOCS Omega MCP - Delta - YYYY-MM-DD

[*] --> PreviousState
PreviousState --> NewState : what changed
NewState : why it changed

@enduml
```

## 2026-06-14 - Pre-Push Verification Delta

```plantuml
@startuml AOCS_Omega_MCP_PrePush_Verification_Delta_2026_06_14

title AOCS Omega MCP - Pre-Push Verification Delta - 2026-06-14
hide empty description

[*] --> DocsCreated
DocsCreated : Two living docs created in docs/.
DocsCreated --> SecretScanClean
SecretScanClean : Search found no pasted API key or GitHub token in repo files.
SecretScanClean --> TestsStarted
TestsStarted : Direct test run first needed PYTHONPATH because package was not installed in current Python environment.
TestsStarted --> TestsPassedWithPyPath
TestsPassedWithPyPath : models, scorer, phase0, router, orchestrator, opencode, direct-http, provider-adapter tests passed.
TestsPassedWithPyPath --> TempWriteSandboxIssue
TempWriteSandboxIssue : config and runtime tests needed temp directory writes blocked by sandbox.
TempWriteSandboxIssue --> TempWriteTestsPassedEscalated
TempWriteTestsPassedEscalated : config and runtime tests passed outside sandbox.
TempWriteTestsPassedEscalated --> CompileallSkippedAsEnvironmentIssue
CompileallSkippedAsEnvironmentIssue : compileall only failed because .pyc cache writes were blocked.
CompileallSkippedAsEnvironmentIssue --> ReadyToCommitAndPush
ReadyToCommitAndPush : Current code, adapters, tests, and docs are ready for GitHub publish.

@enduml
```

## 2026-06-15 - Real OpenCode MCP Smoke Test Delta

```plantuml
@startuml AOCS_Omega_MCP_Real_OpenCode_Smoke_2026_06_15

title AOCS Omega MCP - Real OpenCode MCP Smoke Test - 2026-06-15
hide empty description

[*] --> RepoClean
RepoClean : main matched origin/main before test.
RepoClean --> OpenCodeDetected
OpenCodeDetected : OpenCode 1.16.0 was installed and auth list showed real credentials.
OpenCodeDetected --> EnvKeyMissing
EnvKeyMissing : OPENCODE_API_KEY was not set in the shell environment.
EnvKeyMissing --> MCPListRun
MCPListRun : opencode mcp list was run from the project repo.
MCPListRun --> MCPConnected
MCPConnected : aocs-omega connected through python -m aocs_mcp.
MCPConnected --> AgentSmokeRun
AgentSmokeRun : opencode run asked real agent to call aocs_run_full once.
AgentSmokeRun --> ToolInvoked
ToolInvoked : OpenCode invoked aocs-omega_aocs_run_full with the low-risk 2+2 input.
ToolInvoked --> RuntimeProviderError
RuntimeProviderError : AOCS runtime returned OPENCODE_API_KEY not set in environment.
RuntimeProviderError --> PartialSuccessConclusion
PartialSuccessConclusion : MCP integration works; full run needs OPENCODE_API_KEY supplied to OpenCode's environment.
PartialSuccessConclusion --> NextTestReady
NextTestReady : Set OPENCODE_API_KEY in shell, then rerun OpenCode agent MCP smoke test.

@enduml
```

## 2026-06-15 - Real OpenCode Chat-Style MCP Success Delta

```plantuml
@startuml AOCS_Omega_MCP_Real_OpenCode_Chat_Success_2026_06_15

title AOCS Omega MCP - Real OpenCode Chat-Style MCP Success - 2026-06-15
hide empty description

[*] --> UserRequestsRealChatTest
UserRequestsRealChatTest : Test should behave like OpenCode GUI/chat problem solving.

UserRequestsRealChatTest --> ApiKeyProcessEnv
ApiKeyProcessEnv : OPENCODE_API_KEY is supplied only to the process environment.

ApiKeyProcessEnv --> FirstMediumRun
FirstMediumRun : OpenCode calls aocs_run_full for medium architecture question.

FirstMediumRun --> TimeoutFailure
TimeoutFailure : MCP error -32001 Request timed out at 30000 ms.

TimeoutFailure --> BadManualFallbackObserved
BadManualFallbackObserved : OpenCode manually emulated AOCS using Markdown skill after timeout.

BadManualFallbackObserved --> TimeoutIncreased
TimeoutIncreased : Project OpenCode MCP timeout changed to 300000 ms.

TimeoutIncreased --> StrictLowRiskRun
StrictLowRiskRun : Strict test forbids skill fallback and calls aocs_run_full for what is 2+2.

StrictLowRiskRun --> LowRiskSuccess
LowRiskSuccess : MCP_SUCCESS=4; run 20260615T050331Z-61a33850 completed; 1 LLM call; accept.

LowRiskSuccess --> StrictMediumRun
StrictMediumRun : Strict architecture test calls aocs_run_full with max_sub_agents=12.

StrictMediumRun --> MediumSuccess
MediumSuccess : MCP_SUCCESS; run 20260615T050411Z-56ffec8b completed; 11 LLM calls; flag_for_review; confidence 90.

MediumSuccess --> VerifiedOperationalPath
VerifiedOperationalPath : OpenCode agent -> MCP -> AOCSRuntime -> LLMRouter -> OpenCode Go direct HTTPS -> AOCS result.

VerifiedOperationalPath --> [*]

@enduml
```

## 2026-06-15 - Open-Domain Request Boundary Correction Delta

```plantuml
@startuml AOCS_Omega_MCP_Open_Domain_Request_Boundary_2026_06_15

title AOCS Omega MCP - Open-Domain Request Boundary Correction - 2026-06-15
hide empty description

[*] --> UserRejectsHiddenDefaults
UserRejectsHiddenDefaults : User states every problem is new and AOCS must not force software/medium defaults.

state "Previous Behavior" as PreviousBehavior {
  [*] --> AdapterInjectedDomain
  AdapterInjectedDomain : CLI/MCP/slash command could inject domain=software.
  AdapterInjectedDomain --> AdapterInjectedRisk
  AdapterInjectedRisk : CLI/MCP/slash command could inject risk=medium.
  AdapterInjectedRisk --> SentinelDepth
  SentinelDepth : CLI used -1 sentinel and MCP used 0 default for fractal depth.
  SentinelDepth --> ProblemPreShaped
  ProblemPreShaped : AOCS received a pre-shaped request before Phase 0 reasoning.
}

UserRejectsHiddenDefaults --> BoundaryRedesigned

state "Corrected Request Boundary" as BoundaryRedesigned {
  [*] --> DomainOptional
  DomainOptional : domain omitted means request.domain=null.
  DomainOptional --> RiskOptional
  RiskOptional : risk omitted means request.risk=null.
  RiskOptional --> DepthOptional
  DepthOptional : fractal_depth omitted means request.fractal_depth=null.
  DepthOptional --> ExplicitHintsOnly
  ExplicitHintsOnly : adapters pass domain/risk/depth only when user explicitly gives them.
}

BoundaryRedesigned --> Phase0OpenDomain

state "Open-Domain Phase 0" as Phase0OpenDomain {
  [*] --> ParserAutoInfer
  ParserAutoInfer : Parser prints Domain auto-infer from problem.
  ParserAutoInfer --> OpenLenses
  OpenLenses : Multi-Framer uses generic domain/evidence/safety/frontier lenses.
  OpenLenses --> OpenAssumptions
  OpenAssumptions : Assumption Mapper uses open-domain assumptions unless domain is explicit.
}

Phase0OpenDomain --> InternalClassification

state "Internal AOCS Classification" as InternalClassification {
  [*] --> ClassifierUsesEvidence
  ClassifierUsesEvidence : Classifier decides Type 1/2/3 and risk after Phase 0.
  ClassifierUsesEvidence --> RiskMayStillBeMedium
  RiskMayStillBeMedium : risk=medium may appear as an internal decision, not a caller default.
}

InternalClassification --> Type3OpenDomain

state "Open-Domain Type 3" as Type3OpenDomain {
  [*] --> GenericDiscoveryLenses
  GenericDiscoveryLenses : Type 3 uses Domain Inference, First Principles, Evidence, Systems, Safety.
  GenericDiscoveryLenses --> NoSoftwareUnlessEvidence
  NoSoftwareUnlessEvidence : Prompt says do not assume software unless evidence points there.
}

Type3OpenDomain --> RegressionTests

state "Regression Tests" as RegressionTests {
  [*] --> OpenDomainTestAdded
  OpenDomainTestAdded : tests/test_open_domain_defaults.py added.
  OpenDomainTestAdded --> SuitePassed
  SuitePassed : python -X utf8 -B -m pytest tests -p no:cacheprovider => 38 passed.
}

RegressionTests --> CurrentContract
CurrentContract : Current rule - do not provide domain/risk/fractal_depth unless user explicitly gives them.
CurrentContract --> [*]

@enduml
```
