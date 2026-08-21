# Frontend Style Guide

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Frontend Style Guide |
| Document ID | FRONTEND-STD-001 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | All Frontend Applications |
| Classification | Engineering Standard |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document defines the engineering standards for developing frontend applications within the MedMatch platform.

Its objective is to establish consistent architectural patterns, component organization, design principles, coding conventions, accessibility requirements, and implementation practices across all React applications.

Following these standards improves maintainability, scalability, usability, accessibility, consistency, and developer productivity.

---

# Scope

These standards apply to every frontend application within the MedMatch repository.

Examples include:

- Web Application
- Administrative Portal
- Patient Portal
- Sponsor Portal
- Future React Applications

These standards apply to:

- Production code
- Test code
- Styling
- Assets
- Configuration
- Build tooling
- Shared component libraries

Unless explicitly documented, all frontend code shall comply with this guide.

---

# Design Philosophy

The MedMatch frontend shall prioritize:

- Simplicity
- Consistency
- Accessibility
- Responsiveness
- Reusability
- Maintainability
- Performance
- Security
- User Experience

The interface shall emphasize clarity over decoration.

Visual consistency shall be maintained across all user roles while allowing role-specific functionality.

Every screen shall appear to belong to the same application regardless of the authenticated user's role.

---

# Technology Stack

The frontend shall use the following technologies.

| Category | Standard |
|----------|----------|
| Framework | React 19 |
| Language | TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS v4 |
| UI Library | shadcn/ui |
| Icons | Lucide React |
| Routing | React Router |
| Server State | TanStack Query |
| Forms | React Hook Form |
| Validation | Zod |
| HTTP Client | Axios |
| Charts | Recharts |
| Animation | Framer Motion (where appropriate) |

Additional libraries require architectural approval.

---

# Project Structure

Every frontend application shall follow the same directory structure.

```text
frontend/
│
├── public/
│
├── src/
│   ├── app/
│   ├── assets/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── layouts/
│   ├── lib/
│   ├── routes/
│   ├── services/
│   ├── store/
│   ├── styles/
│   ├── types/
│   ├── utils/
│   ├── App.tsx
│   └── main.tsx
│
├── package.json
├── vite.config.ts
├── tsconfig.json
├── eslint.config.js
├── components.json
└── README.md
```

Additional directories shall only be introduced when justified by project requirements.

---

# Package Organization

The frontend shall organize source code by responsibility.

Example:

```text
src/

├── app
├── assets
├── components
├── features
├── hooks
├── layouts
├── lib
├── routes
├── services
├── store
├── styles
├── types
└── utils
```

Packages shall remain cohesive and independent.

---

# Package Responsibilities

| Package | Responsibility |
|----------|----------------|
| app | Application initialization |
| assets | Static assets |
| components | Reusable UI components |
| features | Feature modules |
| hooks | Custom React hooks |
| layouts | Shared layouts |
| lib | Third-party configuration |
| routes | Route definitions |
| services | API clients |
| store | Global state |
| styles | Global styles |
| types | Shared TypeScript types |
| utils | Stateless helper functions |

Responsibilities shall not overlap.

---

# Naming Conventions

The following naming conventions are mandatory.

| Element | Convention |
|----------|------------|
| Folder | kebab-case |
| Component | PascalCase |
| Hook | useCamelCase |
| Type | PascalCase |
| Interface | PascalCase |
| Enum | PascalCase |
| Enum Value | UPPER_SNAKE_CASE |
| Constant | UPPER_SNAKE_CASE |
| Utility Function | camelCase |
| File | kebab-case |

Names shall describe business intent rather than implementation details.

Abbreviations shall be avoided unless universally understood.

---

# Layer Responsibilities

The frontend shall follow a layered architecture.

```text
Pages

↓

Features

↓

Shared Components

↓

Services

↓

Backend APIs
```

Each layer has one primary responsibility.

Business logic shall remain inside feature modules.

Reusable presentation logic shall remain inside shared components.

Service modules shall encapsulate communication with backend APIs.

Layer boundaries shall remain explicit.

---

# React Principles

Frontend development shall follow these principles.

- Functional components only.
- Composition over inheritance.
- Reusable UI.
- Declarative rendering.
- Predictable state.
- Explicit data flow.
- Minimal prop drilling.
- Separation of concerns.
- Accessibility by default.
- Performance by design.

Components shall remain small, focused, and independently testable.

Business logic shall not be duplicated across components.

---

# Related Documents

This guide complements:

- `docs/standards/repository-standards.md`
- `docs/standards/api-guidelines.md`
- `docs/standards/java-style-guide.md`
- `docs/standards/python-style-guide.md`
- `docs/standards/definition-of-done.md`

Implementation quality requirements are defined by the Definition of Done.

---

---

# Component Standards

Components are the fundamental building blocks of the frontend.

Every component shall have one clear responsibility.

Components shall be reusable, composable, accessible, and independently testable.

---

## Component Categories

Components shall belong to one of the following categories.

| Category | Responsibility |
|----------|----------------|
| UI | Generic reusable components |
| Layout | Page layouts and navigation |
| Feature | Business-specific components |
| Shared | Components reused across features |
| Chart | Data visualization |
| Form | Form controls and form composition |
| Feedback | Alerts, loaders, dialogs, notifications |

A component shall belong to one category only.

---

## Component Organization

Example:

```text
components/

├── ui/
├── layout/
├── charts/
├── forms/
├── feedback/
└── shared/
```

Feature-specific components shall remain inside their feature module.

---

## Component Design

Components should:

- Have one responsibility.
- Accept typed props.
- Avoid duplicated logic.
- Be reusable.
- Remain stateless where practical.

Large components should be decomposed into smaller components.

---

## Component Naming

Component names shall use PascalCase.

Examples:

```text
DashboardCard

PatientTable

TrialStatusBadge

HospitalSelector

MatchConfidenceChart
```

Generic names such as:

```text
Card1

Table2

Widget

Box
```

shall not be used.

---

# Design System

The application shall use one shared design system.

The design system defines visual consistency across the entire platform.

No feature shall introduce independent styling rules.

---

## Colors

Semantic colors shall be used instead of arbitrary color values.

Examples:

```text
Primary

Secondary

Success

Warning

Danger

Info

Muted

Background

Foreground

Border
```

Colors shall be defined centrally.

Hardcoded hexadecimal values inside components are prohibited.

---

## Typography

Typography shall follow a consistent scale.

Examples:

| Element | Usage |
|----------|-------|
| Display | Hero sections |
| H1 | Page title |
| H2 | Section title |
| H3 | Card title |
| Body | Standard content |
| Small | Supporting information |
| Caption | Metadata |

Font sizes shall remain consistent throughout the application.

---

## Spacing

Spacing shall use a consistent spacing scale.

Examples:

```text
4px

8px

12px

16px

24px

32px

48px

64px
```

Arbitrary spacing values shall be avoided.

---

## Border Radius

Border radius shall follow one scale.

Examples:

```text
Small

Medium

Large

Full
```

Different components shall not invent independent radius values.

---

## Shadows

Shadow usage shall remain subtle.

Examples:

- Card shadow
- Dropdown shadow
- Modal shadow

Heavy shadows shall be avoided.

---

## Icons

Lucide React shall be the standard icon library.

Icons should:

- Match adjacent typography.
- Maintain consistent sizing.
- Represent actions clearly.

Decorative icons shall not replace labels.

---

# Layout Standards

Layouts define the structural organization of pages.

Layouts shall remain independent from business logic.

---

## Layout Types

The application shall provide standardized layouts.

Examples:

```text
Public Layout

Authentication Layout

Dashboard Layout

Error Layout
```

Every page shall use an appropriate layout.

---

## Dashboard Layout

Dashboard pages shall contain:

- Sidebar
- Top Navigation
- Main Content
- Footer (where appropriate)

Role-specific navigation shall be configured through data rather than duplicated layouts.

---

## Responsive Design

The application shall support:

- Desktop
- Laptop
- Tablet
- Mobile

Layouts shall adapt without changing business functionality.

---

# Routing Standards

Routing shall be centralized.

Routes shall remain independent from feature implementation.

---

## Route Organization

Example:

```text
routes/

index.tsx

public-routes.tsx

protected-routes.tsx
```

Routing logic shall not be scattered throughout feature modules.

---

## Route Categories

Routes shall be categorized as:

- Public
- Authenticated
- Role-based
- Error

Authorization checks shall occur before rendering protected content.

---

## Nested Routes

Nested routes shall be used where hierarchical layouts exist.

Example:

```text
Dashboard

↓

Patients

↓

Patient Details
```

Nested routing shall reduce duplicated layout code.

---

# State Management

State shall be categorized by scope.

The smallest appropriate scope shall always be chosen.

---

## Local State

Local state belongs inside components.

Use:

```text
useState

useReducer
```

Local state shall not be promoted unnecessarily.

---

## Server State

Server state shall use TanStack Query.

