# CodeMorph: `dependency_analyzer` - Advanced Graph Analysis Roadmap

## Document Version: 1.0
## Date: 2025-05-17

## Introduction

This document outlines the roadmap for implementing advanced graph analysis features within the `dependency_analyzer` package of the CodeMorph project. The goal of these features is to provide deep insights into legacy PL/SQL codebases, facilitating a more informed and efficient migration to Java SpringBoot. Features are prioritized based on their foundational nature, immediate value for migration tasks, and feasibility with current data structures.

## Ranking Scheme & Prioritization

Features are organized into tiers:

*   **Tier 1 (Foundational & High Immediate Value):** Core metrics and classifications that enable further analysis and offer quick wins.
*   **Tier 2 (Structural Insights & Grouping):** Features that help understand the macro-structure and logical groupings within the codebase.
*   **Tier 3 (Migration Strategy & Planning Aids):** Features directly supporting strategic decisions for the migration process.
*   **Tier 4 (Advanced/Future Enhancements):** More complex features, potentially requiring new data sources or significant algorithmic development.

---

## Tier 1: Foundational & High Immediate Value

### 1.1 Feature: Node Complexity Metrics

*   **Summary:** Calculate and store various complexity metrics for each `PLSQL_CodeObject` in the graph.
*   **Detailed Description:**
    *   **Needs:** To quantitatively assess the effort and risk associated with migrating individual PL/SQL objects. Provides data for prioritization and resource allocation.
    *   **Requirements:** Metrics should be derivable from the existing `PLSQL_CodeObject` data.
    *   **Details:**
        *   **Lines of Code (LOC):** Based on `clean_code`.
        *   **Number of Parameters:** Based on `parsed_parameters`.
        *   **Number of Outgoing Calls:** Based on `extracted_calls` (unique callees or total calls).
        *   **Approximate Cyclomatic Complexity (ACC):** A heuristic based on counting control flow keywords in `clean_code`.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create a new function `calculate_node_complexity_metrics(graph: nx.DiGraph) -> None`.
            *   This function will iterate through `graph.nodes(data=True)`.
            *   For each node, access `node_data['object']` (the `PLSQL_CodeObject`).
            *   Implement logic to calculate:
                *   LOC: `len(obj.clean_code.splitlines()) if obj.clean_code else 0`.
                *   NumParams: `len(obj.parsed_parameters)`.
                *   NumCallsMade: `len(obj.extracted_calls)`.
                *   ACC:
                    *   Define a list of decision-point keywords (e.g., `IF`, `ELSIF`, `CASE WHEN`, `LOOP`, `FOR`, `WHILE`, `EXCEPTION WHEN`).
                    *   Count occurrences of these (case-insensitive) in `obj.clean_code`. ACC = count + 1.
            *   Store these metrics as new attributes on the graph node itself (e.g., `graph.nodes[node_id]['loc'] = loc_value`).
        *   `packages/dependency_analyzer/src/dependency_analyzer/cli.py`:
            *   Modify `full_build` command to optionally calculate and store these metrics if a flag is provided.
            *   Potentially add a new CLI command `analyze metrics <graph_path>` to compute and update metrics on an existing graph.
    *   **Tools/Libraries:** Standard Python string methods, `re` module for ACC keyword counting.
    *   **Optimization:** ACC calculation on `clean_code` should be reasonably fast. Other metrics are direct lookups.
*   **Data Requirements:**
    *   **Current:** `PLSQL_CodeObject.clean_code`, `parsed_parameters`, `extracted_calls` are sufficient.
    *   **Missing:** None for these specific metrics.
*   **Pros:**
    *   Provides objective data for comparing object complexity.
    *   Forms the basis for more advanced analyses (critical paths, utility node identification).
    *   Easy to implement with existing data.
*   **Cons:**
    *   LOC and ACC are heuristic measures and may not perfectly reflect true logical complexity.
*   **Migration Use Case:**
    *   Identify highly complex objects that may require more refactoring or careful migration.
    *   Helps estimate migration effort per object.
    *   Sort objects by complexity to distribute workload or tackle challenging parts early/late.

---

### 1.2 Feature: Reachability Analysis (Ancestors/Descendants)

