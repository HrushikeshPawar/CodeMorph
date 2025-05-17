# CodeMorph: `dependency_analyzer` Enhancement Roadmap - FastAPI

**Project Goal:** To transform `dependency_analyzer` into a powerful tool supporting semi-automated code migration from PL/SQL to Java SpringBoot, featuring advanced graph analysis, a FastAPI backend, and a rich React frontend.

**Prioritization Strategy:**

The roadmap is structured in releases, prioritizing features based on:

1.  **Core Value:** Features directly aiding migration understanding and planning.
2.  **Foundation First:** Backend capabilities before complex UI features that depend on them.
3.  **Iterative Complexity:** Start with essential analysis and gradually add more advanced features.
4.  **User Feedback Loop (Implied):** Ideally, after each major release, feedback would inform subsequent priorities.

---

## Release 1.0: Core Analysis & API Foundation

**Theme:** Establish robust backend data access, foundational graph loading, subgraph generation, and essential server-side analyses accessible via API. This enables basic UI interaction and data-driven insights.

**Target Repo Structure Changes (Illustrative for FastAPI part):**

```
CodeMorph/
├── dependency_analyzer/             # Existing package
│   ├── src/dependency_analyzer/
│   │   ├── analysis/
│   │   ├── builder/
│   │   ├── cli.py
│   │   ├── config.py
│   │   ├── __init__.py
│   │   ├── persistence/
│   │   ├── utils/
│   │   └── visualization/
│   └── tests/
├── fastapi_app/                     # NEW: FastAPI application root
│   ├── main.py
│   ├── routers/
│   │   ├── graphs.py
│   │   └── analysis.py
│   │   └── nodes.py
│   ├── services/
│   │   ├── graph_service.py
│   │   └── analysis_service.py
│   ├── models/                     # Pydantic models
│   │   ├── graph_models.py
│   │   ├── analysis_models.py
│   │   └── node_models.py
│   ├── core/
│   │   └── config.py               # FastAPI specific config
│   ├── db/                         # NEW: For FastAPI app's own DB (user data, metadata)
│   │   ├── session.py              # (e.g., SQLAlchemy setup)
│   │   └── base.py                 # (e.g., Base for ORM models)
│   ├── crud/                       # NEW: CRUD operations for FastAPI app's DB
│   │   └── graph_metadata_crud.py
│   └── tests/                      # NEW: FastAPI specific tests
├── generated/                       # As before
├── packages/                        # As before (dependency_analyzer is here)
└── ... (other project files)
```

---

### Feature 1.1: FastAPI App Setup & Graph Metadata Persistence

*   **Summary:** Initialize the FastAPI application. Implement a system to manage metadata about available graph files.
*   **Detailed Description:**
    *   **Need:** A central way for the backend (and subsequently the UI) to know which dependency graphs exist and where to find them, along with basic information about each.
    *   **Requirements:**
        *   FastAPI application instance.
        *   Database (SQLite initially) for storing `graph_metadata`.
        *   Mechanism to populate `graph_metadata` (manual registration endpoint and/or directory scan).
*   **Implementation Plan:**
    1.  **FastAPI App (`fastapi_app/main.py`):**
        *   Create FastAPI app instance.
        *   Setup basic CORS middleware.
        *   Define a simple root endpoint (`/`) for health checks.
    2.  **Configuration (`fastapi_app/core/config.py`):**
        *   Load paths from `dependency_analyzer.config` (e.g., `GRAPHS_DIR`, `DATABASE_PATH` for PL/SQL data).
        *   Define path for the new FastAPI app's SQLite DB (e.g., `FA_DB_URL = "sqlite:///./fastapi_app_data.db"`).
    3.  **Database Setup (`fastapi_app/db/session.py`, `fastapi_app/crud/graph_metadata_crud.py`):**
        *   Define SQLAlchemy models (or use direct SQL) for the `graph_metadata` table:
            *   `graph_id: TEXT PRIMARY KEY` (filename stem)
            *   `file_path: TEXT UNIQUE NOT NULL`
            *   `description: TEXT`
            *   `source_plsql_db_path: TEXT`
            *   `created_at: DATETIME`
            *   `node_count: INTEGER`
            *   `edge_count: INTEGER`
            *   `tags: TEXT` (JSON)
            *   `is_structure_only: BOOLEAN`
        *   Create CRUD functions for `graph_metadata` (create, get, list, update, delete).
        *   Initialize DB and tables on app startup if they don't exist.
    4.  **Pydantic Models (`fastapi_app/models/graph_models.py`):**
        *   `GraphInfo` (for listing graphs).
        *   `GraphMetadataCreate` (for registration endpoint).
*   **Tools & Libraries:** FastAPI, Pydantic, SQLAlchemy (optional, for DB interaction), `dependency_analyzer.config`, `dependency_analyzer.persistence.GraphStorage` (for parsing graph files during registration to get node/edge counts).
*   **Missing Data/Features:** A robust initial population strategy for `graph_metadata` if many pre-existing graphs.
*   **Pros:** Enables dynamic discovery of graphs, provides context.
*   **Cons:** Adds a new database dependency for the FastAPI app.

---

### Feature 1.2: API Endpoints for Graph Listing and Loading

*   **Summary:** Implement API endpoints to list available graphs and load a specific graph's structure and node/edge data.
*   **Detailed Description:**
    *   **Need:** Allow the UI to present a list of graphs to the user and then fetch the data for a selected graph to visualize.
    *   **Requirements:**
        *   Endpoint to list graphs based on `graph_metadata`.
        *   Endpoint to retrieve a full graph (nodes, edges, minimal object attributes) by its ID.
        *   Support loading structure-only graphs and populating with objects if full details are requested.
