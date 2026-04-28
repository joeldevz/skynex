## Goal

Introduce a versioned CLI installer named `skynex` that gives users one consistent way to install and manage this skills repository and other supported packages or repositories such as `neurox` across Claude Code and OpenCode. This matters because the current install flow is repo-specific and tool-specific, while the product now needs a reusable, interactive installer that can validate prerequisites up front, let users choose versions intentionally, and keep a durable record of what was requested versus what was actually installed.

## Users

- **Primary users:** developers and AI power users who want to install or update shared skill packages into Claude Code and/or OpenCode.
- **Secondary users:** maintainers of installable repos/packages who need a predictable way to distribute versioned releases.
- **Indirectly affected:** teams relying on consistent local AI agent behavior, especially where Neurox-backed workflows are mandatory.
- **System actors:** supported install targets (Claude Code and OpenCode), installable packages/repos (this repo, `neurox`, future compatible packages), and local configuration state represented by `skills.config.json` and `skills.lock.json`.

## Behavior

### Primary workflows

1. **Interactive install**
   - The user runs `skynex` and is guided through an interactive flow.
   - The user selects one or more installable packages/repos.
   - The user selects a target environment: Claude Code, OpenCode, or both.
   - The user selects a repository/package version, or accepts the default suggested version.
   - The installer performs preflight validations before applying changes.
   - If validations pass, the installer installs the selected package version for the selected target(s).

2. **Automatic mode**
   - The user runs the same command in a non-interruptive mode.
   - The installer uses explicit inputs and/or stored defaults to choose package, version, and target.
   - The installer still performs the same validations and tracking as the interactive flow.

3. **Version tracking**
   - The installer records the user’s intended package selections and target preferences in `skills.config.json`.
   - The installer records the resolved installed versions and related install state in `skills.lock.json`.
   - Versioning is tracked at the whole repository/package level, not per individual skill.

4. **Cross-target installation**
   - One command supports Claude Code and OpenCode without requiring separate installer products.
   - The user can install the same package version into either target independently or both together.
   - The experience stays unified even when target-specific validations or outputs differ.

5. **Preflight validation**
   - Before installation, the installer checks whether the selected package is installable for the selected target(s).
   - It verifies required local prerequisites, detects incompatible or unsupported states, and surfaces actionable issues before making changes.
   - Because Neurox is mandatory across the system, the installer treats missing or incompatible Neurox requirements as blocking validation failures where applicable.

## Acceptance Criteria

- A user can use `skynex` to install this repository into Claude Code, OpenCode, or both from one product entry point.
- A user can use the same CLI to install another supported package or repository, such as `neurox`, without switching to a different installer.
- GIVEN the user starts an interactive install, WHEN the CLI runs, THEN it prompts for package/repository choice, target choice, and version choice before installation proceeds.
- GIVEN the user starts automatic mode, WHEN required inputs or stored defaults are available, THEN the install proceeds without interactive prompts.
- GIVEN a version is selected, WHEN installation completes successfully, THEN the installed state is recorded at package/repository level in `skills.lock.json`.
- GIVEN the user has package or target preferences, WHEN installation completes, THEN those preferences are persisted in `skills.config.json`.
- GIVEN the selected package supports both Claude Code and OpenCode, WHEN the user chooses either or both targets, THEN the CLI handles that through the same command surface.
- GIVEN preflight validation fails, WHEN the installer detects the issue, THEN it stops before applying install changes and explains what must be corrected.
- GIVEN Neurox is required for the selected install path, WHEN Neurox prerequisites are missing or incompatible, THEN the installer reports that as a validation failure.
- GIVEN the repo/package version changes between installs, WHEN the user installs again, THEN the tracked lock state reflects the newly resolved installed version.
- The MVP does not require rollback support in order to be considered complete.

## Edge Cases

- The user selects a package/repo that is known to the CLI but is not compatible with the chosen target.
- The selected version does not exist, is unavailable, or cannot be resolved consistently.
- The same package is already installed at the requested version.
- The package is already installed at a different version than the one requested.
- `skills.config.json` or `skills.lock.json` is missing, corrupted, or contains conflicting data.
- The user chooses both Claude Code and OpenCode, but only one target passes validation.
- Required local dependencies, permissions, network access, or filesystem paths are unavailable.
- Neurox is missing, misconfigured, or incompatible with the selected install flow.
- Automatic mode is invoked without enough inputs or defaults to resolve package, target, or version safely.
- Multiple installable repos/packages introduce conflicting target requirements or incompatible version expectations.

## Out of Scope

- Rollback, uninstall, or recovery workflows.
- Per-skill versioning, pinning, or selective skill-level installs.
- Background auto-updates or silent self-healing.
- A package publishing workflow or release management system.
- Support for additional install targets beyond Claude Code and OpenCode in the MVP.
- Arbitrary third-party repositories with no compatibility contract.
- Deep configuration editing beyond the installer-owned `skills.config.json` and `skills.lock.json` records.

## Constraints implied by supporting multiple installable repos/packages

- The CLI must distinguish package identity, selected version, and target compatibility at the package/repository level.
- The user experience must stay consistent even when different packages have different target-specific install behaviors.
- Config and lock state must represent multiple installed packages/repos without assuming this repo is the only managed package.
- Validation must happen before install so unsupported package-target combinations fail clearly instead of partially applying changes.
- The product must preserve a centralized command experience even though installation outcomes differ by target and package.