*   **Summary:** Determine all nodes reachable from a given node (descendants) and all nodes that can reach a given node (ancestors).
*   **Detailed Description:**
    *   **Needs:** Essential for understanding the ripple effect of changes and the scope of dependencies for any given PL/SQL object.
    *   **Requirements:** Basic graph traversal capabilities.
    *   **Details:** Provide functions to get sets of ancestor and descendant nodes, optionally within a certain depth.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create `get_descendants(graph: nx.DiGraph, source_node: str, depth_limit: Optional[int] = None) -> Set[str]`.
                *   Uses `nx.descendants(graph, source_node)` if `depth_limit` is None.
                *   If `depth_limit` is provided, use `nx.bfs_tree(graph, source_node, depth_limit=depth_limit).nodes()`.
            *   Create `get_ancestors(graph: nx.DiGraph, target_node: str, depth_limit: Optional[int] = None) -> Set[str]`.
                *   Uses `nx.ancestors(graph, target_node)` if `depth_limit` is None.
                *   If `depth_limit` is provided, use `nx.bfs_tree(graph.reverse(copy=False), target_node, depth_limit=depth_limit).nodes()`.
        *   `packages/dependency_analyzer/src/dependency_analyzer/cli.py`:
            *   Potentially add commands like `analyze reachability <graph_path> <node_id> [--downstream] [--upstream] [--depth N]`.
*   **Tools/Libraries:** `networkx`.
*   **Optimization:** NetworkX functions are generally optimized. `graph.reverse(copy=False)` avoids duplicating graph data for ancestor search.
*   **Data Requirements:**
    *   **Current:** Graph structure is sufficient.
    *   **Missing:** None.
*   **Pros:**
    *   Fundamental for impact analysis.
    *   Clear and unambiguous results.
*   **Cons:**
    *   For very dense graphs, the set of ancestors/descendants can be very large.
*   **Migration Use Case:**
    *   "If `PROC_A` is migrated and its interface changes, what are its `descendants` (direct and indirect PL/SQL callees that might be affected) and its `ancestors` (PL/SQL callers that need to be updated)?"

---

### 1.3 Feature: Execution Path Tracing

*   **Summary:** From a selected node, trace all (or simple) execution paths downstream, up to a certain depth or to specific targets.
*   **Detailed Description:**
    *   **Needs:** To understand the sequence of calls and the functional scope originating from a particular object.
    *   **Requirements:** Graph traversal and path reconstruction.
    *   **Details:** Find simple paths (no repeated nodes) or all paths up to a depth limit.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   The existing `find_all_paths(graph, source, target, cutoff)` is a good basis if a target is known.
            *   Create `trace_downstream_paths(graph: nx.DiGraph, source_node: str, depth_limit: Optional[int] = None, target_node: Optional[str] = None) -> List[List[str]]`.
                *   If `target_node` is provided, use `nx.all_simple_paths(graph, source_node, target_node, cutoff=depth_limit)`.
                *   If `target_node` is None, perform a DFS/BFS traversal up to `depth_limit` and reconstruct paths. `nx.dfs_edges(graph, source_node, depth_limit=depth_limit)` can be used to get edges; paths need reconstruction.
                *   Careful with cycles: focus on simple paths or depth-limited paths.
*   **Tools/Libraries:** `networkx`.
*   **Optimization:** `nx.all_simple_paths` can be expensive if many paths exist. Depth limiting is crucial.
*   **Data Requirements:**
    *   **Current:** Graph structure is sufficient.
    *   **Missing:** None.
*   **Pros:**
    *   Visualizes control flow.
    *   Helps understand the breadth and depth of a feature.
*   **Cons:**
    *   Can produce a very large number of paths, especially with cycles or high branching factors. Needs clear UI presentation and filtering.
*   **Migration Use Case:**
    *   "Show me all sequences of PL/SQL calls that occur if `ENTRY_POINT_PROC` is executed, to understand the full logic flow we need to replicate in Java."

---

### 1.4 Feature: Automated Node Classification

