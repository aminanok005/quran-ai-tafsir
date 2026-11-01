# Skill: Parallel Task Manager

## Purpose
Coordinate multiple coding agents without overlapping edits.

## Procedure
1. Discover repository state.
2. Break work into independently testable tasks.
3. Assign exactly one owner to each file path.
4. Identify shared contracts and freeze them.
5. Give each agent a separate worktree.
6. Record dependencies and acceptance criteria.
7. Require reports before integration.
8. Detect overlapping file changes.
9. Escalate conflicts to Coordinator.

## Required task contract
TASK ID, AGENT, OBJECTIVE, ALLOWED FILES, FORBIDDEN FILES,
DEPENDENCIES, INPUT CONTRACT, OUTPUT CONTRACT, TESTS,
ACCEPTANCE CRITERIA, REPORT LOCATION.

Never assume agents can automatically communicate or launch one another.
