# Tasks

- [x] Task 1: Create and approve LDVH landing check report spec
  - [x] SubTask 1.1: Define report scope, safety boundary, consumed diagnostics, and task-0061 update requirements
  - [x] SubTask 1.2: Treat this user instruction as approval to implement after spec creation

- [x] Task 2: Implement LDVH landing check report
  - [x] SubTask 2.1: Reuse existing governed-projects, landing-report, runtime-projection, human-gate, fact, and spec validation helpers
  - [x] SubTask 2.2: Add report metadata, summary, checks, remaining_gaps, and CLI JSON/text output
  - [x] SubTask 2.3: Keep default scope project-local and read-only

- [x] Task 3: Update tests and task facts
  - [x] SubTask 3.1: Add tests for report status, missing governed-projects, fact/spec issue consumption, and CLI output
  - [x] SubTask 3.2: Update task-0061 verification and remaining gaps

- [x] Task 4: Validate and commit related files only
  - [x] SubTask 4.1: Run focused tests and full validation commands
  - [x] SubTask 4.2: Review diff to avoid unrelated deletions, user-level directory writes, or LDVH-GOVERNED changes
  - [ ] SubTask 4.3: Commit only related files

# Task Dependencies

- Task 2 depends on Task 1.
- Task 3 depends on Task 2.
- Task 4 depends on Tasks 2 and 3.