*   **Summary:** Automatically classify nodes into roles like Hubs, Connectors, Utilities, and Orphans based on graph metrics.
*   **Detailed Description:**
    *   **Needs:** To quickly identify architecturally significant objects or potential dead code without manual inspection of every node.
    *   **Requirements:** Calculation of various graph centrality measures and degree metrics. Node complexity metrics (from Feature 1.1) are beneficial for some classifications.
    *   **Details:**
        *   **Entry/Terminal Points:** Already implemented via `find_entry_points` and `find_terminal_nodes`.
        *   **Hubs/Connectors:** Nodes with high degree centrality, betweenness centrality, or PageRank.
        *   **Utility Nodes:** Nodes with high out-degree but relatively low internal complexity (uses Feature 1.1).
        *   **Orphaned Component Members:** Nodes belonging to small, weakly connected components.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create `classify_nodes(graph: nx.DiGraph, complexity_metrics_calculated: bool = True) -> None`.
            *   This function will:
                *   Calculate degree: `graph.degree()`, `graph.in_degree()`, `graph.out_degree()`.
                *   Calculate `nx.betweenness_centrality(graph, normalized=True)`. (Consider `k` for large graphs).
                *   Calculate `nx.pagerank(graph)`.
                *   Use `get_connected_components(graph, strongly_connected=False)` for orphans.
                *   Define thresholds (these might need to be configurable or adaptive, e.g., top X%):
                    *   `HUB_DEGREE_THRESHOLD`, `HUB_BETWEENNESS_THRESHOLD`, `UTILITY_OUT_DEGREE_THRESHOLD`, `UTILITY_MAX_COMPLEXITY_THRESHOLD`, `ORPHAN_COMPONENT_MAX_SIZE`.
                *   Iterate nodes and assign a `node_role` attribute (e.g., `graph.nodes[node_id]['role'] = 'hub'`). A node can have multiple roles or a primary role.
        *   `packages/dependency_analyzer/src/dependency_analyzer/cli.py`:
            *   Command `analyze classify <graph_path>` to run classification and update the graph file (if node attributes are saved).
*   **Tools/Libraries:** `networkx`.
*   **Optimization:** Centrality measures can be slow. Use approximations or sampling (`k` in betweenness) if needed.
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Enhanced by:** Node Complexity Metrics (Feature 1.1) for more accurate Utility Node classification.
    *   **Missing:** None for basic classification.
*   **Pros:**
    *   Provides a quick architectural overview.
    *   Highlights key objects for focused attention.
    *   Helps identify potential dead code (orphans).
*   **Cons:**
    *   Thresholds for classification can be arbitrary and may need tuning per codebase.
    *   A node might fit multiple roles.
*   **Migration Use Case:**
    *   **Hubs:** Indicate complex integration points that need careful design in the Java system (e.g., as API gateways or core services).
    *   **Utilities:** Candidates for early migration into shared Java libraries.
    *   **Orphans:** Investigate if they are truly unused and can be skipped during migration.

---

## Tier 2: Structural Insights & Grouping

### 2.1 Feature: Package-Based Grouping (Analytical)

*   **Summary:** Analyze dependencies *between* packages and cohesion *within* packages.
*   **Detailed Description:**
    *   **Needs:** To understand the modularity of the existing PL/SQL codebase at the package level.
    *   **Requirements:** Ability to aggregate node-level dependencies to package-level.
    *   **Details:**
        *   Construct a "meta-graph" of packages.
        *   Calculate inter-package coupling (number of calls between distinct packages).
        *   Calculate intra-package cohesion (density of calls within the same package).
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create `analyze_package_dependencies(graph: nx.DiGraph) -> Dict[str, Any]`.
            *   This function will:
                1.  Extract all unique package names from `graph.nodes[node_id]['object'].package_name`.
                2.  Create a new `nx.DiGraph()` for packages.
                3.  For each edge `(u, v)` in the original graph:
                    *   Get `pkg_u = graph.nodes[u]['object'].package_name` and `pkg_v = graph.nodes[v]['object'].package_name`.
                    *   If `pkg_u` and `pkg_v` are valid and `pkg_u != pkg_v`, add/increment weight of edge `(pkg_u, pkg_v)` in the package graph.
                4.  Calculate cohesion for each package:
                    *   For package `P`, find all nodes `N_p` belonging to `P`.
                    *   Count internal edges: number of edges `(n1, n2)` where `n1, n2` are in `N_p`.
                    *   Max possible internal edges: `len(N_p) * (len(N_p) - 1)`.
                    *   Cohesion = (internal edges) / (max possible internal edges) if `len(N_p) > 1` else 1.
                5.  Calculate coupling for each package:
                    *   In-coupling: Number of incoming edges from other packages in the package graph.
                    *   Out-coupling: Number of outgoing edges to other packages in the package graph.
            *   Return a dictionary containing the package meta-graph, cohesion scores, and coupling scores.
