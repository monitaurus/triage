# Agents Contributing Guide

Follow these rules:

## Versioning & Commits
* Format commit messages using the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Code Generation & Tooling
* Use Context7 for code generation, setup, configuration, or API documentation. 
* Trigger Context7 MCP tools automatically to resolve library IDs and retrieve documentation.

## Project Architecture
* **Agent-First CLI**: Build tools for automation. 
* **No UIs**: Exclude Terminal UIs, interactive prompts, and standard logging. 
* **Use JSON**: Rely on argument-based subcommands and `--json` outputs.
* **Pure Go**: Avoid CGO bindings. 
* **Cross-Compile**: Maintain cross-compilation support.
