# Copilot Instructions for this repository

This repository is a computer engineering capstone project.

The goal is to build a simple, working, submission-ready web application with minimum viable scope.

## Project summary
- Project name: Dijitalleştirilmiş Otosanayi
- Purpose: build a web application that creates a digital bridge between auto repair businesses and customers
- Main roles:
  - customer
  - business owner
  - admin

## Core features
- business listing
- business detail page
- review and rating system
- average service price information
- work order creation
- work order status tracking
- register / login / JWT authentication
- role-based access control

## Tech stack
- Backend: FastAPI
- Frontend: React
- Database: PostgreSQL
- Auth: JWT

## Architecture preferences
- Keep frontend, backend, and database concerns separated.
- Preserve the existing project structure unless there is a strong reason to change it.
- Prefer simple, clear, beginner-friendly code over clever or overly abstract code.
- Avoid unnecessary libraries, patterns, and large refactors.

## Working style
- First provide a short plan.
- Before writing code, list the files that will change.
- Make small, minimal, controlled changes.
- Do not rewrite large parts of the project unless explicitly requested.
- Do not work on backend and frontend in the same step unless explicitly requested.
- Focus on one task at a time.
- Prefer step-by-step progress that is easy to verify.
- After suggesting code changes, explain briefly why each change is needed.
- End with a short verification checklist.
- Suggest a commit message at the end.
- Assume the user wants to push after every commit.

## Scope control
- Prioritize minimum viable delivery.
- Do not add extra features outside the defined scope unless explicitly requested.
- Do not over-engineer the project.
- Prefer completion and clarity over perfection.

## Guidance style
- Be practical and direct.
- Assume the user is still learning.
- Give beginner-friendly explanations when needed.
- When debugging, start with the most likely and simplest cause.
- When proposing commands, make them easy to run in VS Code terminal on Windows PowerShell.

## Project context references
When useful, consult these files in the repository:
- `docs/project_brief_for_copilot.md`
- `docs/current_status.md`
- `docs/working_rules.md`