*   **Tools/Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** `PLSQL_CodeObject.package_name` on nodes.
    *   **Missing:** None.
*   **Pros:**
    *   Reveals high-level architecture and module interactions.
    *   Identifies well-encapsulated vs. overly-dependent packages.
*   **Cons:**
    *   Metrics can be simplistic; large packages might still have low numeric cohesion despite being functionally diverse.
*   **Migration Use Case:**
    *   Highly cohesive, loosely coupled packages are strong candidates for migration as independent Java modules/services.
    *   Packages with high inter-dependencies require careful planning for interface definitions or might be migrated together.

---

### 2.2 Feature: Community Detection

*   **Summary:** Automatically detect densely connected subgraphs (communities/modules) using graph algorithms.
*   **Detailed Description:**
    *   **Needs:** To find "natural" groupings of PL/SQL objects that might represent underlying logical components, even if not explicitly organized by packages.
    *   **Requirements:** Implementation of community detection algorithms.
    *   **Details:** Apply algorithms like Louvain or Girvan-Newman to the dependency graph.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create `detect_communities(graph: nx.DiGraph, algorithm: str = 'louvain', **kwargs) -> List[Set[str]]`.
            *   Implement wrappers for:
                *   `nx.community.louvain_communities(graph, weight=kwargs.get('weight'), resolution=kwargs.get('resolution', 1.0))`
                *   `nx.community.girvan_newman(graph)` (note: returns an iterator of tuples of frozensets)
                *   `nx.community.label_propagation_communities(graph)`
            *   The function should return a list of sets, each set containing node IDs of a community.
            *   Optionally, add a function `add_community_labels_to_graph(graph, communities)` to store `community_id` as a node attribute.
        *   `packages/dependency_analyzer/src/dependency_analyzer/cli.py`:
            *   Command `analyze communities <graph_path> [--algorithm louvain/girvan_newman/label_propagation]`.
*   **Tools/Libraries:** `networkx.algorithms.community`.
*   **Optimization:** Louvain and Label Propagation are generally faster for large graphs. Girvan-Newman can be slow.
*   **Data Requirements:**
    *   **Current:** Graph structure. Edge weights (e.g., based on call frequency if available, or inverse complexity) could refine results for some algorithms but are not strictly necessary.
    *   **Missing:** None for basic implementation.
*   **Pros:**
    *   Objective, data-driven way to find potential modules.
    *   Can uncover non-obvious relationships or groupings.
*   **Cons:**
    *   Results can vary based on algorithm and parameters; may require experimentation.
    *   Detected communities need domain expert validation to confirm their logical coherence.
*   **Migration Use Case:**
    *   Communities can serve as primary candidates for microservice boundaries or distinct Java modules.
    *   Helps in decomposing a monolithic PL/SQL application into more manageable, independent parts for migration.

---

### 2.3 Feature: Circular Dependency Analysis (Advanced)