*   **Implementation Plan:**
    1.  **Router (`fastapi_app/routers/graphs.py`):**
        *   **`GET /graphs`**:
            *   Uses `graph_metadata_crud.list_graphs()` to fetch data.
            *   Serializes to `List[GraphInfo]`.
        *   **`GET /graphs/{graph_id}`**:
            *   Uses `graph_metadata_crud.get_graph(graph_id)` to get `file_path` and `source_plsql_db_path`, `is_structure_only`.
            *   **Service (`fastapi_app/services/graph_service.py`):**
                *   Inject `GraphStorage` and `DatabaseLoader`.
                *   If `details="full"` and `is_structure_only` is true, use `GraphStorage.load_and_populate()`.
                *   Else, use `GraphStorage.load_graph()`.
                *   Transform NetworkX graph to `GraphResponse` (with `NodeResponse`, `EdgeResponse`, `PLSQLCodeObjectMinimalResponse`).
    2.  **Pydantic Models (`fastapi_app/models/graph_models.py`):**
        *   `GraphResponse`, `NodeResponse`, `EdgeResponse`, `PLSQLCodeObjectMinimalResponse`.
    3.  **Service (`graph_service.py`):**
        *   Encapsulate logic for loading graphs, handling structure-only vs. full, and transforming to response models.
        *   Manage instances of `GraphStorage` and `DatabaseLoader`. `DatabaseLoader` will need the `source_plsql_db_path` for the specific graph.
*   **Tools & Libraries:** FastAPI, Pydantic, `dependency_analyzer.persistence.GraphStorage`, `dependency_analyzer.utils.DatabaseLoader`.
*   **Missing Data/Features:** `source_plsql_db_path` must be reliably stored in `graph_metadata`.
*   **Pros:** Provides the core data feed for the UI.
*   **Cons:** Potentially large responses for big graphs; initial load in UI might be slow.
*   **Optimizations:** Server-Side Caching for frequently accessed/large graphs (e.g., using Redis or in-memory LRU cache if app is single instance).

---

### Feature 1.3: API Endpoint for Subgraph Generation

*   **Summary:** Implement an API endpoint to generate and return subgraphs based on user-defined parameters.
*   **Detailed Description:**
    *   **Need:** Allow users to focus on specific parts of the dependency graph.
    *   **Requirements:** Accept a source graph ID, a central node ID, upstream/downstream depth, and return the resulting subgraph.
*   **Implementation Plan:**
    1.  **Router (`fastapi_app/routers/graphs.py`):**
        *   **`POST /graphs/{source_graph_id}/subgraph`**:
            *   Request body: `SubgraphRequest` (Pydantic model).
    2.  **Service (`fastapi_app/services/graph_service.py`):**
        *   Load the `source_graph_id` (potentially using `load_and_populate` based on `SubgraphRequest.load_with_objects`).
        *   Call `dependency_analyzer.analysis.analyzer.generate_subgraph_for_node()`.
        *   Transform the resulting NetworkX subgraph to `GraphResponse`.
        *   *Decision Point:* Persist generated subgraphs? If yes, save using `GraphStorage`, register in `graph_metadata`, and return its new ID. If no, return the subgraph data directly. For V1, returning data directly is simpler.
    3.  **Pydantic Models (`fastapi_app/models/graph_models.py`):**
        *   `SubgraphRequest`.
*   **Tools & Libraries:** FastAPI, Pydantic, `dependency_analyzer.analysis.analyzer`.
*   **Missing Data/Features:** If persisting subgraphs, a clear naming and lifecycle management strategy.
*   **Pros:** Enables interactive exploration and reduces data transfer for focused views.
*   **Cons:** Subgraph generation can be computationally intensive for very large source graphs and deep/wide exploration.
*   **Optimizations:** Consider async execution if subgraph generation is slow.

---

### Feature 1.4: Basic Server-Side Graph Analysis API Endpoints

*   **Summary:** Expose fundamental graph analysis functions (cycles, entry points, terminal nodes, node degrees, paths, connected components) via API.
*   **Detailed Description:**
    *   **Need:** Provide basic analytical insights to the UI without requiring the UI to implement these algorithms or fetch the entire graph for client-side processing.
    *   **Requirements:** Endpoints for each analysis type, taking graph ID and relevant parameters, returning structured results.
*   **Implementation Plan:**
    1.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `GET /graphs/{graph_id}/analysis/cycles` -> `List[List[str]]`
        *   `GET /graphs/{graph_id}/analysis/entry_points` -> `List[str]`
        *   `GET /graphs/{graph_id}/analysis/terminal_nodes` (query: `exclude_placeholders`) -> `List[str]`
        *   `GET /graphs/{graph_id}/analysis/node_degrees/{node_id}` -> `Dict[str, int]`
        *   `GET /graphs/{graph_id}/analysis/paths` (query: `source_node`, `target_node`, `cutoff`) -> `List[List[str]]`
        *   `GET /graphs/{graph_id}/analysis/connected_components` (query: `strongly_connected`) -> `List[List[str]]`
    2.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   Methods corresponding to each endpoint.
        *   Load the graph (likely minimal version, no full objects needed unless an analysis depends on object attributes not in `PLSQLCodeObjectMinimalResponse`).
        *   Call the respective functions from `dependency_analyzer.analysis.analyzer`.
        *   Format results for JSON response.
    3.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   Specific response models if needed for more complex results, or use standard list/dict.
*   **Tools & Libraries:** FastAPI, Pydantic, `dependency_analyzer.analysis.analyzer`.
*   **Pros:** Offloads analysis to backend, reduces client-side complexity, consistent results.
*   **Cons:** Each call loads the graph; consider caching the loaded graph instance in the service if multiple analyses are performed on the same graph in short succession (requires careful state management or request-scoped service instances).
*   **Optimizations:** `async def` for endpoints. Caching of graph objects in memory (LRU cache) keyed by `graph_id` to avoid repeated file loading.

---

### Feature 1.5: API Endpoint for Node Source Code

