# Vibe-Coding Control Modes Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the user's personal vibe-coding preference skill to support an Autopilot default and explicit, task-scoped Manual/Autopilot switching.

**Architecture:** Keep this as one focused personal skill at `~/.copilot/skills/vibe-coding-choice-preference/SKILL.md`. Add clear mode triggers, defaults, task boundaries, decision categories, and safety limits without changing the existing Recommended-first and routine `Allow all` behavior. Validate the skill by running identical pressure scenarios with isolated agents before and after the edit.

**Tech Stack:** Markdown skill document with YAML frontmatter; Copilot general-purpose subagents for pressure-scenario tests.

---

## File map

- Modify only `/home/nisreen/.copilot/skills/vibe-coding-choice-preference/SKILL.md`.
- Do not modify application code, repository instructions, or other skills.
- The reviewed design is `docs/superpowers/specs/2026-11-08-vibe-coding-control-modes-design.md`.

## Chunk 1: Verify the behavior gap and update the personal skill

### Task 1: Define baseline pressure scenarios

**Files:**
- No files; use isolated general-purpose subagents for behavior tests.

- [x] **Step 1: Run the baseline scenarios without the custom skill**

Baseline run completed before editing. The tested pressures were:

1. **Manual override under time pressure:** Prior Recommended-first delegation,
   short deadline, and a user instruction to ask before a layout decision.
2. **Autopilot with an external-risk boundary:** User delegates the task and is
   unavailable; assistant must choose a reversible local approach but not
   publish a potentially production-impacting deployment.
3. **Mid-task mode change:** Task starts under prior Autopilot delegation, then
   user says they will control the next design choice.
4. **No mode specified:** The user asks for an explicit Manual/Autopilot option
   but does not choose one for the current task, then presents three options with
   option one marked Recommended.

Observed baseline: the agent handled explicit Manual override, the production
approval boundary, and prospective mode changes correctly. In the no-mode
scenario, it proposed **Manual as the default**, contradicting the user's
established delegation. The test did not exercise a same-task follow-up versus
a new-task boundary; the current skill also provides no rule for that
distinction. The missing default and task-boundary rules are the gaps to
correct and explicitly test after the edit.

### Task 2: Update the user-level skill

**Files:**
- Modify: `/home/nisreen/.copilot/skills/vibe-coding-choice-preference/SKILL.md`

- [ ] **Step 1: Preserve and inspect the current skill before editing**

Read the current full skill and verify its only frontmatter keys are `name` and
`description`. Keep the existing rules for Recommended-first choices,
task-scoped `Allow all`, newer task-specific instructions, and safety
boundaries.

- [ ] **Step 2: Define the requested mode behavior in the skill**

Edit the skill to state:

- Autopilot is the default when the user has not selected a mode.
- In Autopilot, make safe, reversible, task-scoped decisions using relevant
  skills; keep selecting option one when it is marked Recommended and avoid
  repeated prompts for routine decisions or permissions already covered.
- Clear user-directed phrases such as `Manual`, `ควบเอง`, `Autopilot`, and
  `มอบอำนาจ` switch the mode. Do not treat quoted or discussed keywords as a
  switch. A mode change applies prospectively and never undoes completed work.
- In Manual mode, pause before decisions about user-visible behavior/UX, scope,
  significant architecture/dependencies, or external side effects. Continue
  independent work and routine implementation within already approved
  requirements; do not ask about every minor coding detail unless the user
  requests step-by-step control. Never guess to bypass a decision pause.
- Follow-ups and corrections on the same deliverable retain the selected mode.
  A distinct new request or explicit completion starts a new task in default
  Autopilot mode unless the user specifies otherwise.
- Autopilot does not impersonate the user, invent personal preferences, or
  claim approval for external actions. Preserve explicit approval requirements
  for secrets, destructive/irreversible operations, production-impacting
  changes, and other restricted actions.

Update the description to start with `Use when...` and include the manual/
Autopilot switching trigger while keeping it focused on when the skill applies.

- [ ] **Step 3: Review the edited skill for clarity and scope**

Confirm the document remains concise, has only `name` and `description` in
frontmatter, and retains the current permission and safety boundaries. Remove
any ambiguous statements that imply Autopilot can answer on the user's behalf
or that Manual blocks independent approved work.

### Task 3: Re-run pressure scenarios with the skill

**Files:**
- Test: `/home/nisreen/.copilot/skills/vibe-coding-choice-preference/SKILL.md`

- [ ] **Step 1: Re-run the same four baseline scenarios with the skill enabled**

Use the same pressure scenario wording as Task 1, adding an instruction to apply
the updated skill. Expected results:

1. Manual wins over prior delegation and deadline pressure; the assistant pauses
   for the layout decision while continuing independent work.
2. Autopilot chooses the reversible local approach, but does not deploy without
   required approval.
3. The mid-task switch applies to future decisions only; completed work remains.
4. With no mode specified, the user's established Autopilot default applies and
   the first Recommended option is selected without another prompt.

- [ ] **Step 2: Test additional mode and task-boundary cases**

Run isolated agent scenarios for:

- A user-directed switch from Manual back to Autopilot takes effect
  prospectively.
- Quoting “Manual” or “Autopilot” for discussion does not switch modes.
- A follow-up on the same deliverable retains the chosen mode, while a distinct
  new request resets to Autopilot unless specified otherwise.
- Manual pauses for representative UX, scope, architecture/dependency, and
  external-side-effect choices, but not routine implementation details.
- `Allow all` remains limited to ordinary task-scoped permissions.

- [ ] **Step 3: Verify the skill metadata and final diff**

Parse the YAML frontmatter and verify its exact keys and description with the
available Python YAML parser:

```bash
python3 -c 'from pathlib import Path; import yaml; text=Path("/home/nisreen/.copilot/skills/vibe-coding-choice-preference/SKILL.md").read_text(); metadata=yaml.safe_load(text.split("---", 2)[1]); assert set(metadata) == {"name", "description"}; assert metadata["description"].startswith("Use when"); assert "Manual" in metadata["description"] and "Autopilot" in metadata["description"]'
```

Expected: Exit status 0. Then inspect the final skill diff and confirm there are
no unrelated file changes. If this personal skill directory is not
version-controlled, report that it is a user-level local change rather than
attempting to commit it to the application repository.
