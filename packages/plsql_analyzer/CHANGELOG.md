# Changelog

All notable changes to the PL/SQL Analyzer package will be documented in this file.

## [Unreleased] - 2026-02-02

### Changed
- Performance optimization: Optimized directory traversal in `ExtractionWorkflow` by replacing multiple redundant `rglob` calls with a single traversal and in-memory filtering.
- Performance optimization: Changed list membership checks to set membership checks in `FileHelpers.get_processed_fpath` and `FileHelpers.derive_package_name_from_path` for O(1) complexity.
