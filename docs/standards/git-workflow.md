# Git Workflow

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Git Workflow |
| Document ID | GIT-STD-001 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | Entire Repository |
| Classification | Engineering Standard |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document defines the Git workflow used throughout the MedMatch repository.

Its purpose is to ensure that every change follows a predictable lifecycle from initial development to production deployment.

A standardized workflow improves collaboration, simplifies reviews, reduces merge conflicts, and preserves repository stability.

This document governs branch usage, merge strategy, pull request workflow, release management, and repository maintenance.

---

# Scope

This workflow applies to all contributors and every repository component, including:

- Backend services
- Frontend
- Infrastructure
- Documentation
- Database migrations
- CI/CD configuration
- Monitoring
- Security
- Automation

No repository change is exempt unless explicitly approved through an Architecture Decision Record (ADR).

---

# Branching Strategy

The repository follows a trunk-based development model with controlled long-lived branches.

Long-lived branches:

```

main

develop

```

Short-lived branches:

```

feature/\*

bugfix/\*

hotfix/\*

release/\*

docs/\*

refactor/\*

```

The number of permanent branches shall remain minimal.

Long-lived branches represent stable integration points.

Short-lived branches represent isolated units of work.

---

# Branch Responsibilities

## main

Purpose

Production-ready code.

Characteristics

- Stable
- Fully tested
- Deployable
- Tagged for releases

Direct commits are prohibited.

Changes reach `main` only through approved pull requests.

---

## develop

Purpose

Primary integration branch.

Characteristics

- Active development
- Feature integration
- Continuous testing

Every new feature is merged into `develop` before eventually reaching `main`.

---

# Branch Lifecycle

Feature branches originate from:

```

develop

```

Bugfix branches originate from:

```

develop

```

Release branches originate from:

```

develop

```

Hotfix branches originate from:

```

main

```

Documentation branches originate from:

```

develop

```

Refactor branches originate from:

```

develop

```

After merge, short-lived branches shall be deleted.

---

# Branch Naming

Branch names shall follow the format:

```

<type>/<short-description>

```

Examples

```

feature/patient-dashboard

feature/trial-search

feature/jwt-refresh

bugfix/login-validation

bugfix/cache-key

docs/api-guidelines

docs/repository-standards

refactor/matching-service

release/v1.0.0

hotfix/security-patch

```

Branch names shall:

- use lowercase
- use hyphens
- clearly describe the work
- avoid ticket numbers unless required by project policy

---

# Branch Protection

The following protections apply.

## main

- Protected
- No force push
- No direct commit
- Pull Request required
- Review required
- CI must pass

---

## develop

- Protected
- Pull Request required
- CI must pass

---

Feature branches remain unprotected.

---

# Workflow Principles

The Git workflow follows these principles.

- Small changes are preferred over large changes.
- Every branch has one purpose.
- Every pull request addresses one concern.
- Repository history should remain understandable.
- Changes must be reviewable.
- Long-running branches are discouraged.
- Merge conflicts should be minimized through frequent synchronization.

---

---

# Feature Development Workflow

Every new feature shall be developed in an isolated feature branch.

Feature branches must originate from the latest `develop` branch.

Workflow:

```text
develop
    │
    ├── feature/patient-dashboard
    │
    ├── feature/trial-search
    │
    └── feature/auth-refresh
```

Feature branches shall:

- Implement one feature only.
- Remain short-lived.
- Be synchronized with `develop` regularly.
- Be deleted after merge.

A feature branch shall never be reused for another feature.

---

# Feature Development Process

The recommended workflow is:

1. Update local `develop`.
2. Create a new feature branch.
3. Implement the feature.
4. Execute local validation.
5. Commit logical changes.
6. Push the branch.
7. Open a Pull Request.
8. Address review comments.
9. Merge into `develop`.
10. Delete the feature branch.

Feature work shall not be committed directly to `develop`.

---

# Bug Fix Workflow

Bug fixes follow the same lifecycle as feature development.

Workflow:

```text
develop
      │
      └── bugfix/login-validation
```

A bug fix branch shall:

- Fix one issue.
- Include appropriate tests.
- Avoid unrelated refactoring.
- Preserve backward compatibility whenever possible.

After approval, the branch shall be merged into `develop` and deleted.

---

# Documentation Workflow

Documentation updates shall use dedicated documentation branches.

Example:

```text
docs/api-guidelines

docs/database-schema

docs/repository-standards
```

Documentation changes should accompany implementation whenever both are required.

Documentation-only changes should not include application code.

---

# Refactor Workflow

Refactoring shall occur in dedicated branches.

Example:

```text
refactor/matching-service
```

Refactoring shall not intentionally introduce new functionality.

Objectives include:

- Improving readability
- Reducing complexity
- Removing duplication
- Improving maintainability
- Improving architecture

Behavior shall remain unchanged.

---

# Release Workflow

Release branches prepare a stable release candidate.

Workflow:

```text
develop
      │
      └── release/v1.0.0
```

Release branches may include:

- Version updates
- Documentation updates
- Release notes
- Minor bug fixes

New features shall not be introduced into release branches.

Once approved:

```text
release
     │
     ├── merge → main
     │
     └── merge → develop
```

Both branches must contain identical release changes.

---

# Hotfix Workflow

Hotfix branches address production issues requiring immediate correction.

Workflow:

```text
main
   │
   └── hotfix/security-patch
```

Hotfix branches shall contain only the minimum required changes.

