# Commit Convention

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Commit Convention |
| Document ID | GIT-STD-002 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | Entire Repository |
| Classification | Engineering Standard |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document defines the commit message convention used throughout the MedMatch repository.

Its objective is to produce a Git history that is readable, searchable, predictable, and suitable for long-term maintenance.

A consistent commit history improves code reviews, debugging, release management, and repository traceability.

This document specifies commit structure, commit types, message formatting, and repository history expectations.

---

# Scope

These conventions apply to every commit made to the repository, including:

- Backend services
- Frontend
- Infrastructure
- Documentation
- Database migrations
- Monitoring
- CI/CD
- Security
- Automation

Every contributor shall follow these conventions.

---

# Commit Philosophy

A commit represents one logical unit of work.

Every commit should answer a single question:

> **What changed and why?**

Commits should remain:

- Small
- Focused
- Independent
- Reviewable
- Reversible

A commit should never combine unrelated work.

Examples of unrelated work:

- Feature implementation and documentation cleanup
- Bug fix and dependency upgrade
- Refactoring and new functionality

Such work shall be committed separately.

---

# Conventional Commit Format

Every commit message shall follow the format:

```text
<type>: <short summary>
```

Examples:

```text
feat: add patient eligibility endpoint

fix: validate JWT expiration

docs: add repository standards

refactor: simplify matching service

test: add integration tests for login

build: update Docker image

ci: configure GitHub Actions
```

The summary should:

- Begin with a lowercase verb.
- Be concise.
- Describe the completed change.
- Avoid ending punctuation.

---

# Commit Types

The following commit types are permitted.

| Type | Purpose |
|------|---------|
| feat | New functionality |
| fix | Bug fix |
| docs | Documentation changes |
| refactor | Internal code improvement without changing behavior |
| test | Add or update tests |
| build | Build system or dependency changes |
| ci | CI/CD workflow changes |
| chore | Repository maintenance tasks |
| perf | Performance improvements |
| style | Formatting changes without behavioral impact |
| revert | Revert a previous commit |

Each commit shall use the type that best represents its primary purpose.

---

# Commit Type Definitions

## feat

Introduces new functionality.

Example:

```text
feat: implement JWT refresh endpoint
```

---

## fix

Corrects incorrect behavior.

Example:

```text
fix: prevent duplicate patient registration
```

---

## docs

Updates documentation only.

Example:

```text
docs: add API authentication guide
```

---

## refactor

Improves implementation without changing observable behavior.

Example:

```text
refactor: extract eligibility validation service
```

---

## test

Adds or improves automated tests.

Example:

```text
test: add unit tests for trial repository
```

---

## build

Modifies the build process or project dependencies.

Example:

```text
build: upgrade Spring Boot to 3.5.16
```

---

## ci

Changes continuous integration or deployment automation.

Example:

```text
ci: add Docker image publishing workflow
```

---

## chore

Repository maintenance that does not affect application behavior.

Example:

```text
chore: remove obsolete configuration
```

---

## perf

Improves performance without changing functionality.

Example:

```text
perf: optimize vector similarity search
```

---

## style

Formatting changes only.

Example:

```text
style: format Java source files
```

---

## revert

Reverts a previous commit.

Example:

```text
revert: remove experimental cache implementation
```

---

---

# Commit Message Rules

Every commit message shall consist of a single summary line.

Format:

```text
<type>: <summary>
```

The summary shall:

- Start with a lowercase verb.
- Describe what the commit accomplishes.
- Be written in the imperative mood.
- Avoid unnecessary implementation details.
- Not end with a period.

Good:

```text
feat: add patient dashboard

fix: validate refresh token

docs: update deployment guide
```

Bad:

```text
Added dashboard

fixed bug

changes

misc

update

final

work in progress
```

---

# Commit Summary Guidelines

A good summary should describe the completed change.

Preferred verbs include:

- add
- implement
- create
- update
- remove
- rename
- validate
- optimize
- simplify
- improve
- configure
- document
- replace
- migrate

Examples:

```text
feat: add trial eligibility endpoint

fix: validate patient age

refactor: simplify JWT service

docs: document authentication flow
```

---

# Commit Body

A commit body is optional.

It should be included when additional context improves understanding.

Recommended structure:

```text
feat: implement patient search

Add patient search by name and identifier.

The endpoint now supports pagination and
case-insensitive matching.

Resolves MED-24.
```

The body should explain:

- Why the change exists.
- Important implementation decisions.
- Architectural implications.
- Migration requirements, if any.

The body should not repeat information already present in the summary.

---

# Breaking Changes

Breaking changes shall be explicitly identified.

Example:

```text
feat!: replace JWT format

BREAKING CHANGE:
Authentication tokens generated by previous
versions are no longer accepted.
```

Breaking changes require:

- Documentation update.
- Version increment.
- Migration guidance.

---

# Atomic Commits

Commits shall be atomic.

An atomic commit contains one logical change.

Examples of atomic commits:

- Add JWT authentication.
- Fix Redis connection retry.
- Update Kubernetes deployment.
- Rename patient DTO.

Examples of non-atomic commits:

- Add authentication.
- Fix dashboard.
- Update README.
- Upgrade Spring Boot.

These should be committed separately.

---

# Commit Ordering

When multiple commits are required, they should follow a logical progression.

Example:

```text
feat: create patient entity

feat: implement patient repository

feat: add patient service

feat: expose patient API

test: add patient API tests

docs: document patient endpoints
```

Each commit should leave the repository in a buildable state.

---

# Commit Frequency

Developers should commit frequently.

Recommended guidance:

- Complete one logical task.
- Validate locally.
- Commit.

Very large commits reduce review quality and increase merge conflicts.

Very small commits with no logical value should also be avoided.

---

# Commit Examples

## Feature

```text
feat: implement eligibility scoring
```

---

## Bug Fix

```text
fix: prevent duplicate trial creation
```

---

## Documentation

```text
docs: add Kubernetes deployment guide
```

---

## Refactoring

```text
refactor: extract matching strategy interface
```

---

## Performance

```text
perf: reduce vector search latency
```

---

## Testing

```text
test: add integration tests for authentication
```

---

## Build

```text
build: upgrade PostgreSQL driver
```

---

## CI

```text
ci: configure container image scanning
```

---

## Chore

```text
chore: remove deprecated Docker Compose file
```

---

## Revert

```text
revert: remove experimental caching layer
```

---

---

# Commit Anti-Patterns

The following commit practices are prohibited because they reduce repository readability, complicate debugging, and weaken project history.

## Vague Commit Messages

Examples:

```text
update

changes

fix

work

final

done

temp

misc
```

These messages provide no meaningful information about the change.

---

## Multiple Unrelated Changes

A single commit shall not contain unrelated work.

Incorrect:

```text
feat: add JWT authentication

- Update README
- Upgrade Spring Boot
- Fix Redis connection
- Rename Docker image
```

Instead, create separate commits for each logical change.

---

## Generated Files

Generated artifacts should not be committed unless they are intentionally version controlled.

Examples include:

- Build output
- Temporary files
- IDE metadata
- Local caches
- Compiled binaries

Exceptions must be documented.

---

## Broken Commits

A commit shall never intentionally leave the repository in a broken state.

Every commit should:

- Build successfully.
- Pass applicable local validation.
- Preserve repository consistency.

---

## Temporary Commits

Temporary commit messages are prohibited.

Examples:

```text
temp

wip

trying

test

backup

123

asdf
```

If work is incomplete, continue development on the branch instead of creating meaningless commits.

---

# Repository History Standards

Repository history should remain:

- Understandable
- Searchable
- Predictable
- Traceable

Each commit should clearly communicate:

- What changed
- Why it changed

Developers should be able to understand repository history without reading the implementation.

---

# Commit Granularity

Commit size should reflect one logical engineering task.

Recommended examples:

- Add one API endpoint
- Fix one authentication issue
- Create one database migration
- Implement one feature
- Update one deployment configuration

Avoid combining unrelated responsibilities.

---

# Commit Ownership

Every commit should have one identifiable author responsible for the change.

Co-authored commits are acceptable when collaboration is documented using Git's standard `Co-authored-by` trailer.

Commit authors are responsible for:

- Code quality
- Documentation updates
- Testing performed
- Repository standard compliance

---

# Repository History Maintenance

Repository history should remain clean.

Practices include:

- Squash feature branch commits before merging.
- Remove obsolete branches after merge.
- Avoid unnecessary merge commits.
- Use descriptive commit messages.
- Revert commits rather than rewriting published history.

History should accurately represent the evolution of the project.

---

# Commit Checklist

Before creating a commit, verify:

- [ ] The commit represents one logical change.
- [ ] The summary follows the required format.
- [ ] The correct commit type is used.
- [ ] The repository builds successfully.
- [ ] Required tests have been executed.
- [ ] Documentation has been updated where necessary.
- [ ] No secrets or sensitive information are included.
- [ ] Temporary or generated files are excluded.
- [ ] The commit message clearly describes the change.

---

# Related Documents

This document complements:

- `docs/standards/repository-standards.md`
- `docs/standards/git-workflow.md`
- `docs/standards/definition-of-done.md`

Implementation guidance is provided by:

- `docs/standards/java-style-guide.md`
- `docs/standards/python-style-guide.md`
- `docs/standards/frontend-style-guide.md`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial commit convention standard. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All commits to the MedMatch repository shall comply with the conventions defined within this document.

---

**End of Document**