*   **Summary:** Allow fetching the `clean_code` and `literal_map` for a specific PL/SQL object.
*   **Detailed Description:**
    *   **Need:** UI needs to display the source code of a selected PL/SQL object.
    *   **Requirements:** Endpoint to take graph ID and node ID, return code and literal map.
*   **Implementation Plan:**
    1.  **Router (`fastapi_app/routers/nodes.py`):**
        *   `GET /graphs/{graph_id}/nodes/{node_id}/code`
    2.  **Service (`fastapi_app/services/graph_service.py` or a new `node_service.py`):**
        *   Method `get_node_code(graph_id: str, node_id: str)`.
        *   Strategy 1: If `PLSQLCodeObject` stored in the graph file contains `clean_code` and `literal_map` (current plan is NO for structure-only saves), load graph and extract.
        *   Strategy 2 (Preferred for efficiency & consistency):
            *   Get `source_plsql_db_path` from `graph_metadata` for the `graph_id`.
            *   Use `DatabaseManager(source_plsql_db_path)` to query the `Extracted_PLSQL_CodeObjects` table for the row where `id == node_id`.
            *   The `codeobject_data` column stores the JSON of `PLSQL_CodeObject.to_dict()`. Parse this JSON.
            *   Extract `clean_code` and `literal_map`.
    3.  **Pydantic Models (`fastapi_app/models/node_models.py`):**
        *   `NodeCodeResponse` (`node_id`, `clean_code`, `literal_map`).
    4.  **Enhancement to `plsql_analyzer.persistence.DatabaseManager`:**
        *   Add `get_codeobject_data_by_id(object_id: str) -> Optional[Dict]` method to fetch the raw `codeobject_data` JSON string or parsed dict.
*   **Tools & Libraries:** FastAPI, Pydantic, `plsql_analyzer.persistence.DatabaseManager`.
*   **Pros:** Decouples large source code from main graph data transfer.
*   **Cons:** Requires an extra API call from UI.
*   **Optimizations:** Ensure efficient DB query in `DatabaseManager`.

---

## Release 1.5: Basic UI Integration & Advanced Node Metrics

**Theme:** Develop a basic React UI that can consume the Release 1.0 APIs for graph display and interaction. Enhance backend with more detailed node metrics.

(UI development is out of scope for this detailed `dependency_analyzer` backend plan, but its needs inform the API).

### Feature 1.5.1: Advanced Node Metrics Calculation & API

*   **Summary:** Implement calculation for node complexity (LOC, NumParams, NumCallsMade, ApproxCyclo) and centrality metrics (Degree, Betweenness, PageRank). Expose via API.
*   **Detailed Description:**
    *   **Need:** Provide richer quantitative data about each node for better understanding and prioritization.
    *   **Requirements:**
        *   Functions to calculate these metrics for each node in a graph.
        *   API endpoint to return these metrics for all nodes in a graph.
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.analyzer` Enhancements:**
        *   New function `calculate_all_node_metrics(graph: nx.DiGraph) -> Dict[str, Dict[str, Any]]`:
            *   Iterate nodes. For each `PLSQLCodeObject`:
                *   LOC: `len(obj.clean_code.splitlines())`.
                *   NumParams: `len(obj.parsed_parameters)`.
                *   NumCallsMade: `len(obj.extracted_calls)`.
                *   ApproxCyclo: Count `IF`, `LOOP`, `CASE`, `WHILE`, `FOR` in `obj.clean_code`.
            *   Use NetworkX for: `nx.degree_centrality`, `nx.betweenness_centrality` (consider `k` for approximation), `nx.pagerank`.
            *   Return a dict: `{node_id: {'loc': x, 'num_params': y, ..., 'pagerank': z}}`.
    2.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   New method `get_all_node_metrics(graph_id: str)`. Loads graph, calls `calculate_all_node_metrics`.
    3.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `GET /graphs/{graph_id}/analysis/node_metrics_all` -> `Dict[str, Dict[str, Any]]`.
    4.  **Node Attribute Storage:** These calculated metrics should ideally be added as attributes to the nodes in the NetworkX graph object *if the graph object is cached or reused by the service*. If graphs are always reloaded, then calculation is on-demand.
*   **Tools & Libraries:** NetworkX, modifications to `dependency_analyzer.analysis.analyzer`.
*   **Missing Data:** Robust heuristic for ApproxCyclo.
*   **Pros:** Deepens understanding of individual object characteristics.
*   **Cons:** Betweenness centrality can be slow. ApproxCyclo is an estimate.

---

## Release 2.0: User Interactivity & Deeper Analysis

**Theme:** Enable user-driven organization (notes, groups) and more sophisticated graph analysis like community detection and automated node classification.

### Feature 2.1: User Notes and Grouping API & Persistence

*   **Summary:** Implement backend support for users to add notes to graph elements and create custom groups of nodes.
*   **Detailed Description:**
    *   **Need:** Allow users to overlay their domain knowledge and migration planning thoughts onto the graph.
    *   **Requirements:**
        *   Database tables (`notes`, `user_groups`) in the FastAPI app DB.
        *   CRUD API endpoints for notes and groups.
*   **Implementation Plan:**
    1.  **Database (`fastapi_app/db/session.py`, `fastapi_app/crud/user_data_crud.py`):**
        *   Define SQLAlchemy models (or use direct SQL) for `notes` and `user_groups` tables as outlined previously.
        *   Implement CRUD functions for these tables.
    2.  **Routers (`fastapi_app/routers/user_data.py`):**
        *   `POST, GET, PUT, DELETE /graphs/{graph_id}/notes`
        *   `POST, GET, PUT, DELETE /graphs/{graph_id}/groups`
    3.  **Pydantic Models (`fastapi_app/models/user_data_models.py`):**
        *   `NoteRequest`, `NoteResponse`, `GroupRequest`, `GroupResponse`.
    4.  **Service (`fastapi_app/services/user_data_service.py`):**
        *   Business logic for managing notes and groups, interacting with CRUD layer.
*   **Tools & Libraries:** SQLAlchemy (optional), Pydantic, FastAPI.
*   **Pros:** Significantly enhances the tool's utility for collaborative migration planning.
*   **Cons:** Adds DB complexity to the FastAPI app. Needs UI support to be useful.

---

### Feature 2.2: Community Detection & Node Role Classification API

*   **Summary:** Implement community detection and automated node role classification (hubs, utilities, orphans) and expose via API.
*   **Detailed Description:**
    *   **Need:** Provide automated insights into the graph's modular structure and the roles of different nodes.
    *   **Requirements:**
        *   Integrate community detection algorithms.
        *   Implement logic for classifying nodes based on metrics.
        *   API endpoints to trigger these analyses and return results.
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.analyzer` Enhancements:**
        *   Function `detect_communities(graph, algorithm="louvain", **kwargs)` using `nx.community`.
        *   Function `classify_node_roles(graph, metrics_dict)`:
            *   Takes graph and pre-calculated metrics (from Feature 1.5.1).
            *   Applies rules to assign roles (e.g., 'hub', 'utility', 'orphan_component_member', 'entry_point', 'terminal_node').
            *   Returns `Dict[str, str]` (node_id -> role_label).
    2.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `get_communities(graph_id, algorithm, **kwargs)`.
        *   `get_node_roles(graph_id)` (internally calls `get_all_node_metrics` then `classify_node_roles`).
    3.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `GET /graphs/{graph_id}/analysis/communities` (query: `algorithm`, `resolution`, etc.) -> `List[List[str]]` or `Dict[str, int]`.
        *   `GET /graphs/{graph_id}/analysis/node_roles` -> `Dict[str, str]`.