Examples:

- API responses
- Pagination
- Search results
- Trial data

Server state shall not be duplicated inside global stores.

---

## Global State

Global state should remain minimal.

Examples:

- Current user
- Theme
- Authentication
- Notifications

Business data shall not be stored globally unless required.

---

# Custom Hooks

Reusable logic shall be extracted into custom hooks.

Hooks encapsulate behavior rather than presentation.

---

## Hook Naming

Hooks shall begin with:

```text
use
```

Examples:

```text
useAuth

useTrials

usePagination

useDebounce

usePermissions
```

---

## Hook Responsibilities

Hooks may:

- Manage state.
- Perform API interactions.
- Encapsulate reusable logic.
- Coordinate side effects.

Hooks shall not render UI.

---

# API Layer

Communication with backend services shall remain centralized.

Components shall never perform HTTP requests directly.

---

## API Organization

Example:

```text
services/

auth/

patients/

trials/

matching/

reports/
```

Each module shall communicate with one backend resource.

---

## HTTP Client

Axios shall be the standard HTTP client.

A shared Axios instance shall configure:

- Base URL
- Authentication
- Interceptors
- Error handling
- Timeouts

Application code shall not repeatedly configure HTTP behavior.

---

## React Query

All server state shall be managed using TanStack Query.

Queries shall define:

- Query key
- Fetch function
- Retry policy
- Cache duration
- Invalidation strategy

Manual state synchronization shall be avoided whenever possible.

---

---

# Form Standards

Forms are the primary mechanism for user input.

Forms shall be:

- Accessible
- Predictable
- Consistent
- Fully validated
- Easy to complete

Every form shall use the same implementation approach throughout the application.

---

## Form Library

The standard form stack is:

- React Hook Form
- Zod
- shadcn/ui Form Components

Alternative form libraries shall not be introduced without architectural approval.

---

## Form Structure

Every form shall contain:

- Title
- Description (when helpful)
- Clearly labeled fields
- Validation messages
- Submit action
- Cancel action (when applicable)

Field ordering shall follow the natural workflow of the user.

---

## Form Validation

Validation shall occur using Zod schemas.

Validation should include:

- Required fields
- Length constraints
- Numeric ranges
- Date validation
- Email validation
- File validation
- Business-specific rules

Validation shall occur before API submission whenever possible.

---

## Validation Feedback

Validation messages shall:

- Be displayed adjacent to the relevant field.
- Clearly describe the problem.
- Explain how to resolve the issue.

Error messages shall never expose technical implementation details.

---

## Submit Behavior

During submission:

- Inputs should be disabled when appropriate.
- Submit buttons shall display loading indicators.
- Duplicate submissions shall be prevented.

Users shall always receive feedback indicating that processing is occurring.

---

# Table Standards

Tables present structured business data.

Every table shall remain readable regardless of data volume.

---

## Standard Table Features

Business tables should support:

- Pagination
- Sorting
- Filtering
- Searching
- Row selection (when applicable)
- Responsive layout

Feature availability depends on business requirements.

---

## Column Design

Columns shall:

- Use meaningful headers.
- Display formatted values.
- Maintain consistent alignment.
- Avoid unnecessary width.

Numeric values should be right aligned.

Text values should be left aligned.

---

## Row Actions

Actions should appear consistently.

Examples:

- View
- Edit
- Delete
- Download
- Export

Destructive actions shall require confirmation.

---

## Empty Tables

When no records exist, tables shall display an informative empty state.

Example:

```text
No patients found.

Create a patient to begin.
```

Empty tables shall not appear broken.

---

# Chart Standards

Charts communicate trends and analytical information.

Charts shall support understanding rather than decoration.

---

## Supported Charts

Approved chart types include:

- Line Chart
- Area Chart
- Bar Chart
- Pie Chart
- Donut Chart
- Stacked Bar Chart

Additional chart types require justification.

---

## Chart Library

Recharts is the standard chart library.

All dashboards shall use the shared chart components.

---

## Chart Design

Charts should:

- Display titles.
- Display legends.
- Display tooltips.
- Use semantic colors.
- Remain responsive.

Decorative effects shall be minimized.

---

## Data Presentation

Charts shall:

- Label axes clearly.
- Format values consistently.
- Avoid misleading scales.
- Handle empty datasets gracefully.

Charts shall prioritize accuracy over visual complexity.

---

# Loading States

Loading states communicate that work is in progress.

Every asynchronous page shall provide loading feedback.

---

## Skeleton Loaders

