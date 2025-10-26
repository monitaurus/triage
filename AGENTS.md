# Agents Contributing Guide

## Commands

* Dependencies are managed with `uv` and defined in `pyproject.toml`. Any new dependencies should be added there.

## Versioning

* Use git as versioning.
* Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Code

* New code should follow the existing style (f-strings, type hints, `rich` for output).
* Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.

## Others

* product requirements could be found in file `docs/PRD.md`
