# Deliverable Inventory

- Total deliverables: 33

| ID | Artifact | Category | Current path | Expected path | Build | Run | Inclusion | License/confidentiality | Missing dependencies | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-NATIVE-001 | CPU_SIM shared library source | NATIVE_PLUGIN | hcccl | native/libhccl_plugin.so | BUILDABLE_STATIC_AUDIT_REQUIRED | HOST_EXECUTED_HISTORICAL | INCLUDE_WITH_CPU_SIM_LABEL | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-NATIVE-002 | Official-ABI direct adapter | NATIVE_PLUGIN | hcccl/direct | native/direct_adapter_or_wrapper | STATIC_ARCHIVE_BUILD_ONLY | HOST_HARNESS_ONLY | INCLUDE_SOURCE_AND_READINESS_DOCS | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-BUILD-001 | CMake build configuration | BUILD_CONFIGURATION | hcccl/CMakeLists.txt | native/CMakeLists.txt | PRESENT | CONFIGURED_HISTORICAL | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-SOURCE-001 | Public CPU_SIM headers | SOURCE_CODE | hcccl/include | native/include | PRESENT | NOT_EXECUTABLE | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-SOURCE-002 | Direct adapter public header | SOURCE_CODE | hcccl/direct/include/hccl_direct_adapter.h | native/include/hccl_direct_adapter.h | PRESENT | HOST_HARNESS_ONLY | INCLUDE_WITH_BOUNDARY | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-AGENT-001 | Agent source and CLI | AGENT_ENGINEERING | agent | agent | PYTHON_IMPORTABLE | HOST_EXECUTED | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-D |
| ART-AGENT-002 | Top-level Agent CLI | AGENT_ENGINEERING | main.py | main.py | PYTHON_IMPORTABLE | CPU_SIM_HOST_EXECUTED | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | frozen dependency inventory<br>clean-environment bootstrap | G3-B |
| ART-SKILL-001 | Agent Skills source | PROMPT_AND_SKILLS | skills | agent/skills | PYTHON_IMPORTABLE | HOST_EXECUTED | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-D |
| ART-PROMPT-001 | Prompt template set | PROMPT_AND_SKILLS | prompts/algorithm_prompt.txt | agent/prompts/algorithm_prompt.txt | PRESENT | PARTIAL_RUNTIME_USE | INCLUDE_AFTER_VERSIONING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-D |
| ART-TRACE-001 | Authoritative Agent run logs | EVIDENCE | — | agent/evidence/runs.jsonl | MISSING | MISSING | MISSING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | sanitized authoritative run log<br>commit mapping | G3-D |
| ART-TRACE-002 | Authoritative Prompt call logs | EVIDENCE | — | agent/evidence/prompt_calls.jsonl | MISSING | MISSING | MISSING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | sanitized prompt records<br>prompt version | G3-D |
| ART-TRACE-003 | Generated code and commit trace | EVIDENCE | examples/generated_code | agent/evidence/generation_trace | UNVERIFIED_PROVENANCE | STATIC_EXAMPLES_ONLY | REBUILD_IN_G3_D | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-D |
| ART-SIM-001 | Simulator source | SIMULATOR | simulator | simulator | PYTHON_IMPORTABLE | HOST_EXECUTED | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-SIM-002 | Simulator acceptance runners | SIMULATOR | simulator/tools | simulator/tools | PYTHON_IMPORTABLE | HOST_EXECUTED_HISTORICAL | INCLUDE_AFTER_REPRO_WRAPPER | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | G2-F-5 requires built CPU_SIM library | G3-B |
| ART-CONFIG-001 | Cluster configuration | CONFIGURATION | config/cluster.json | simulator/config/cluster.json | PRESENT | READ_BY_AGENT | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-TEST-001 | C tests | TEST_TOOL | hcccl/tests | tests/native | BUILDABLE | HOST_EXECUTED_HISTORICAL | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-TEST-002 | Python tests | TEST_TOOL | tests | tests/python | PYTHON_IMPORTABLE | HOST_EXECUTED_HISTORICAL | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-BENCH-001 | Benchmark tools | BENCHMARK_TOOL | agent/benchmark_skill.py | tools/benchmark | PYTHON_IMPORTABLE | HOST_EXECUTED | INCLUDE_AFTER_UNIFIED_CLI | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-FAULT-001 | Fault injection tools | FAULT_INJECTION_TOOL | simulator/fault_injector.py | tools/fault_injection | PYTHON_IMPORTABLE | SIMULATOR_EXECUTED | INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-EVID-001 | G2-E official VM final evidence | EVIDENCE | experiments/hccl_vm/evidence/g2_e_summary_20260730T095800.105217Z | evidence/g2_e | IMMUTABLE | VERIFIED | INCLUDE_OR_REFERENCE_AFTER_SIZE_REVIEW | PROJECT_EVIDENCE / SUBMISSION_ARTIFACT | — | G3-B |
| ART-EVID-002 | G2-F final evidence | EVIDENCE | experiments/final_audit/evidence/g2_f_7_20260805T010000Z | evidence/g2_f_7 | IMMUTABLE | VERIFIED | INCLUDE | PROJECT_EVIDENCE / SUBMISSION_ARTIFACT | — | G3-B |
| ART-EVID-003 | Simulator correctness evidence | EVIDENCE | experiments/simulator/evidence/g2_f_5_simulator_20260804T010000Z | evidence/simulator_correctness | IMMUTABLE | VERIFIED | INCLUDE | PROJECT_EVIDENCE / SUBMISSION_ARTIFACT | — | G3-B |
| ART-EVID-004 | Simulator performance/reliability evidence | EVIDENCE | experiments/simulator/evidence/g2_f_6_simulator_20260804T020000Z | evidence/simulator_performance | IMMUTABLE | VERIFIED | INCLUDE | PROJECT_EVIDENCE / SUBMISSION_ARTIFACT | — | G3-B |
| ART-DOC-001 | Top-level README | TECHNICAL_REPORT | README.MD | README.md | PRESENT | NOT_EXECUTABLE | UPDATE_AND_INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-DOC-002 | Simulator manual | TECHNICAL_REPORT | docs/simulator_guide.md | docs/simulator_manual.md | STALE | NOT_EXECUTABLE | REWRITE_FROM_EVIDENCE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-C |
| ART-DOC-003 | Direct readiness appendix | TECHNICAL_REPORT | docs/direct_api_contract.md | docs/direct_readiness_appendix.md | PRESENT | NOT_EXECUTABLE | UPDATE_AND_INCLUDE | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-C |
| ART-DOC-004 | Formal algorithm/correctness/performance/reliability reports | TECHNICAL_REPORT | — | reports | INCOMPLETE | NOT_EXECUTABLE | MISSING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | formal performance report<br>formal scale report<br>updated reliability report | G3-C |
| ART-DEMO-001 | Five-minute demo video | DEMO_MATERIAL | — | demo/five_minute_demo.mp4 | MISSING | MISSING | MISSING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-F |
| ART-DEMO-002 | Demo script/storyboard/captions | DEMO_MATERIAL | — | demo | MISSING | MISSING | MISSING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-F |
| ART-RELEASE-001 | Submission manifest and SHA256 | RELEASE_METADATA | — | manifest | MISSING | MISSING | MISSING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | — | G3-B |
| ART-RELEASE-002 | Project license and notices | RELEASE_METADATA | — | LICENSE | MISSING | MISSING | MISSING | PROJECT_LICENSE_MISSING / SUBMISSION_ARTIFACT | license choice<br>copyright/team confirmation | USER_ACTION |
| ART-INTERNAL-001 | Controlled competition DOCX | INTERNAL_REFERENCE | docs/2026年中国研究生人工智能大赛--华为赛题.docx | EXCLUDED_BY_DEFAULT | PRESENT | READ_ONLY | EXCLUDE_PENDING_USER_CONFIRMATION | CONFIDENTIALITY_REVIEW_REQUIRED / INTERNAL_REFERENCE | — | USER_ACTION |
| ART-OFFICIAL-001 | Official CANN/HCOMM/HCCL binaries/source | INTERNAL_REFERENCE | — | EXCLUDED_BY_DEFAULT | EXTERNAL_ONLY | STATIC_QUERIES_ONLY | EXCLUDE | REDISTRIBUTION_REVIEW_REQUIRED / OFFICIAL_THIRD_PARTY | — | USER_ACTION |