*   **Summary:** Enhance existing cycle detection by providing visualization support, ranking cycles, and potentially suggesting break points.
*   **Detailed Description:**
    *   **Needs:** Circular dependencies are problematic for migration and indicate tight coupling. Advanced analysis helps prioritize and resolve them.
    *   **Requirements:** Cycle detection, node complexity metrics (Feature 1.1).
    *   **Details:**
        *   Visualize cycles clearly in the UI.
        *   Rank cycles by size (number of nodes) or cumulative/average complexity of nodes within the cycle.
        *   (Experimental) Suggest potential edges to remove to break cycles, based on heuristics (e.g., breaking the "weakest" link or a link to/from the least central node in the cycle).
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Modify `find_circular_dependencies` or create a new function `analyze_cycles(graph: nx.DiGraph) -> List[Dict[str, Any]]`.
            *   Each dictionary in the list could represent a cycle and include:
                *   `nodes: List[str]`
                *   `size: int`
                *   `average_complexity: float` (requires Feature 1.1)
                *   `cumulative_complexity: float` (requires Feature 1.1)
                *   `suggested_break_points: List[Tuple[str, str]]` (list of edges - Advanced)
            *   For break points (advanced): Iterate edges within a cycle. For each edge `(u,v)`, consider its "cost" to remove (e.g., based on how many other paths use it, or complexity of `u` and `v`). This is non-trivial. A simpler start is just ranking.
        *   `packages/dependency_analyzer/src/dependency_analyzer/visualization/exporter.py`:
            *   When exporting, if cycle information is available (e.g., nodes tagged as part of a specific cycle), use distinct styling for cycle edges/nodes.
*   **Tools/Libraries:** `networkx` for cycle detection.
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Enhanced by:** Node Complexity Metrics (Feature 1.1) for ranking.
    *   **Missing:** Reliable metrics for "edge importance" for suggesting break points.
*   **Pros:**
    *   Provides actionable insights for refactoring tightly coupled code.
    *   Essential for designing a more modular target architecture.
*   **Cons:**
    *   Automatically suggesting optimal break points is very difficult and often requires domain knowledge.
*   **Migration Use Case:**
    *   Identify and prioritize the resolution of circular dependencies before or during migration, as they often don't translate well to service-oriented or modular Java designs.

---

## Tier 3: Migration Strategy & Planning Aids

*(Features in this tier often leverage outputs from Tier 1 & 2)*

### 3.1 Feature: Impact Analysis ("What if?")

*   **Summary:** Allow users to select a node and visualize all directly and indirectly affected upstream (callers) and downstream (callees) objects.
*   **Detailed Description:**
    *   **Needs:** To understand the potential consequences of changing or migrating a specific PL/SQL object.
    *   **Requirements:** Interactive UI to select a node, backend to compute ancestors/descendants.
    *   **Details:** This is essentially a UI-driven application of Reachability Analysis (Feature 1.2).
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   **Backend (FastAPI):**
            *   Endpoint `GET /graphs/{graph_id}/nodes/{node_id}/impact?direction=all&depth=N`
            *   Internally calls `get_ancestors` and `get_descendants` from `analyzer.py`.
            *   Returns `{ "ancestors": [...], "descendants": [...] }`.
        *   **Frontend:**
            *   User selects a node.
            *   UI calls the impact analysis endpoint.
            *   Highlights the returned ancestor and descendant nodes on the graph, perhaps with different colors.
*   **Tools/Libraries:** `networkx` (already used).
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Missing:** None.
*   **Pros:**
    *   Powerful tool for risk assessment and change management during migration.
    *   Interactive and intuitive.
*   **Cons:**
    *   Visualization can become cluttered if the impact set is very large. UI needs to handle this gracefully (e.g., list view alongside graph highlight).
*   **Migration Use Case:**
    *   "If we migrate `PROC_A` to Java and change its interface, what existing PL/SQL code (ancestors) will need to be updated to call the new Java version? What other PL/SQL code (descendants) relied on `PROC_A` and might need to be migrated or refactored as part of the same unit of work?"

---

### 3.2 Feature: Critical Path Identification

*   **Summary:** Identify paths in the graph that are "critical" based on accumulated node complexity or other weights.
*   **Detailed Description:**
    *   **Needs:** To focus migration efforts on the most complex, risky, or important sequences of operations in the legacy system.
    *   **Requirements:** Node complexity metrics (Feature 1.1) or user-defined weights. Pathfinding algorithms.
    *   **Details:** Find paths between specified start/end nodes (or all entry-to-terminal paths) that maximize a cumulative weight (e.g., sum of node complexities).
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create `find_critical_paths(graph: nx.DiGraph, source_node: Optional[str] = None, target_node: Optional[str] = None, weight_attribute: str = 'complexity_score', N: int = 5) -> List[List[str]]`.
            *   If graph is a DAG, can use algorithms for longest paths by negating weights and finding shortest paths.
            *   For general graphs (with cycles), finding the "longest simple path" is NP-hard. Instead:
                1.  If `source_node` and `target_node` are given: find all simple paths `nx.all_simple_paths`.
                2.  For each path, calculate its total "criticality" (e.g., sum of `weight_attribute` for all nodes in path).
                3.  Return the top `N` paths by criticality.
            *   If no `source`/`target`, consider paths between all entry points and terminal nodes.
