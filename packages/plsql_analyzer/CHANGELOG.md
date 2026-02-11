# Changelog

All notable changes to the PL/SQL Analyzer package will be documented in this file.

## [Unreleased] - 2026-02-02

### Changed
- Performance optimization: Optimized directory traversal in `ExtractionWorkflow` by replacing multiple redundant `rglob` calls with a single traversal and in-memory filtering.
- Performance optimization: Implemented bulk insert for PL/SQL code objects in `ExtractionWorkflow`, replacing N+1 inserts with `executemany` for significant speedup (measured ~37% improvement).
