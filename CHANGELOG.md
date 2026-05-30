# Changelog

All notable changes to BlueCrack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-30

### Added
- Glassmorphism dark theme with gradient accents
- Live stats dashboard (elapsed time, speed, ETA, hit counter)
- Success-string validation in GUI mode
- Max attempts limiter
- Continue-after-success mode for multi-user testing
- Export log to file button
- JSON session report auto-generation
- Retry budget per credential combo (max 3)
- Thread-safe credential tracking
- Graceful WebDriver restart with backoff
- URL redirect detection heuristic
- Colored CLI output with progress counter
- CLI flags: --max-attempts, --continue-after-success, --output, --json-report
- Demo server: multiple accounts, CSRF simulation, JSON API endpoint
- Demo server: configurable rate limits via CLI
- CHANGELOG.md

### Changed
- Complete GUI redesign with modern glassmorphism aesthetic
- Improved engine reliability with sentinel-based queue termination
- Deduplicated JavaScript snippets and Chrome options builder
- Pinned dependency versions in requirements.txt
- Updated README with comprehensive documentation

### Fixed
- Thread-safety issues with shared `found` state (now uses threading.Event)
- Infinite retry loops on element lookup failures
- Bare except clauses replaced with proper exception handling
- Race conditions in Queue.empty() checks

## [1.0.0] - 2025-01-01

### Added
- Initial release with GUI and CLI modes
- Selenium-based browser automation
- PyQt6 desktop interface
- CUPP wordlist generator integration
- Number sequence generator
- Tor proxy support
- Auto CSS selector detection