*   **Tools/Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Required:** Node Complexity Metrics (Feature 1.1) or another node attribute to use as `weight_attribute`.
    *   **Missing:** None if Feature 1.1 is done.
*   **Pros:**
    *   Guides prioritization of migration tasks based on objective complexity/effort.
    *   Helps in identifying core business logic flows.
*   **Cons:**
    *   Computationally intensive if `all_simple_paths` is used on large, dense graphs. Needs sensible limits (e.g., path length cutoff, `N` top paths).
    *   Definition of "criticality" (the weight attribute) is key to useful results.
*   **Migration Use Case:**
    *   "Which execution paths in the PL/SQL system represent the highest accumulated complexity? These should be prioritized for thorough analysis and careful migration."

---

### 3.3 Feature: Strangler Fig Pattern Support (Candidate Identification)

*   **Summary:** Identify PL/SQL objects that are good candidates to be wrapped or replaced early using the Strangler Fig pattern.
*   **Detailed Description:**
    *   **Needs:** To facilitate incremental migration by identifying suitable "seams" in the application where new Java services can intercept calls to old PL/SQL.
    *   **Requirements:** Analysis of call patterns, particularly incoming calls from diverse parts of the system.
    *   **Details:** Candidates are typically procedures/functions that:
        *   Have a high in-degree.
        *   Are called by objects from multiple different packages or communities (indicating they serve a cross-cutting concern or are a widely used interface).
        *   Have well-defined interfaces (parameters from `parsed_parameters`).
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create `identify_strangler_candidates(graph: nx.DiGraph, min_in_degree: int = 5, min_distinct_caller_packages: int = 2) -> List[str]`.
            *   Iterate nodes:
                1.  Check `graph.in_degree(node_id)`.
                2.  For each node, get its callers: `graph.predecessors(node_id)`.
                3.  Count how many distinct `package_name`s these callers belong to. (Requires community labels if using communities instead of packages).
                4.  If criteria are met, add `node_id` to the candidate list.
*   **Tools/Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure, `PLSQL_CodeObject.package_name`. Community labels from Feature 2.2 would be beneficial.
    *   **Missing:** None for a basic implementation.
*   **Pros:**
    *   Directly supports a proven, lower-risk incremental migration strategy.
    *   Helps decouple the system piece by piece.
*   **Cons:**
    *   Metrics are heuristic; identified candidates still need manual validation for suitability as a "strangler facade."
*   **Migration Use Case:**
    *   "Identify PL/SQL procedures that are widely called across different packages. These are good candidates to create Java Spring Boot facade services for, gradually strangling the old PL/SQL implementation."

---

### 3.4 Feature: User-Defined Grouping (Backend)

*   **Summary:** Allow users to manually group nodes based on domain knowledge or migration planning, and persist these groups.
*   **Detailed Description:**
    *   **Needs:** To overlay business or migration-specific context onto the technical call graph, enabling more tailored analysis and planning.
    *   **Requirements:** Backend storage for group definitions and APIs to manage them.
    *   **Details:** A group consists of a name/ID and a list of node IDs.
