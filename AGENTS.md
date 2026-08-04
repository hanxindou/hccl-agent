# hccl-agent Project Instructions

## Scope

- Keep changes narrowly aligned with the requested competition feature.
- Do not scan or parse the entire `docs/` directory unless the task concerns documentation or competition requirements.
- Preserve existing Python and C plugin interfaces unless interface changes are explicitly required.

## Validation

- Run the smallest affected Python test module first.
- Run affected C tests when modifying `hcccl/`.
- Do not run the complete Python and C test suites after every small edit.
- Run the full relevant suite before declaring a substantial feature complete.
- Use concise test output and report the pass/fail count.

## Documentation

- Update existing documentation only when behavior, architecture, interfaces, setup steps, or competition coverage materially changes.
- Prefer editing an existing document over creating a new overlapping document.