*   **Tools & Libraries:** NetworkX.
*   **Pros:** Provides higher-level structural insights automatically.
*   **Cons:** Community detection parameters may need tuning. Role classification rules are heuristic.

---

## Release 3.0: Advanced Migration Strategy & Planning Aids

**Theme:** Provide sophisticated tools to directly support migration planning, including detailed impact analysis, identification of critical code paths, and support for common migration patterns like Strangler Fig. This release heavily leverages the foundational analysis and user interaction capabilities built in previous releases.

**Target Repo Structure Changes:**

*   Minor additions within `fastapi_app/routers/analysis.py` and `fastapi_app/services/analysis_service.py`.
*   Enhancements primarily within `dependency_analyzer/analysis/analyzer.py`.
*   New database tables within the FastAPI app's DB for storing user-defined group metadata if not already fully implemented in 2.x.

---

### Feature 3.1: Impact Analysis ("What if?") Integration

*   **Summary:** Fully integrate the "What if?" impact analysis into the API and prepare for UI consumption, allowing users to select a node and visualize all directly and indirectly affected upstream (callers) and downstream (callees) objects.
*   **Detailed Description:**
    *   **Need:** To provide an interactive way for users to understand the ripple effects of changing, refactoring, or migrating a specific PL/SQL object.
    *   **Requirements:**
        *   An API endpoint that accepts a graph ID, a node ID, and optional depth limits for upstream and downstream analysis.
        *   The backend should efficiently compute the ancestor and descendant sets.
        *   The response should clearly delineate these two sets for UI highlighting.
    *   **Details:** This feature makes the existing reachability analysis (`nx.ancestors`, `nx.descendants`) more directly usable for a common migration planning question.
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.analyzer.py`:**
        *   Ensure `get_ancestors_at_depth(graph, node_id, depth_limit)` and `get_descendants_at_depth(graph, node_id, depth_limit)` functions are robust (using BFS from the node on the reversed graph for ancestors, and BFS on the normal graph for descendants, up to `depth_limit`). If `depth_limit` is `None`, find all. These might already be implicitly covered by `generate_subgraph_for_node` logic but dedicated functions are cleaner for this specific API.
    2.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   `ImpactAnalysisRequest(node_id: str, upstream_depth: Optional[int] = None, downstream_depth: Optional[int] = None)`
        *   `ImpactAnalysisResponse(node_id: str, ancestors: List[str], descendants: List[str])`
    3.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `perform_impact_analysis(graph_id: str, request: ImpactAnalysisRequest) -> ImpactAnalysisResponse`:
            *   Loads the graph (minimal structure should suffice).
            *   Calls the new/existing ancestor/descendant functions from `analyzer.py`.
            *   Constructs and returns `ImpactAnalysisResponse`.
    4.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `POST /graphs/{graph_id}/analysis/impact` (using POST as it takes a request body, or GET with query params if preferred).
*   **Tools & Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure from loaded graph files.
    *   **Missing:** None.
*   **Pros:**
    *   Provides critical insights for planning changes and assessing risk.
    *   Highly interactive and intuitive when paired with a UI.
*   **Cons:**
    *   For highly connected nodes, the ancestor/descendant sets can be very large, potentially leading to large API responses and cluttered UI if not handled carefully (e.g., by UI pagination or summarization of results).
*   **Migration Use Case:** Before migrating `PROC_X`, a developer uses this feature to see:
    1.  All PL/SQL objects that call `PROC_X` (ancestors) – these will need to be updated to call the new Java equivalent or have their logic re-evaluated.
    2.  All PL/SQL objects called by `PROC_X` (descendants) – these might need to be migrated along with `PROC_X` or have their interfaces carefully managed.

---

### Feature 3.2: Critical Path Identification (Weighted Paths)

*   **Summary:** Implement functionality to identify critical execution paths within the graph based on accumulated node complexity or other user-defined/calculated weights.
*   **Detailed Description:**
    *   **Need:** To help prioritize migration efforts by focusing on sequences of PL/SQL objects that represent significant complexity, business value, or risk.
    *   **Requirements:**
        *   Node complexity metrics (from Release 1.5.1: LOC, NumParams, NumCallsMade, ApproxCyclo) or a user-definable weight attribute per node.
        *   Ability to find paths (e.g., between specified entry/exit points, or all significant paths).
        *   A way to rank these paths by their cumulative "criticality."
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.analyzer.py`:**
        *   New function: `find_weighted_critical_paths(graph: nx.DiGraph, weight_attribute: str, N_top_paths: int = 10, source_nodes: Optional[List[str]] = None, target_nodes: Optional[List[str]] = None, max_path_length: Optional[int] = None) -> List[Dict[str, Any]]`.
            *   **Input:** Graph, name of the node attribute to use as weight (e.g., 'complexity_score_approx', 'loc'), number of top paths to return.
            *   **Optional Inputs:** Lists of source nodes (e.g., entry points) and target_nodes (e.g., terminal nodes). If not provided, might consider all entry-to-terminal paths (computationally expensive). `max_path_length` to control `all_simple_paths`.
            *   **Logic:**
                a.  Validate `weight_attribute` exists on nodes.
                b.  Determine path candidates:
                    *   If `source_nodes` and `target_nodes` provided, iterate through all pairs and find simple paths (`nx.all_simple_paths`) between them, respecting `max_path_length`.
                    *   If only `source_nodes`, find paths from them.
                    *   If only `target_nodes`, find paths to them (on reversed graph).
                    *   (More advanced) If neither, could iterate from all entry points to all terminal nodes.
                c.  For each path found, calculate its total weight (sum of `weight_attribute` for all nodes in the path).
                d.  Sort paths by total weight in descending order.
                e.  Return the top `N_top_paths`, each path as a list of node IDs along with its total weight (e.g., `{'path': ['nodeA', 'nodeB'], 'total_weight': 150.0}`).
    2.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   `CriticalPathRequest(weight_attribute: str, N_top_paths: int = 10, source_nodes: Optional[List[str]] = None, target_nodes: Optional[List[str]] = None, max_path_length: Optional[int] = None)`
        *   `PathDetail(path: List[str], total_weight: float)`
        *   `CriticalPathResponse(paths: List[PathDetail])`
    3.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `get_critical_paths(graph_id: str, request: CriticalPathRequest) -> CriticalPathResponse`:
            *   Loads graph (ensuring node metrics required for `weight_attribute` are present or calculated on-the-fly – might need to load full objects if complexity depends on `clean_code`).
            *   Calls `find_weighted_critical_paths`.
    4.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `POST /graphs/{graph_id}/analysis/critical_paths` (POST due to potentially complex request body).