*   **Implementation Plan:**
    *   **Repository Structure Change:**
        *   Potentially add `packages/dependency_analyzer/src/dependency_analyzer/persistence/group_storage.py` if logic becomes complex, or extend `graph_storage.py` if simple.
        *   Database schema (SQLite) needs a new table: `UserDefinedGroups (group_id TEXT PRIMARY KEY, group_name TEXT UNIQUE, description TEXT)` and `UserGroupNodes (group_id TEXT, node_id TEXT, FOREIGN KEY(group_id) REFERENCES UserDefinedGroups(group_id), PRIMARY KEY (group_id, node_id))`.
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/persistence/graph_storage.py` (or new `group_storage.py`):
            *   Functions to `create_group`, `add_node_to_group`, `remove_node_from_group`, `get_group_nodes`, `list_groups`, `delete_group`.
        *   `packages/dependency_analyzer/src/dependency_analyzer/cli.py`:
            *   Commands like `groups create <name>`, `groups add <group_name> <node_id>`, etc.
        *   **FastAPI Backend (Future):** Endpoints for CRUD operations on groups.
*   **Tools/Libraries:** `sqlite3`.
*   **Data Requirements:**
    *   **Current:** Node IDs from the graph.
    *   **Missing:** Storage mechanism for groups (addressed by plan).
*   **Pros:**
    *   Highly flexible, allows users to tailor the graph view to their specific needs.
    *   Essential for collaborative migration planning.
*   **Cons:**
    *   Requires manual effort from users.
    *   Group definitions need to be maintained if the underlying graph changes significantly.
*   **Migration Use Case:**
    *   "Let's group all PL/SQL objects related to 'Billing' into a 'Billing_Module' group to analyze its internal complexity and external dependencies as a unit before planning its migration."

---

## Tier 4: Advanced/Future Enhancements

*(These features are generally more complex or build heavily on previous tiers)*

### 4.1 Feature: Minimizing Inter-Unit Dependencies (Analysis)

*   **Summary:** Analyze a given partitioning of the graph (e.g., by package, community, or user-defined group) to quantify inter-unit dependencies and suggest refinements.
*   **Detailed Description:**
    *   **Needs:** To optimize the boundaries of migration units (e.g., microservices) to reduce coupling and improve independence.
    *   **Requirements:** A pre-existing grouping of nodes. Graph partitioning concepts.
    *   **Details:** Given a set of groups, calculate the "cut size" (number of edges between groups). Potentially offer suggestions for moving nodes between groups to reduce this cut size.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   `calculate_inter_group_dependencies(graph: nx.DiGraph, groups: Dict[str, List[str]]) -> Dict[Tuple[str, str], int]`: Takes a dict of group_name -> list_of_node_ids. Returns a dict of (group1_name, group2_name) -> call_count.
            *   (Advanced) `suggest_group_refinements(graph, groups)`: Implement heuristics (e.g., identify nodes in group A that are called more by group B than by group A itself as candidates to move).
*   **Tools/Libraries:** `networkx`. Graph partitioning algorithms are available but might be overkill initially.
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Required:** Node groupings (from Features 2.1, 2.2, or 3.4).
*   **Pros:** Leads to better-defined, more loosely coupled migration units.
*   **Cons:** Optimal graph partitioning is NP-hard. Heuristics can be complex to implement and tune.
*   **Migration Use Case:** "After initial grouping, analyze the 'chatty' interfaces between proposed Java services. Can we move some PL/SQL objects between these planned units to reduce inter-service calls?"

---

### 4.2 Feature: Change Propagation Path Visualization

*   **Summary:** For a selected source and target node, visualize the shortest or most common paths through which changes might propagate.
*   **Detailed Description:**
    *   **Needs:** To understand specific routes of influence between two components, beyond general reachability.
    *   **Requirements:** Pathfinding algorithms.
    *   **Details:** Similar to Execution Path Tracing (1.3) but often focused on fewer, more specific paths between two points.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   **Backend (FastAPI):** Endpoint `GET /graphs/{graph_id}/paths?source={node1}&target={node2}[&type=shortest/all_simple&cutoff=N]`.
        *   Internally uses `nx.shortest_path` or `nx.all_simple_paths` from `analyzer.py`.
        *   **Frontend:** UI to select two nodes and display the highlighted path(s).
*   **Tools/Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Missing:** None.
*   **Pros:** More focused than general reachability for understanding specific A-to-B influences.
*   **Cons:** "Most common" paths are hard to define without dynamic call data. `all_simple_paths` can still be numerous.
*   **Migration Use Case:** "If `LOW_LEVEL_UTIL` is changed during migration, what are the most direct ways this change could affect `HIGH_LEVEL_BUSINESS_PROC`?"

---

### 4.3 Feature: Anti-Pattern Detection

*   **Summary:** Identify known PL/SQL anti-patterns in the codebase using graph metrics and `PLSQL_CodeObject` data.
*   **Detailed Description:**
    *   **Needs:** To proactively find problematic structures that will complicate migration or lead to poor design in the target Java system if migrated as-is.
    *   **Requirements:** Rules based on graph metrics, object properties, and potentially `clean_code` analysis.
    *   **Details:**
        *   **Large Package:** Count objects per `package_name`.
        *   **God Procedure/Function:** High scores on multiple Node Complexity Metrics (Feature 1.1) and high degree/centrality (Feature 1.4).
        *   **(Future) Excessive Global Package State:** Requires `plsql_analyzer` to identify package-level variables and their usage. Then, `dependency_analyzer` would look for packages where many internal objects heavily reference these package-level variables.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/analyzer.py`:
            *   Create `detect_anti_patterns(graph: nx.DiGraph, config: AntiPatternConfig) -> Dict[str, List[str]]`.
            *   `AntiPatternConfig` would hold thresholds for various metrics.
            *   Implement rule-based checks.
    *   **Repository Structure Change:**
        *   `plsql_analyzer` would need enhancements to extract package variable declarations and their usage contexts if "Excessive Global Package State" is to be detected reliably.