After validation:

```text
hotfix
     │
     ├── merge → main
     └── merge → develop
```

This ensures that production fixes are not lost during future development.

---

# Synchronizing with Develop

Feature branches should remain synchronized with `develop`.

Recommended process:

1. Fetch latest repository state.
2. Update local `develop`.
3. Merge or rebase onto the feature branch.
4. Resolve conflicts.
5. Continue development.

Frequent synchronization reduces merge complexity.

---

# Merge Strategy

The repository uses **Squash and Merge** for feature work.

Benefits include:

- Clean history
- One commit per completed feature
- Easier rollback
- Simpler release history

Merge commits are reserved for release and hotfix branches where historical context is valuable.

---

# Pull Request Lifecycle

Every Pull Request follows the same lifecycle.

```text
Feature Branch

↓

Push

↓

Open Pull Request

↓

Automated Validation

↓

Code Review

↓

Requested Changes (if needed)

↓

Approval

↓

Merge

↓

Delete Branch
```

No branch shall be merged without completing the required review process.

---

---

# Pull Request Workflow

Every change merged into a protected branch shall be introduced through a Pull Request (PR).

Direct commits to protected branches are prohibited.

A Pull Request shall represent one logical unit of work.

A Pull Request shall not combine unrelated features, bug fixes, refactoring, or documentation updates.

---

# Pull Request Requirements

Every Pull Request shall:

- Reference the associated branch.
- Contain a clear and descriptive title.
- Describe the purpose of the change.
- Summarize implementation details.
- Document any architectural impact.
- Identify breaking changes, if applicable.
- Include testing performed.
- Link relevant ADRs or documentation updates where applicable.

---

# Pull Request Size

Pull Requests should remain small enough for effective review.

Recommended guidelines:

| Size | Recommendation |
|------|----------------|
| < 300 lines | Preferred |
| 300–600 lines | Acceptable |
| > 600 lines | Consider splitting |

Generated files are excluded from these recommendations.

---

# Code Review Workflow

Every Pull Request shall undergo code review before merge.

The purpose of review is to improve:

- Correctness
- Maintainability
- Readability
- Architectural consistency
- Security
- Test quality
- Documentation quality

Code review is a collaborative engineering activity rather than an approval process.

---

# Code Review Checklist

Reviewers should verify:

## Architecture

- [ ] Repository standards are followed.
- [ ] Service boundaries remain intact.
- [ ] Dependency direction is correct.
- [ ] No architectural violations are introduced.

---

## Implementation

- [ ] Code is understandable.
- [ ] Responsibilities are clearly separated.
- [ ] No unnecessary complexity exists.
- [ ] Naming follows repository standards.
- [ ] Error handling is appropriate.

---

## Security

- [ ] Secrets are not committed.
- [ ] Authentication remains correct.
- [ ] Authorization remains correct.
- [ ] Sensitive data is protected.

---

## Testing

- [ ] Required tests exist.
- [ ] Existing tests pass.
- [ ] New functionality is covered.

---

## Documentation

- [ ] Documentation reflects implementation.
- [ ] API documentation is updated if required.
- [ ] ADR added if architecture changed.

---

# Conflict Resolution

Merge conflicts shall be resolved by the branch owner.

Conflict resolution should:

- Preserve intended functionality.
- Maintain repository standards.
- Keep commit history understandable.

After resolving conflicts:

1. Rebuild the affected components.
2. Execute applicable tests.
3. Push the updated branch.
4. Continue the review process.

---

# Repository Maintenance Workflow

Repository maintenance includes activities that improve the engineering quality of the repository without introducing new functionality.

Examples include:

- Dependency updates
- Documentation improvements
- Security updates
- Build improvements
- Infrastructure improvements
- CI/CD improvements
- Refactoring
- Repository cleanup

Maintenance work shall follow the same Pull Request workflow as feature development.

---

# Release Tagging

Every production release shall be tagged.

Tag format:

```text
vMAJOR.MINOR.PATCH
```

Examples:

```text
v1.0.0
v1.2.0
v2.0.0
```

Release tags shall correspond to commits on the `main` branch.

---

# Branch Cleanup

After successful merge:

- Delete the source branch.
- Remove obsolete local branches.
- Remove obsolete remote branches.

Long-lived inactive branches should be avoided.

---

# Emergency Changes

Emergency production fixes shall:

- Use a `hotfix/*` branch.
- Be limited to the minimum required change.
- Undergo expedited review where appropriate.
- Be merged into both `main` and `develop`.

Emergency changes do not bypass repository standards.

---

# Workflow Checklist

Before opening a Pull Request verify:

- [ ] Branch is based on the correct parent.
- [ ] Branch name follows conventions.
- [ ] Work addresses one logical concern.
- [ ] Local validation completed.
- [ ] Tests executed.
- [ ] Documentation updated where required.
- [ ] No merge conflicts remain.
- [ ] Repository standards are satisfied.

---

# Related Documents

This workflow is complemented by:

- `docs/standards/repository-standards.md`
- `docs/standards/commit-convention.md`
- `docs/standards/definition-of-done.md`
- `docs/standards/api-guidelines.md`

Language-specific implementation guidance is provided by:

- `docs/standards/java-style-guide.md`
- `docs/standards/python-style-guide.md`
- `docs/standards/frontend-style-guide.md`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial Git workflow standard. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All repository contributions shall follow this workflow unless superseded by a later approved revision.

---

**End of Document**