*   **Tools & Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Required:** Node attributes for weighting (e.g., 'loc', 'complexity_score_approx' from Feature 1.5.1).
    *   **Missing:** Reliable node complexity scores if not yet implemented. A way for users to specify custom node weights if desired (could be part of user-defined data).
*   **Pros:**
    *   Provides a data-driven approach to prioritizing complex or lengthy execution flows for migration.
    *   Helps in identifying core business logic or high-risk areas.
*   **Cons:**
    *   Finding all simple paths can be very computationally expensive for large/dense graphs. `max_path_length` and limiting source/target pairs are crucial.
    *   The usefulness heavily depends on the quality and relevance of the `weight_attribute`.
*   **Migration Use Case:** A project manager wants to identify the top 10 "most complex execution chains" (based on summed LOC of involved procedures) to allocate senior developers for their analysis and migration.

---

### Feature 3.3: Strangler Fig Pattern Support (Candidate Identification)

*   **Summary:** Enhance the backend to identify PL/SQL objects that are strong candidates for applying the Strangler Fig migration pattern by analyzing their call patterns and interface characteristics.
*   **Detailed Description:**
    *   **Need:** To provide actionable suggestions for incremental migration, focusing on creating facades for widely used and externally-facing PL/SQL components.
    *   **Requirements:**
        *   Analyze node in-degrees.
        *   Analyze the diversity of callers (e.g., from different packages or identified communities).
        *   Consider the "stability" or "well-definedness" of the interface (e.g., number of parameters).
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.analyzer.py`:**
        *   Refine/create `identify_strangler_candidates(graph: nx.DiGraph, community_mapping: Optional[Dict[str, Any]] = None, min_in_degree: int = 5, min_distinct_caller_sources: int = 2, max_params: Optional[int] = 10) -> List[Dict[str, Any]]`.
            *   **Input:** Graph, optional mapping of node_id to community_id (from Feature 2.2), thresholds.
            *   **Logic:**
                a.  For each node:
                    i.  Get in-degree.
                    ii. Get direct callers (`graph.predecessors(node_id)`).
                    iii.Determine the "source diversity" of callers:
                        *   Count distinct `package_name` of callers.
                        *   If `community_mapping` provided, count distinct community IDs of callers.
                    iv. Get `PLSQLCodeObject` for the current node to check `len(obj.parsed_parameters)`.
                    v.  Apply thresholds: `in_degree >= min_in_degree`, `distinct_caller_package_count >= min_distinct_caller_sources` (or distinct community count), `num_params <= max_params` (interfaces that are too wide might be poor initial candidates).
                b.  Return a list of candidate node IDs, perhaps with their scores or reasons (e.g., `[{'node_id': 'pkg.proc_A', 'in_degree': 10, 'distinct_caller_packages': 3, 'num_params': 4}, ...]`).
    2.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   `StranglerCandidate(node_id: str, in_degree: int, distinct_caller_sources: int, num_params: int, object_details: PLSQLCodeObjectMinimalResponse)`
        *   `StranglerAnalysisResponse(candidates: List[StranglerCandidate])`
        *   `StranglerAnalysisRequest(min_in_degree: int = 5, min_distinct_caller_sources: int = 2, source_type: str = 'package', # 'package' or 'community'
                                     max_params: Optional[int] = 10)`
    3.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `get_strangler_candidates(graph_id: str, request: StranglerAnalysisRequest) -> StranglerAnalysisResponse`:
            *   Loads graph (needs `PLSQLCodeObject` details for params, so potentially `load_and_populate`).
            *   If `request.source_type == 'community'`, it first calls `get_communities` (Feature 2.2).
            *   Calls `identify_strangler_candidates` with appropriate parameters.
    4.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `POST /graphs/{graph_id}/analysis/strangler_candidates`.
*   **Tools & Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure, `PLSQL_CodeObject.package_name`, `PLSQLCodeObject.parsed_parameters`.
    *   **Optional:** Community labels (from Feature 2.2).
    *   **Missing:** None for a basic implementation focusing on package diversity.
*   **Pros:**
    *   Directly supports a practical, risk-reducing incremental migration strategy.
    *   Helps identify key interfaces to focus on early.
*   **Cons:**
    *   Thresholds are heuristic and may need tuning.
    *   True suitability also depends on business logic and data coupling, not just call structure.
*   **Migration Use Case:** The migration architect uses this feature to get a list of PL/SQL procedures that are heavily used by various other parts of the system. These become primary targets for creating Java-based facades in the early stages of the Strangler Fig migration.

---

### Feature 3.4: User-Defined Grouping Enhancement (Backend Persistence & API Finalization)

*   **Summary:** Fully implement and stabilize the backend persistence and API for user-defined node groups.
*   **Detailed Description:**
    *   **Need:** This feature, potentially started in Release 2.0, needs to be robust for users to save, load, and manage their logical groupings of PL/SQL objects.
    *   **Requirements:**
        *   Reliable storage of group definitions (group name, description, list of node IDs) associated with a specific graph ID.
        *   Full CRUD (Create, Read, Update, Delete) API endpoints for managing these groups.
        *   Ability for other analysis functions to leverage these user-defined groups (e.g., for calculating inter-group dependencies).
*   **Implementation Plan:**
    1.  **Database Schema (FastAPI app DB - ensure complete from Release 2.1):**
        *   `user_groups` table: `group_id (PK)`, `graph_id (FK)`, `name`, `description`, `node_ids (JSON TEXT)`, `created_at`, `updated_at`.
    2.  **CRUD Layer (`fastapi_app/crud/user_data_crud.py`):**
        *   Mature functions: `create_user_group`, `get_user_group`, `list_user_groups_for_graph`, `update_user_group`, `delete_user_group`, `add_nodes_to_group`, `remove_nodes_from_group`.
    3.  **Pydantic Models (`fastapi_app/models/user_data_models.py`):**
        *   Finalize `GroupRequest`, `GroupResponse`, `NodeGroupMembershipRequest`.
    4.  **Service (`fastapi_app/services/user_data_service.py`):**
        *   Business logic for group management, including validation (e.g., node IDs exist in the specified graph – this check might be complex and is optional for V1).
    5.  **Router (`fastapi_app/routers/user_data.py`):**
        *   `POST /graphs/{graph_id}/groups`
        *   `GET /graphs/{graph_id}/groups`
        *   `GET /graphs/{graph_id}/groups/{group_id}`
        *   `PUT /graphs/{graph_id}/groups/{group_id}` (e.g., update name, description, or overwrite node list)
        *   `DELETE /graphs/{graph_id}/groups/{group_id}`
        *   `POST /graphs/{graph_id}/groups/{group_id}/nodes` (add nodes)
        *   `DELETE /graphs/{graph_id}/groups/{group_id}/nodes` (remove nodes, request body with node IDs)
*   **Tools & Libraries:** SQLAlchemy (optional), Pydantic, FastAPI.
*   **Data Requirements:**
    *   **Current:** Graph node IDs.
    *   **Missing:** None specifically for storing definitions. The challenge is UI for creating/editing.
*   **Pros:**
    *   Empowers users to organize the complex graph according to their understanding and migration strategy.
    *   Forms a basis for more advanced group-based analysis.
*   **Cons:**
    *   Group definitions are static; if the underlying graph structure changes (e.g., nodes renamed/deleted in a new `plsql_analyzer` run), groups might become outdated. Requires a strategy for managing this (e.g., warnings in UI, cleanup jobs).
*   **Migration Use Case:** A team lead groups all PL/SQL objects related to "User Authentication" and another for "Profile Management." They then analyze dependencies *between* these two user-defined groups to plan their migration as separate modules/services.

---

## Release 4.0: Advanced & Future Enhancements

**Theme:** Introduce more sophisticated analytical capabilities, including deeper code analysis (anti-patterns, similarity) and optimizing migration unit boundaries. These features often require more complex algorithms or data from `plsql_analyzer`.

---

### Feature 4.1: Minimizing Inter-Unit Dependencies (Analysis & Heuristics)

*   **Summary:** Provide tools to analyze a given partitioning of the graph (by package, community, or user-defined groups) and quantify inter-unit dependencies, potentially suggesting refinements.
*   **Detailed Description:**
    *   **Need:** To help architects design target Java services/modules with minimal coupling, leading to a more maintainable and scalable system.
    *   **Requirements:** A way to define "units" (collections of nodes). Metrics for inter-unit calls. Heuristics for suggesting improvements.
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.analyzer.py`:**
        *   `calculate_inter_group_dependencies(graph: nx.DiGraph, node_to_group_mapping: Dict[str, str]) -> Dict[Tuple[str, str], int]`:
            *   Input: Graph, and a dictionary mapping each `node_id` to a `group_id` (or group name).
            *   Output: A dictionary where keys are `(source_group_id, target_group_id)` and values are the count of directed calls between them.
        *   `calculate_group_cohesion_coupling(graph: nx.DiGraph, group_nodes: List[str], all_nodes_in_graph: List[str]) -> Dict[str, float]`:
            *   Calculates internal cohesion for `group_nodes` and external coupling to `all_nodes_in_graph - group_nodes`.
        *   **(Advanced/Heuristic) `suggest_group_refinements(graph: nx.DiGraph, node_to_group_mapping: Dict[str, str], target_metric: str = 'minimize_cuts') -> List[Dict[str, str]]`:**
            *   This is complex. Could start with simple heuristics: e.g., identify nodes within a group that have more calls to/from an external group than within their own group. Suggest moving such nodes.
            *   Could explore algorithms like Kernighan-Lin for bisection or spectral partitioning if very advanced.
    2.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   `GroupPartition(groups: List[GroupDefinition])` where `GroupDefinition(group_id: str, node_ids: List[str])`.
        *   `InterGroupDependenciesRequest(partition: GroupPartition)`
        *   `InterGroupDependencyMetric(source_group_id: str, target_group_id: str, call_count: int)`
        *   `InterGroupDependenciesResponse(dependencies: List[InterGroupDependencyMetric], overall_cut_size: int)`
        *   `GroupCohesionCouplingResponse(group_id: str, cohesion: float, coupling_in: int, coupling_out: int)`
    3.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `get_inter_group_dependencies(graph_id: str, request: InterGroupDependenciesRequest)`.
        *   `get_group_cohesion_coupling_metrics(graph_id: str, group_id: str)` (assuming group definition is fetched from user_data_service).
    4.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `POST /graphs/{graph_id}/analysis/inter_group_dependencies`
        *   `GET /graphs/{graph_id}/groups/{group_id}/cohesion_coupling_metrics`
