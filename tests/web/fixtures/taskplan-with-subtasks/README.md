# TaskPlan With SubTasks Fixture

This fixture is a synthetic LDVH fact source for Web/API tests.

Use the fixture root as `LDVH_ROOT` when running the Web app:

```bash
cd web
LDVH_ROOT=../tests/web/fixtures/taskplan-with-subtasks npm run dev
```

The Web API test also reads this fixture directly.

It intentionally covers:

- Task statuses: `planned`, `executing`, `verifying`, `review_needed`, `closed`
- SubTask statuses: `planned`, `executing`, `verifying`, `review_needed`, `closed`
- Task-level `blocked_by` relationships
- SubTask-level `blocked_by` relationships