*   **Tools/Libraries:** `networkx`, `re` for code scanning if needed.
*   **Data Requirements:**
    *   **Current:** Graph structure, `PLSQL_CodeObject` attributes.
    *   **Enhanced by:** Node Complexity Metrics (Feature 1.1).
    *   **Missing (for some patterns):** Detailed parse of package variable declarations and their usage from `plsql_analyzer`.
*   **Pros:** Helps identify technical debt and areas needing refactoring.
*   **Cons:** Rule definition can be complex and heuristic. Some patterns require deeper code analysis than currently available.
*   **Migration Use Case:** "Find all 'God procedures' in the PL/SQL that need to be broken down into smaller, more focused Java classes/methods." "Identify packages that act like global variable buckets, which need careful handling in a stateless Java environment."

---

### 4.4 Feature: Code Similarity/Clustering (Content-Based)

*   **Summary:** Find PL/SQL objects with structurally or semantically similar `clean_code`.
*   **Detailed Description:**
    *   **Needs:** To identify duplicated or near-duplicated logic that can be consolidated into reusable components in the target Java system.
    *   **Requirements:** Access to `clean_code`, text similarity algorithms, or ML/LLM capabilities.
    *   **Details:** Use techniques like Levenshtein distance, Jaccard similarity on tokenized code, or LLM embeddings for semantic similarity.
*   **Implementation Plan:**
    *   **Affected Files/Objects:**
        *   `packages/dependency_analyzer/src/dependency_analyzer/analysis/code_similarity.py` (new file).
            *   Function `find_similar_code_objects(graph: nx.DiGraph, method: str = 'jaccard', threshold: float = 0.8, llm_model: Optional[str] = None) -> List[Tuple[str, str, float]]`.
            *   Implement Jaccard: tokenize `clean_code` (simple split by whitespace/punctuation or more advanced PL/SQL tokenizer).
            *   Implement LLM embeddings: Use a library like `sentence-transformers` (with a code-trained model) or an API service. Calculate pairwise cosine similarity.
    *   **Tools/Libraries:** `textdistance`, `scikit-learn` (for tokenization, clustering), `sentence-transformers`, LLM client libraries.
*   **Data Requirements:**
    *   **Current:** `PLSQL_CodeObject.clean_code`.
    *   **Missing:** None for basic text metrics. LLM access/models for semantic.
*   **Pros:**
    *   Can significantly reduce redundant code in the migrated system.
    *   Improves maintainability.
*   **Cons:**
    *   Syntactic similarity can be superficial.
    *   Semantic similarity (LLM) adds external dependencies, potential costs, and complexity.
    *   Computationally intensive for pairwise comparisons on many objects.
*   **Migration Use Case:** "Are there multiple PL/SQL procedures performing very similar validation logic? Let's identify them and create a single Java validation utility."

---

This roadmap provides a structured approach. Each feature can be further broken down into smaller tasks. Regular review and adaptation of this roadmap will be necessary as the project progresses and new insights are gained.