*   **Tools & Libraries:** `networkx`. Possibly graph partitioning libraries if going very advanced (e.g., `python-louvain` for communities which is a form of partitioning, or libraries wrapping METIS).
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Required:** Node groupings (from package info, Feature 2.2 community detection, or Feature 3.4 user-defined groups).
*   **Pros:**
    *   Aids in designing well-structured target architectures with clear boundaries and reduced inter-service communication overhead.
*   **Cons:**
    *   Suggesting optimal refinements automatically is very difficult and often requires domain context. The tool can provide metrics to aid manual refinement.
    *   Full graph partitioning algorithms can be computationally intensive.
*   **Migration Use Case:** An architect has an initial plan for microservice boundaries based on user-defined groups. They use this feature to quantify the number of calls expected between these planned services and identify "hotspots" of high inter-service dependency that might warrant rethinking group boundaries.

---

### Feature 4.2: Change Propagation Path Visualization (API Enhancement)

*   **Summary:** Enhance the API to robustly support visualizing shortest or top N weighted paths for change propagation analysis.
*   **Detailed Description:**
    *   **Need:** A more focused way than general impact analysis (Feature 3.1) to understand specific routes of influence or dependency between two components.
    *   **Requirements:** API to accept source node, target node, and parameters for path finding (e.g., shortest, all simple up to a cutoff, top N weighted).
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.analyzer.py`:**
        *   Ensure `find_all_paths(graph, source, target, cutoff)` is robust.
        *   New/Refined function: `find_relevant_paths(graph, source, target, type: str = 'all_simple', cutoff: Optional[int] = 5, weight_attribute: Optional[str] = None, N_top: Optional[int] = 5) -> List[PathDetail]`.
            *   If `type == 'shortest'`, use `nx.shortest_path` (if unweighted or `weight_attribute` is distance-like) or `nx.dijkstra_path` (if `weight_attribute` is cost).
            *   If `type == 'all_simple'`, use `nx.all_simple_paths` with `cutoff`. If `weight_attribute` and `N_top` are given, calculate path weights and return top N.
    2.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   `RelevantPathsRequest(source_node_id: str, target_node_id: str, path_type: str = 'all_simple', cutoff: Optional[int] = 5, weight_attribute: Optional[str] = None, N_top: Optional[int] = 5)`
        *   `RelevantPathsResponse(paths: List[PathDetail])` (reuse `PathDetail` from Critical Paths).
    3.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `get_relevant_paths(graph_id: str, request: RelevantPathsRequest)`.
    4.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `POST /graphs/{graph_id}/analysis/relevant_paths`.
*   **Tools & Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure.
    *   **Optional:** Node weights if weighted paths are desired (from Feature 1.5.1).
*   **Pros:** Provides more targeted insight into specific dependencies than broad reachability.
*   **Cons:** `all_simple_paths` can still be computationally expensive and return too many paths if `cutoff` is large.
*   **Migration Use Case:** "If we refactor the data structure returned by `GET_DATA_FUNC`, what are the primary procedures that consume this data and would be most directly affected, following the shortest call paths?"

---

### Feature 4.3: Anti-Pattern Detection (Initial Rules)

*   **Summary:** Implement detection for a basic set of PL/SQL anti-patterns using graph metrics and `PLSQLCodeObject` data.
*   **Detailed Description:**
    *   **Need:** To flag code structures that are known to be problematic for maintenance and migration, helping to prioritize refactoring efforts.
    *   **Requirements:**
        *   Define a set of detectable anti-patterns and their heuristic rules.
        *   An API endpoint to report detected anti-patterns.
*   **Implementation Plan:**
    1.  **Define Anti-Patterns & Rules (Configuration or Hardcoded initially):**
        *   **Large Package:** `package_node_count > X` (requires counting nodes per package).
        *   **God Procedure/Function:** `(node.complexity_score_approx > C) AND (node.in_degree + node.out_degree > D) AND (node.betweenness_centrality > B)` (requires metrics from Feature 1.5.1 and node role classification logic).
        *   **Deeply Nested Calls (from a specific entry point):** Path length from an entry point > N.
        *   **(Placeholder) Spaghetti Code:** High number of cycles involving a node, or high clustering coefficient for its local neighborhood but low overall modularity.
    2.  **`dependency_analyzer.analysis.analyzer.py`:**
        *   `detect_anti_patterns(graph: nx.DiGraph, node_metrics: Dict[str, Dict[str,Any]], community_mapping: Optional[Dict[str,Any]] = None) -> Dict[str, List[Dict[str, Any]]]`:
            *   Input: Graph, pre-calculated node metrics, optional community data.
            *   Output: `{'large_packages': [{'package_name': 'X', 'node_count': Y}], 'god_objects': [{'node_id': 'Z', 'metrics': {...}}], ...}`.
            *   Implement logic for each defined rule.
    3.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   Models for each type of anti-pattern detail.
        *   `AntiPatternReport(detected_patterns: Dict[str, List[Any]])`
    4.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `get_anti_pattern_report(graph_id: str)`. Fetches graph, metrics, (optionally communities), then calls `detect_anti_patterns`.
    5.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `GET /graphs/{graph_id}/analysis/anti_patterns`.
    6.  **`plsql_analyzer` Enhancements (Long-term for "Excessive Global Package State"):**
        *   `plsql_analyzer.parsing.structural_parser` (or a new parser) would need to identify package-level variable declarations.
        *   `plsql_analyzer.parsing.call_extractor` (or equivalent for variable usage) would need to identify reads/writes to these package variables within procedures/functions of that package.
        *   This data would be stored in `PLSQL_CodeObject` or a related structure.
*   **Tools & Libraries:** `networkx`.
*   **Data Requirements:**
    *   **Current:** Graph structure, `PLSQL_CodeObject` attributes.
    *   **Required:** Node Complexity Metrics (Feature 1.5.1), Centrality Metrics (Feature 1.5.1).
    *   **Missing (for advanced patterns):** Detailed parsing of package variable usage from `plsql_analyzer`.
*   **Pros:** Helps identify technical debt and targets for refactoring before or during migration, potentially leading to a cleaner Java codebase.
*   **Cons:** Anti-pattern detection is heuristic. False positives/negatives are possible. Some complex patterns require very deep code understanding not yet available.
*   **Migration Use Case:** "Are there any PL/SQL packages with over 50 procedures? These are 'Large Package' anti-patterns and should be broken up during migration." "Identify 'God Procedures' that handle too many responsibilities and plan to decompose them into smaller, focused Java classes."

---

### Feature 4.4: Code Similarity/Clustering (Basic Syntactic)

*   **Summary:** Implement basic syntactic code similarity detection (e.g., Jaccard similarity on tokenized `clean_code`) to find duplicated or near-duplicated logic.
*   **Detailed Description:**
    *   **Need:** To identify opportunities for code consolidation and reuse when migrating to Java, reducing redundancy.
    *   **Requirements:** Access to `PLSQL_CodeObject.clean_code`. A simple tokenization strategy. A similarity metric.
*   **Implementation Plan:**
    1.  **`dependency_analyzer.analysis.code_similarity.py` (New File):**
        *   `tokenize_plsql_light(code: str) -> Set[str]`: Simple tokenizer (split by whitespace and common punctuation, lowercase, filter common PL/SQL keywords that are not part of logic).
        *   `jaccard_similarity(set1: Set[str], set2: Set[str]) -> float`.
        *   `find_syntactically_similar_code(graph: nx.DiGraph, threshold: float = 0.85, min_loc_for_comparison: int = 10) -> List[Dict[str, Any]]`:
            *   Iterate over all pairs of `PLSQL_CodeObject`s (that meet `min_loc_for_comparison`).
            *   For each pair, get their `clean_code`, tokenize, calculate Jaccard similarity.
            *   If similarity > `threshold`, record the pair and their similarity score.
            *   Return `[{'object1_id': id1, 'object2_id': id2, 'similarity': score}, ...]`.
    2.  **Pydantic Models (`fastapi_app/models/analysis_models.py`):**
        *   `CodeSimilarityPair(object1_id: str, object2_id: str, similarity_score: float, object1_details: PLSQLCodeObjectMinimalResponse, object2_details: PLSQLCodeObjectMinimalResponse)`
        *   `CodeSimilarityResponse(similar_pairs: List[CodeSimilarityPair])`
        *   `CodeSimilarityRequest(threshold: float = 0.85, min_loc_for_comparison: int = 10)`
    3.  **Service (`fastapi_app/services/analysis_service.py`):**
        *   `get_code_similarity_report(graph_id: str, request: CodeSimilarityRequest)`. Loads graph (needs `clean_code`), calls `find_syntactically_similar_code`.
    4.  **Router (`fastapi_app/routers/analysis.py`):**
        *   `POST /graphs/{graph_id}/analysis/code_similarity`.
*   **Tools & Libraries:** Standard Python string/set operations. Potentially `nltk` for more advanced tokenization if desired, but simple splitting might be a good start.
*   **Data Requirements:**
    *   **Current:** `PLSQL_CodeObject.clean_code`.
    *   **Missing:** None for basic syntactic similarity.
*   **Pros:**
    *   Can find obvious copy-paste code or highly similar utility functions.
    *   Identifies clear opportunities for creating shared Java methods/classes.
*   **Cons:**
    *   Purely syntactic similarity is superficial; it won't find semantically similar code that is written differently.
    *   Can be computationally intensive (N^2 pairwise comparisons). Needs optimization for large codebases (e.g., MinHashing/LSH if scaling becomes an issue, or only compare within same package/community initially).
    *   Threshold tuning is important.
*   **Migration Use Case:** "Scan the PL/SQL codebase for procedures with >85% syntactic similarity. Review these pairs to see if they can be implemented as a single, parameterized Java utility method."

This extended roadmap provides a comprehensive vision. Each feature will require further detailed design during its specific implementation phase. Remember to adapt and re-prioritize based on evolving project needs and user feedback.