Skeleton components are preferred over generic spinners.

Skeletons should approximate the final layout.

Examples:

- Dashboard cards
- Tables
- Charts
- Forms
- Detail pages

---

## Progress Indicators

Long-running operations should provide progress indicators where practical.

Examples:

- File upload
- Trial processing
- AI matching
- Report generation

Users should understand that processing is continuing.

---

# Empty States

Empty states shall explain why no information is displayed.

Each empty state should include:

- Icon
- Title
- Description
- Primary action (when appropriate)

Example:

```text
No Clinical Trials

Upload your first trial to begin matching patients.
```

---

# Error States

Errors shall be presented consistently.

Every error screen should include:

- Error title
- Explanation
- Recovery action

Examples:

- Retry
- Return Home
- Refresh
- Contact Administrator

Users should always have a clear next step.

---

# Feedback Components

Feedback communicates application status.

Standard feedback components include:

- Toasts
- Alerts
- Dialogs
- Confirmation Modals
- Progress Indicators
- Badges

Each feedback component shall have one clear purpose.

---

## Toast Notifications

Toasts should communicate:

- Success
- Information
- Warning
- Error

Toasts shall be concise.

They shall not replace required confirmation dialogs.

---

## Confirmation Dialogs

Confirmation dialogs shall be used for destructive actions.

Examples:

- Delete patient
- Delete trial
- Remove user
- Reset configuration

Dialogs shall clearly describe the consequence of the action.

---

# Accessibility Standards

Accessibility is a core engineering requirement.

Accessibility shall be considered during implementation rather than added afterward.

---

## Keyboard Navigation

Every interactive component shall support keyboard navigation.

Examples include:

- Forms
- Menus
- Dialogs
- Tables
- Dropdowns

Keyboard users shall have access to all application functionality.

---

## Semantic HTML

Semantic HTML elements shall be preferred.

Examples:

- button
- nav
- header
- main
- section
- article
- footer

Generic containers shall not replace semantic elements unnecessarily.

---

## Labels

Every input shall have an associated label.

Placeholder text shall not replace labels.

---

## Focus Management

Interactive components shall display a visible focus indicator.

Focus order shall follow the visual reading order.

Dialogs shall trap focus while open.

---

## Color Usage

Color shall not be the sole method of communicating information.

Status indicators should combine:

- Color
- Text
- Icons

This improves accessibility for users with color vision deficiencies.

---

## Responsive Accessibility

Accessibility requirements apply equally across:

- Desktop
- Tablet
- Mobile

Responsive layouts shall preserve usability and keyboard accessibility.

---

---

# Performance Standards

Frontend performance is a core quality attribute.

Applications shall remain responsive under expected workloads.

Performance optimizations shall preserve readability and maintainability.

---

## Code Splitting

Large application modules shall be lazy loaded.

Examples include:

- Dashboard
- Reports
- Administration
- Trial Management
- Analytics

React lazy loading shall be used where appropriate.

---

## Lazy Loading

The following resources should be loaded lazily when practical:

- Routes
- Large components
- Charts
- Images
- Feature modules

Critical application functionality shall remain immediately available.

---

## Memoization

Memoization shall be applied only when measurable performance benefits exist.

Approved React APIs include:

- React.memo
- useMemo
- useCallback

Premature memoization shall be avoided.

---

## Rendering

Components should avoid unnecessary re-renders.

Examples:

- Stable props
- Stable callbacks
- Stable context values

Rendering behavior should remain predictable.

---

## Images

Images should:

- Use appropriate formats.
- Be optimized before deployment.
- Specify dimensions.
- Support responsive rendering.
- Use lazy loading where appropriate.

Large unoptimized assets shall not be committed.

---

## Lists

Large datasets should use virtualization when rendering performance becomes a concern.

Examples include:

- Patient lists
- Trial tables
- Audit logs
- Notifications

---

# Security Practices

Frontend security complements backend security.

Sensitive business rules shall always be enforced by the backend.

---

## Authentication

Authentication shall use secure token handling.

Frontend responsibilities include:

- Sending tokens
- Refreshing tokens
- Handling expiration
- Clearing authentication state during logout

Authorization decisions remain the responsibility of the backend.

---

## Protected Routes

Protected routes shall verify authentication before rendering.

Unauthorized users shall be redirected appropriately.

Protected UI elements shall not replace backend authorization.

---

## Input Handling

User input shall always be validated.

Frontend validation improves user experience.

Backend validation remains authoritative.

---

## Sensitive Data

Sensitive information shall never be:

- Stored in source code.
- Logged in production.
- Embedded in client-side configuration.
- Exposed through debugging utilities.

Examples include:

- JWT secrets
- API keys
- Database credentials
- Private URLs

---

## Browser Storage

Only appropriate data shall be stored in browser storage.

Examples:

- UI preferences
- Theme
- Non-sensitive application state

Sensitive information shall follow the project's authentication strategy.

---

# Testing Standards

Frontend code shall be designed to be independently testable.

Testing verifies correctness, usability, and regression prevention.

---

## Component Testing

Components should be tested independently.

Tests should verify:

- Rendering
- User interaction
- Conditional rendering
- Accessibility behavior

---

## Integration Testing

Integration tests should verify:

- Feature workflows
- Form submission
- API interaction
- Navigation
- Error handling

---

## End-to-End Testing

Critical business workflows should include end-to-end testing.

Examples:

- Login
- Upload trial
- Match patient
- Register user
- Review eligibility

---

## Test Organization

Production and test structures should mirror one another.

Example:

```text
features/

patients/

components/

PatientTable.tsx

tests/

PatientTable.test.tsx
```

---

# Code Smells

The following indicators suggest refactoring should be considered.

Examples:

- Large components
- Deep component nesting
- Excessive prop drilling
- Duplicate UI logic
- Duplicate API calls
- Large context providers
- Mixed presentation and business logic
- Excessive conditional rendering

Developers should address code smells before introducing new functionality whenever practical.

---

# Anti-Patterns

The following practices are prohibited.

---

## Business Logic Inside Components

Business logic belongs inside feature modules, services, or custom hooks.

Presentation components should remain focused on rendering.

---

## Direct HTTP Requests

Components shall not communicate directly with Axios.

All HTTP communication shall occur through the centralized service layer.

---

## Duplicate Styling

Styling patterns shall use the shared design system.

Feature modules shall not invent independent design rules.

---

## Large Components

Large components should be decomposed into smaller reusable components.

Each component should represent one primary responsibility.

---

## Global State Overuse

Global state shall remain minimal.

Only application-wide concerns belong in global stores.

Business data should use TanStack Query whenever appropriate.

---

## Inline Business Rules

Business rules shall not be embedded inside JSX.

Complex decision logic belongs in services or reusable hooks.

---

## Hardcoded Values

Avoid hardcoded:

- Colors
- Spacing
- Breakpoints
- Typography
- API URLs

Shared design tokens and configuration shall be used instead.

---

# Code Review Checklist

Before approving frontend code, verify:

## Architecture

- [ ] Project structure follows standards.
- [ ] Component responsibilities are clear.
- [ ] Feature boundaries are respected.

---

## Components

- [ ] Components are reusable.
- [ ] Props are typed.
- [ ] No duplicated UI logic.
- [ ] Components remain reasonably sized.

---

## API Integration

- [ ] API layer used correctly.
- [ ] React Query configured appropriately.
- [ ] Loading states implemented.
- [ ] Error states implemented.

---

## User Experience

- [ ] Responsive layout verified.
- [ ] Empty states implemented.
- [ ] Error states implemented.
- [ ] Loading states implemented.

---

## Accessibility

- [ ] Keyboard navigation supported.
- [ ] Semantic HTML used.
- [ ] Labels present.
- [ ] Focus management verified.
- [ ] Color is not the only indicator of state.

---

## Performance

- [ ] No unnecessary re-renders.
- [ ] Large modules lazy loaded.
- [ ] Images optimized.
- [ ] Memoization used only where justified.

---

## Security

- [ ] Sensitive information protected.
- [ ] Protected routes configured.
- [ ] Input validated.
- [ ] Authentication flow verified.

---

## Testing

- [ ] Component tests updated.
- [ ] Integration tests updated.
- [ ] Critical workflows tested.

---

## Documentation

- [ ] Documentation updated where required.
- [ ] Screenshots updated if documentation depends on UI changes.

---

# Related Documents

This guide complements:

- `docs/standards/repository-standards.md`
- `docs/standards/git-workflow.md`
- `docs/standards/commit-convention.md`
- `docs/standards/definition-of-done.md`
- `docs/standards/api-guidelines.md`
- `docs/standards/java-style-guide.md`
- `docs/standards/python-style-guide.md`

Design specifications and UX decisions belong in:

- `docs/architecture/`
- `docs/diagrams/`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial frontend engineering standard. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All frontend applications within the MedMatch platform shall comply with the standards defined in this document unless superseded by a later approved revision.

---

**End of Document**