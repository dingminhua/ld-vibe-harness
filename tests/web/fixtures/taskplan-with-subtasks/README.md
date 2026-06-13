# TaskPlan With SubTasks Fixture

This fixture is a synthetic LDVH fact source for Web/API tests.

Use the fixture root as `LDVH_ROOT` when running the Web app:

```bash
cd web
LDVH_ROOT=../tests/web/fixtures/taskplan-with-subtasks npm run dev
```

The Web API test also reads this fixture directly.

It intentionally covers:

- 4 WorkArea records across active and archived status
- 10 TaskPlan records across active, review_needed, and closed status
- Task statuses: `planned`, `executing`, `verifying`, `review_needed`, `closed`
- SubTask statuses: `planned`, `executing`, `verifying`, `review_needed`, `closed`
- 33 Task records, including tasks with no subtasks, mixed subtasks, parallel subtasks, verification subtasks, verified subtasks, closed subtasks, planned tasks, blocked tasks, and close-decision evidence samples
- TaskPlan close-decision cases: review-ready with all Tasks closed, active with missing plan evidence, active with partial Task evidence, and closed with complete evidence
- Task-level `blocked_by` relationships
- SubTask-level `blocked_by` relationships
