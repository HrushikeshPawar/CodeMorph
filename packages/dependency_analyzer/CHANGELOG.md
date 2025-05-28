# Changelog

All notable changes to the Dependency Analyzer package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0] - 2025-05-28

### Added
- Comprehensive documentation update with README.md, CONFIGURATION.md, and API_REFERENCE.md
- Complete CLI command structure with command groups (init, build, analyze, visualize, query)
- TOML configuration system with Pydantic validation
- Node classification algorithms (hubs, utilities, bridges, orphans)
- Cycle detection and analysis capabilities
- Reachability analysis for impact assessment
- Enhanced visualization options with multiple engines
- Integrated subgraph creation and visualization
- Migration guide from legacy CLI commands

### Changed
- Restructured CLI interface using cyclopts framework
- Configuration system now uses TOML format instead of Python config files
- Improved error handling with detailed suggestions
- Enhanced logging system with multiple verbosity levels

### Improved
- Performance optimizations for large graph processing
- Better memory management with configurable graph formats
- Enhanced visualization with package-based color coding
- More robust parameter validation and error reporting

---

*Note: This changelog tracks changes from the comprehensive documentation update forward. For historical changes, refer to git commit history.*
