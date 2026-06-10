# Tasks

- [x] Task 1: Define landing apply guard behavior
  - [x] SubTask 1.1: Require landing-plan/v1 input, Human Gate evidence, test design, and write targets
  - [x] SubTask 1.2: Treat missing authorization, missing tests, missing patch, and target escape as blocking failures

- [x] Task 2: Implement landing apply entry
  - [x] SubTask 2.1: Add dry-run and write modes with JSON/text summaries
  - [x] SubTask 2.2: Restrict writes to project-local paths listed by plan write_targets
  - [x] SubTask 2.3: Preserve review_needed next steps and verification command output

- [x] Task 3: Update tests and task facts
  - [x] SubTask 3.1: Add tests for unauthorized, target escape, dry-run, and authorized write scenarios
  - [x] SubTask 3.2: Update task-0067 acceptance, deliverables, and verification evidence

- [x] Task 4: Validate and commit related files only
  - [x] SubTask 4.1: Run focused tests and full pytest
  - [x] SubTask 4.2: Run fact/spec validation and record known residual warnings
  - [x] SubTask 4.3: Commit only task-0067 related files and validation status fixes

# Task Dependencies

- Task 2 depends on Task 1.
- Task 3 depends on Task 2.
- Task 4 depends on Tasks 2 and 3.
