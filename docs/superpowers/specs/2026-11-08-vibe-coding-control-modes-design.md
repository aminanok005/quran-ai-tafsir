# Vibe-Coding Control Modes Design

## Goal

Extend the user's personal `vibe-coding-choice-preference` skill with a clear,
task-scoped way to choose between user-led Manual control and delegated
Autopilot, while preserving the existing preference for recommended options and
routine task-scoped permissions.

## Current context

The personal skill currently says to choose the first option when offered
exactly three choices, especially if it is marked Recommended, and to accept
ordinary task-scoped `Allow all` permissions. It already says to follow newer
task-specific instructions and limits the preference around secrets,
destructive actions, production changes, and external actions requiring
approval. It does not define a Manual mode, an Autopilot default, or how a mode
can change during a task.

Baseline pressure scenarios showed that an assistant can infer that an explicit
Manual request overrides the earlier delegation, stop before a potentially
production-impacting deployment, and apply a mid-task mode change prospectively.
However, without a defined default and switch phrases, assistants can still
disagree about when to ask versus decide.

## Mode behavior

- **Autopilot is the default** when the user has not selected a different mode.
  This preserves the user's established delegation.
- In Autopilot, make safe, reversible, task-scoped decisions using the
  applicable skills and repository context. For a three-choice prompt, continue
  choosing option one, especially when it is marked Recommended. Do not pause
  for routine choices or permissions already covered by the user's stated
  `Allow all` preference.
- **Manual mode** is enabled by clear task instructions such as “Manual,”
  “ควบเอง,” or “I want to control this.” Pause before deciding on user-visible
  behavior or UX, scope changes, significant architecture/dependency choices,
  or external side effects; present the decision for the user. Continue
  independent research and implementation within already approved requirements.
  Do not interrupt for routine coding details unless the user asks to direct
  every step, and do not guess to bypass a decision pause.
- The user can switch modes at any time using phrases such as “Autopilot,”
  “มอบอำนาจ,” “Manual,” or “ควบเอง,” when the user is directing the assistant
  to change modes. Merely quoting or discussing these words does not switch the
  mode. A switch applies to decisions from that point forward and does not undo
  completed work.
- A task remains active through follow-up messages, corrections, and review of
  the same requested deliverable. A distinct new request or a clear statement
  that the previous task is complete starts a new task; initialize that task in
  default Autopilot mode unless the user specifies otherwise.
- Autopilot means choosing among implementation decisions, not impersonating
  the user, fabricating the user's personal preferences, or claiming the user
  approved an external action. Continue to require separate approval for
  secrets exposure, irreversible/destructive actions, production-impacting
  changes, and other actions that applicable instructions require the user to
  approve.

## Scope and implementation

Update only the personal skill file:
`~/.copilot/skills/vibe-coding-choice-preference/SKILL.md`.
Keep its existing choice preference and safety boundaries, update its
description to mention Manual/Autopilot mode selection, and add concise mode
defaults, switch behavior, and examples to the body. Do not modify application
code or other skills.

## Validation

- Re-run the same pressure scenarios used for baseline: Manual override under
  time pressure; Autopilot with a reversible local choice and a
  production-impacting external action; a mid-task switch from Autopilot to
  Manual; and mode reset on a distinct new task while preserving mode through
  a follow-up on the same deliverable.
- In Manual mode, verify the assistant pauses for representative user-visible
  behavior, scope, architecture/dependency, and external-side-effect choices,
  while continuing independent research and approved implementation.
- Verify Autopilot handles routine recommended choices without a repeated
  prompt, while Manual waits for the user's decision.
- Verify a user-directed switch from Manual back to Autopilot takes effect
  prospectively, and quoted mentions do not switch modes.
- Verify neither mode bypasses approval or safety boundaries.
- Confirm the skill frontmatter remains valid with only `name` and `description`
  and that the description starts with “Use when...”.
