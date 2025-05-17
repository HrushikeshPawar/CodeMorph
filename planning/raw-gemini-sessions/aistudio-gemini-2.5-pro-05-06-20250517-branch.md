# Dependency Analyzer Feature Planning

## System Prompt
This is the complete code of my `CodeMorph` project.

The aim of this project is to perform LLM assisted, semi-automated code migration from Language/Framework X to Language/Framework Y

Currently, its for legacy PL/SQL (stored procedures, package and functions) to Java SpringBoot.

Now the focus for this session is on the `dependency_analyzer` package

## Me:

Uploaded `planning/gitingest/digest-20250517-f9fbb5d1827e6387b2840a4fc7a6f82e76c6431a.txt`

Help me plan various features for `dependency_analyzer` package. 

Current Features:
- Create complete dependency (call graph) for given list of `PLSQL_CodeObject`s
- Create subgraphs from given dependency graph
- Networkx graph export - graphviz and pyviz
- Some utility functions to analyze the graphs
- Primitive CLI app

Features (Planning):
- Advance graph analysis (branch analysis, grouping, Node classification, breaking graph into branches for downstream usecases, etc suggest ideas)
- FastAPI backend
- Beautiful and Robust Frontend (suggest framework - React, Vue, Streamlit, etc)

UI Requirements:
- Beautiful graph presentation (as tree)
- Clickable nodes, which would show source (and other details) as pop
- Able to create subgraphs from selected node
- Filter/Hide nodes, and similar other utils
- Robust session state to save to be able to reload on from where we left
- Take developer notes and attach to graphs, nodes, branches, groups, etc
- Suggest other such useful ui features.

Do you research and help me plan(and suggest) the proposed features.
Don't write the code it. This is a brainstorming and planning session.

## Gemini

### Thinking
The user wants to brainstorm and plan features for the `dependency_analyzer` package.
I need to consider the current features, the proposed features, and the UI requirements.
I should research and suggest ideas for:
1.  **Advanced Graph Analysis**:
    *   Branch analysis (what does this mean in the context of a call graph?)
    *   Grouping (by package, by functionality, by complexity?)
    *   Node classification (entry points, utility functions, core logic, data access?)
    *   Breaking graph into branches (identifying independent sub-systems or processing flows?)
    *   Suggest other advanced analysis features.
2.  **FastAPI Backend**: This seems straightforward, serving graph data and analysis results.
3.  **Frontend Framework**: Suggest a suitable framework based on the UI requirements.
    *   Beautiful graph presentation (as tree - though call graphs are not always trees).
    *   Clickable nodes (source code popup).
    *   Subgraph creation from UI.
    *   Filter/Hide nodes.
    *   Robust session state.
    *   Developer notes (attach to graph elements).
    *   Suggest other useful UI features.

Let's break down the thinking process:

**1. Understand the Core Goal:**
The project `CodeMorph` aims for LLM-assisted, semi-automated code migration from PL/SQL to Java SpringBoot. The `dependency_analyzer` is a key component that visualizes and helps understand the structure of the legacy PL/SQL code. This context is crucial for feature planning – features should aid in understanding complexity, identifying migration units, and tracking progress.

**2. Analyze Current Features:**
*   Complete dependency graph creation.
*   Subgraph creation.
*   NetworkX graph export (Graphviz, Pyvis).
*   Basic graph analysis utilities.
*   Primitive CLI.

This is a good foundation. The next steps are about making it more powerful for analysis and more user-friendly for interaction.

**3. Address "Advanced Graph Analysis":**

*   **Branch Analysis**:
    *   *Initial thought*: What kind of "branches"? In a call graph, this could mean:
        *   Identifying main execution paths from entry points.
        *   Isolating subgraphs that represent a distinct piece of functionality (a "feature branch" in the code, not Git).
        *   Analyzing the "reach" of a change – if I modify node X, what "branches" of the application are affected downstream?
    *   *Suggestion*: Pathfinding from specific nodes (entry points or user-selected critical nodes) to terminal nodes or other critical nodes. Visualizing these paths as distinct "branches". Analyzing the fan-out/fan-in at specific nodes to see how many branches converge or diverge.

*   **Grouping**:
    *   *Initial thought*: Group by what?
        *   PL/SQL package is an obvious one.
        *   Maybe by common prefixes if packages are structured hierarchically (e.g., `APP_CORE_UTILS`, `APP_CORE_SERVICES`).
        *   User-defined tags/groups.
        *   Automatically detected communities (using graph algorithms like Louvain community detection).
    *   *Suggestion*:
        *   **Automatic grouping**: By package (already somewhat implied by node naming), by sub-package prefixes.
        *   **Algorithmic grouping**: Community detection to find tightly coupled modules.
        *   **User-defined grouping**: Allow users to manually group nodes (e.g., "Billing Logic", "Reporting Functions") and save these groupings. This aids in semantic understanding.

*   **Node Classification**:
    *   *Initial thought*: Classify based on graph properties and PL/SQL object type.
        *   Entry points (in-degree 0).
        *   Terminal nodes (out-degree 0, excluding std lib calls).
        *   Utility nodes (high fan-out, potentially low fan-in, called by many).
        *   Hub nodes (high degree, connecting different parts of the graph).
        *   Data access nodes (if identifiable by naming convention or calls to specific DB packages, though this might need more info than just call graph).
        *   Complexity classification (e.g., based on McCabe cyclomatic complexity if that data can be parsed and stored in `PLSQL_CodeObject`, or simply by number of lines of code / number of calls made).
    *   *Suggestion*:
        *   **Structural Classification**: Entry points, terminal nodes, articulation points/bridges (nodes whose removal increases connected components).
        *   **Pattern-based Classification**: Identify common patterns like "CRUD wrappers" (if possible to infer).
        *   **Complexity Metrics**: Calculate and display metrics per node (e.g., number of calls made, number of direct/indirect callers/callees, lines of code if available in `PLSQL_CodeObject`).
        *   **User-defined tags**: Allow users to tag nodes (e.g., "To Refactor", "External API Call", "Data Transformation").

*   **Breaking Graph into Branches for Downstream Usecases**:
    *   *Initial thought*: This implies identifying "migration units" or "analysis scopes".
        *   Could be based on entry points and their complete downstream call trees.
        *   Could be based on user-selected "seed" objects and their N-degree neighborhoods.
        *   Could be based on the "groups" identified above.
    *   *Suggestion*:
        *   **Migration Unit Identification**: Algorithms to suggest cohesive subgraphs that could be migrated together. Perhaps based on minimizing inter-subgraph dependencies after a split.
        *   **Impact Analysis Scopes**: Given a set of nodes, define the "blast radius" (all affected upstream/downstream nodes within certain depths).

*   **Suggest Other Advanced Analysis Features**:
    *   *Initial thought*: What else helps in understanding and migration?
        *   **Circular Dependency Details**: Beyond just listing them, visualize the cycle clearly, show its members and their immediate non-cycle connections.
        *   **Dead Code Identification**: Nodes with in-degree 0 that are *not* designated entry points (needs a way to mark entry points).
        *   **Change Impact Simulation**: If node X is changed/removed, highlight all potentially affected nodes.
        *   **Complexity Hotspot Identification**: Nodes or subgraphs with high density of calls, many parameters, deep call stacks.
        *   **Comparison of Graphs**: If migrating iteratively, compare an older version of the graph with a newer one (e.g., after some PL/SQL refactoring before Java migration) to see what changed. (This is more advanced, maybe later).
        *   **Dependency Strength/Weight**: Are all calls equal? Maybe calls passing many parameters or complex types are "stronger" dependencies. (Requires parameter info analysis).
        *   **Path Analysis**: Shortest/longest paths between nodes, critical path analysis (if some notion of execution time or importance can be assigned).
        *   **Centrality Measures**: Degree centrality, betweenness centrality, closeness centrality to identify important nodes.

**4. FastAPI Backend:**
*   *Initial thought*: Standard REST API.
*   *Suggestion*: Endpoints for:
    *   Loading/listing available graphs.
    *   Retrieving a full graph (or its structure if large).
    *   Generating and retrieving subgraphs based on node ID, depth.
    *   Executing analysis functions (e.g., find cycles, unused objects, entry points).
    *   Saving/loading user annotations and groupings.
    *   Serving PL/SQL code for a given node.
    *   Streaming large graph data if necessary (e.g., using Server-Sent Events or WebSockets for updates if the graph is dynamically changing, though less likely for static analysis).

**5. Frontend Framework & UI Requirements:**

*   **Graph Presentation**:
    *   *Requirement*: Beautiful graph presentation (as tree).
    *   *Thought*: Call graphs are general graphs, not strictly trees. Force-directed layouts are common. Hierarchical layouts (like a tree) can be good for certain views, especially when focusing on downstream dependencies from an entry point.
    *   *Framework suitability*:
        *   **React/Vue**: Offer maximum flexibility with libraries like `react-flow`, `vis-network` (which Pyvis uses), `sigma.js`, `cytoscape.js`. More development effort.
        *   **Streamlit/Dash**: Easier for Python-heavy teams. Streamlit is simpler for rapid prototyping. Dash is more flexible for complex UIs. Both have components for network graphs (e.g., `stgraph` for Streamlit, Dash Cytoscape).
        *   Given the complexity and interactivity desired, **React or Vue** would provide the best user experience and control, but with higher dev cost. If the team is Python-centric and wants faster iteration, **Dash** is a strong contender. Streamlit might become limiting for highly custom interactions.
    *   *Suggestion*: Start with Pyvis for quick wins (as it's already used). For a more robust frontend, **React + a dedicated graph library like `react-flow` or `cytoscape.js`** is the standard for complex, interactive graph UIs. If Python backend devs are also doing frontend, **Dash (with Dash Cytoscape)** is a very good option.

*   **Clickable Nodes (Source Code Popup)**:
    *   *Thought*: Standard feature for graph viz tools. Requires backend endpoint to serve code.
    *   *Suggestion*: On node click, fetch `PLSQL_CodeObject.clean_code` (or original code if stored) and display in a modal or side panel with syntax highlighting.

*   **Subgraph Creation from UI**:
    *   *Thought*: Select node, specify upstream/downstream depth, backend generates, frontend displays.
    *   *Suggestion*: Context menu on node -> "Create Subgraph". Form for depth parameters.

*   **Filter/Hide Nodes**:
    *   *Thought*: Filter by type, package, name pattern, tags. Hide selected nodes or groups.
    *   *Suggestion*: UI controls for filtering. Option to "collapse" packages or groups into single meta-nodes.

*   **Robust Session State**:
    *   *Thought*: Browser local storage, or backend session management if more complex state.
    *   *Suggestion*: Use browser's `localStorage` or `sessionStorage` for UI state (zoom level, selected nodes, filter settings, current graph view). For persistent notes/groupings, save to backend.

*   **Developer Notes**:
    *   *Thought*: Attach text notes to nodes, edges, or user-defined groups/branches.
    *   *Suggestion*: CRUD operations for notes via backend API. UI to display/edit notes in a side panel or on hover/click.

*   **Suggest Other Useful UI Features**:
    *   *Search/Highlight*: Search for nodes by name/ID, highlight results in the graph.
    *   **Layout Options**: Allow user to switch between different graph layouts (force-directed, hierarchical, circular).
    *   **Zoom/Pan**: Standard graph navigation.
    *   **Legend**: Dynamically generated legend for node types/colors/shapes.
    *   **Export View**: Export current view as PNG/SVG.
    *   **Undo/Redo**: For actions like hiding nodes, grouping.
    *   **Contextual Information Panel**: When a node is selected, show its properties (type, package, parameters, in/out degree, LOC, complexity metrics, extracted calls, who calls it) and notes.
    *   **Path Highlighting**: Select two nodes and highlight paths between them.
    *   **Mini-map**: For large graphs.
    *   **Multi-Graph Tabs**: Ability to open and work with multiple graphs/subgraphs in different tabs within the UI.
    *   **Diff View**: (Advanced) If comparing graphs, show visual differences.
    *   **Customizable Node Appearance**: Allow users to change color/size of nodes based on attributes or tags.

**6. Research and Justify Framework Choice (Frontend):**
*   **React/Vue with dedicated graph libs (e.g., react-flow, Cytoscape.js, VisX from Airbnb)**:
    *   *Pros*: Highly customizable, rich ecosystem, excellent performance for complex interactions, widely used in industry for specialized UIs. Can achieve truly "beautiful" and fluid graph presentations.
    *   *Cons*: Steeper learning curve if the team is not familiar with JavaScript frontend frameworks. More development time.
*   **Dash (Plotly)**:
    *   *Pros*: Python-based, good for data-intensive apps, Dash Cytoscape component is powerful for network graphs. Easier integration if backend is Python/FastAPI.
    *   *Cons*: Less overall UI flexibility than pure JS frameworks for non-standard components. UI look and feel might be more "dashboard-like" unless heavily customized.
*   **Streamlit**:
    *   *Pros*: Extremely easy and fast to build simple UIs in Python. Good for PoCs or internal tools with simpler interaction needs. `stgraph` or Pyvis via HTML component can work.
    *   *Cons*: Can become limiting for complex state management, highly custom interactions, and achieving a very polished "application" feel. Session state management can be tricky for highly interactive multi-step workflows.
*   **Pyvis (current for export)**:
    *   *Pros*: Already integrated for export. Generates interactive HTML. Good for quick visualization.
    *   *Cons*: Not a full application framework. Limited for building a complete UI with state, notes, complex filtering beyond its built-in controls.

*   **Recommendation for Frontend**:
    *   If "beautiful and robust" with complex interactions like custom notes, filtering, and a polished UX is paramount, **React or Vue with a suitable graph library** is the best long-term choice.
    *   If the development team is primarily Python-focused and wants to iterate quickly while still having good graph capabilities, **Dash** is a strong alternative. It can deliver a very functional and interactive UI.
    *   Streamlit is likely too simple for the full set of UI requirements outlined.

**7. Structure the Output:**
Organize the suggestions clearly under the headings requested by the user: Advanced Graph Analysis, FastAPI Backend, Frontend Framework (with justification), and UI Feature Suggestions.

Self-correction/Refinement during thought process:
*   Initially, "branch analysis" was vague. Refined it to mean specific path analysis or feature-centric subgraphs.
*   Realized that `PLSQL_CodeObject` might not have all data for some advanced classifications (like cyclomatic complexity or detailed data access patterns). Features should be planned acknowledging current data and potential future enhancements to `plsql_analyzer`.
*   For frontend, weighed the trade-offs between ease of development (Python-based frameworks) vs. ultimate UI/UX capability (JS frameworks).
*   Emphasized that graph presentation "as tree" is one type of layout, but call graphs are general directed graphs.

This detailed thought process covers the user's request comprehensively, providing actionable suggestions and justifications.

### Output
Okay, this is an exciting stage for `CodeMorph` and specifically the `dependency_analyzer`! Let's break down the feature planning for each area.

#### Feature Planning for `dependency_analyzer`

Given the goal of migrating PL/SQL to Java SpringBoot, the `dependency_analyzer` should focus on providing deep insights into the legacy codebase's structure, complexity, and interdependencies to facilitate a smoother, more informed migration process.

#### 1. Advanced Graph Analysis

The current analysis utilities are a good start. Here are some ideas to make them more powerful for understanding and migration planning:

*   **Branch/Path Analysis:**
    *   **Execution Path Tracing:** From selected entry points (or any node), trace all possible execution paths downstream. This can help understand the scope of specific functionalities.
    *   **Critical Path Identification:** If you can assign weights to nodes/edges (e.g., based on complexity, estimated migration effort, or even runtime if available), identify critical paths that might represent core functionalities or high-risk areas.
    *   **Reachability Analysis:** Determine all nodes reachable from a given node (and vice-versa) within N degrees or fully. This is useful for impact analysis.

*   **Grouping & Clustering:**
    *   **Package-Based Grouping (Visual & Analytical):** While nodes might be named with packages, allow collapsing/expanding package groups in visualizations. Analyze dependencies *between* packages (inter-package coupling) versus *within* packages (intra-package cohesion).
    *   **Community Detection:** Implement algorithms (e.g., Louvain, Girvan-Newman) to automatically detect densely connected subgraphs (communities/modules). These could represent logical components or potential microservices in the target architecture.
    *   **User-Defined Grouping:** Allow users to manually group nodes (e.g., "Billing Logic," "Reporting Procedures," "User Authentication") and save these logical groupings. This helps overlay business domain knowledge onto the technical graph.

*   **Node Classification & Metrics:**
    *   **Automated Classification:**
        *   **Entry Points:** Nodes with in-degree 0 (already have `find_entry_points`).
        *   **Terminal Points:** Nodes with out-degree 0 (excluding calls to standard/external libraries, already have `find_terminal_nodes`).
        *   **Hubs/Connectors:** Nodes with high degree, high betweenness centrality, or high PageRank, indicating they are critical for connectivity.
        *   **Utility Nodes:** Nodes with high fan-out but relatively low complexity themselves, called by many other modules.
        *   **Orphaned Components:** Weakly connected components that are small and not connected to the main graph could be dead code or very isolated utilities.
    *   **Complexity Metrics per Node:**
        *   **Cyclomatic Complexity (if feasible):** If `plsql_analyzer` could extract this, it would be invaluable. Otherwise, approximate complexity (e.g., lines of code in the object, number of distinct calls made, number of parameters).
        *   **Number of Callers (In-Degree) / Callees (Out-Degree):** Already available.
        *   **Depth/Reach:** Max call stack depth originating from/leading to this node.
    *   **Dependency Strength:** Potentially weight edges based on factors like the number of parameters passed, or frequency of calls (if dynamic analysis data were available, though unlikely for legacy PL/SQL analysis here).

*   **Breaking Graph into Migration Units:**
    *   **Identifying Cohesive Subgraphs:** Use community detection or user-defined groups as starting points for potential migration units.
    *   **Minimizing Inter-Unit Dependencies:** Analyze how "chopping" the graph at certain points would affect the number of dependencies between the resulting chunks. This helps define cleaner bounded contexts for migration.
    *   **Strangler Fig Pattern Support:** Identify service interface candidates – procedures/functions that are called by many external parts of the system and could be the first to be wrapped or reimplemented in Java.

*   **Other Advanced Analysis Ideas:**
    *   **Circular Dependency Analysis:**
        *   Beyond detection, visualize cycles clearly.
        *   Rank cycles by size or by the "importance" of nodes within them.
        *   Suggest potential break points for cycles.
    *   **Impact Analysis ("What if?"):**
        *   Select a node and simulate its removal or change: highlight all directly and indirectly affected upstream (callers) and downstream (callees) objects.
    *   **Anti-Pattern Detection:**
        *   Look for known PL/SQL anti-patterns that might complicate migration (e.g., overly large packages, excessive use of global package state if discernible, "god" procedures with too many responsibilities).
    *   **Code Similarity/Clustering (Content-Based):** (More advanced, might need LLM assistance itself) If `PLSQL_CodeObject` stores `clean_code`, you could try to find structurally or semantically similar code objects, which might be candidates for consolidation in the new system.
    *   **Change Propagation Path:** For a given node, visualize the shortest/most common paths through which changes to its dependencies might affect it, or how changes to it might affect others.

#### 2. FastAPI Backend

This is a solid choice for providing data to a modern frontend.

*   **Core Endpoints:**
    *   `GET /graphs`: List available processed graphs (perhaps from the `GRAPHS_DIR`).
    *   `GET /graphs/{graph_id}`: Retrieve a specific graph (full data or structure-only based on query params). Consider pagination for very large graphs if returning full node/edge lists.
    *   `POST /graphs/subgraph`: Create a subgraph based on `node_id`, `upstream_depth`, `downstream_depth`. Return the subgraph.
    *   `GET /graphs/{graph_id}/nodes/{node_id}/code`: Retrieve the `clean_code` (or original source if stored) for a specific PL/SQL object.
    *   `GET /graphs/{graph_id}/analysis/{analysis_type}`: Perform server-side analysis (e.g., `cycles`, `entry_points`, `terminal_nodes`, `communities`).
        *   Example: `GET /graphs/main_graph/analysis/cycles`
        *   Example: `GET /graphs/main_graph/analysis/node_classification`
    *   `POST /graphs/{graph_id}/nodes/{node_id}/notes`: Add/update notes for a node.
    *   `GET /graphs/{graph_id}/nodes/{node_id}/notes`: Retrieve notes.
    *   `POST /graphs/{graph_id}/groups`: Create/update user-defined groups of nodes.
    *   `GET /graphs/{graph_id}/groups`: List user-defined groups.

*   **Data Serialization:**
    *   Use Pydantic models for request and response bodies to ensure data validation and clear API contracts.
    *   For graph data, the node-link format (as used by `nx.node_link_data`) is generally good for web frontends.

*   **Async Operations:** If some analysis tasks are very time-consuming, consider using FastAPI's `async def` and potentially background tasks for those.

#### 3. Frontend Framework & UI Requirements

Given your UI requirements for a "beautiful and robust" interface with complex interactions, here's a breakdown:

*   **Framework Suggestion:**
    *   **React** or **Vue.js** are the strongest contenders for this level of customization and interactivity. They have rich ecosystems and powerful graph visualization libraries.
        *   **Graph Libraries:** `React Flow`, `Cytoscape.js` (can be used with React/Vue wrappers), `Vis.js Network` (which Pyvis uses under the hood, but direct usage offers more control), `Sigma.js`, or even D3.js for completely custom visualizations.
        *   **Pros:** Maximum flexibility, best performance for dynamic graph interactions, large community, many pre-built UI components.
        *   **Cons:** Requires JavaScript/TypeScript frontend expertise.
    *   **Dash (by Plotly):** If your team is primarily Python-based, Dash is an excellent alternative. It allows building complex, interactive web applications purely in Python.
        *   **Graph Component:** `dash-cytoscape` is very powerful and provides a lot of the needed graph interactivity.
        *   **Pros:** Python-native, good for data-heavy applications, faster development if Python expertise is already strong.
        *   **Cons:** While flexible, achieving a highly bespoke "beautiful" UI might require more CSS/custom component work than with pure JS frameworks.
    *   **Streamlit:** Likely too simplistic for the full range of UI interactions and state management you're aiming for (especially session state, complex filtering, and note-taking attached to graph elements). Good for quick PoCs but might hit limitations.

    **Recommendation:** If you have or can acquire frontend expertise, **React/Vue + React Flow/Cytoscape.js** will give the best results for a polished, highly interactive application. If the team is Python-centric and wants to move fast, **Dash** is a very capable second choice.

*   **UI Requirements & Feature Suggestions:**

    *   **Beautiful Graph Presentation (as tree or general graph):**
        *   Support for various layouts: force-directed (default), hierarchical/tree (for specific explorations like downstream from an entry point), circular, layered.
        *   Smooth animations for layout changes, zoom, pan.
        *   Customizable node appearance (color, shape, size, icons) based on type, package, complexity, or user tags.
        *   Edge styling (thickness, color, arrows, labels for call counts if available).
        *   **Mini-map** for navigating large graphs.
        *   **Highlighting**: Neighbors, paths, search results.

    *   **Clickable Nodes (Source Code Popup & Info Panel):**
        *   On click:
            *   Open a modal or a dedicated side panel.
            *   Display node details: ID, full name, package, type, parameters, return type (for functions).
            *   Display PL/SQL source code with syntax highlighting.
            *   Show graph metrics: in-degree, out-degree, complexity score.
            *   List direct callers and callees (clickable to navigate).
            *   Area for developer notes (see below).

    *   **Able to Create Subgraphs from Selected Node:**
        *   Right-click context menu on a node: "Explore Subgraph".
        *   Modal to specify upstream/downstream depth.
        *   Option to open subgraph in a new tab/view or replace current view.

    *   **Filter/Hide Nodes and Similar Utilities:**
        *   **Filter Panel:**
            *   By node type (Procedure, Function, Package, etc.).
            *   By package name (checkbox list, text search).
            *   By node name (regex/substring search).
            *   By user-defined tags/groups.
            *   By complexity metrics (e.g., show only nodes with > N callers).
        *   **Hide/Show:** Option to hide selected nodes/groups temporarily.
        *   **Collapse/Expand:** Collapse all nodes within a package into a single meta-node, expandable on click. Same for user-defined groups or detected communities.
        *   **Isolate Node/Group:** Hide everything *except* the selected node(s) and their direct neighborhood (or specified degree).

    *   **Robust Session State:**
        *   Browser `localStorage` or `sessionStorage` for:
            *   Current graph view (graph ID, applied filters, zoom/pan state, layout settings).
            *   Last selected nodes or explored subgraphs.
            *   UI theme/preferences.
        *   Backend storage for persistent items like user-defined groups and notes.

    *   **Take Developer Notes:**
        *   Attach notes to:
            *   Individual nodes (e.g., "Needs refactoring", "Key business logic here", "Migrate this to XService in Java").
            *   Edges (e.g., "Complex data transfer via this call").
            *   User-defined groups or subgraphs (e.g., "Migration Wave 1 candidates").
        *   Simple rich text editor for notes.
        *   Notes displayed in the info panel and potentially as visual cues on the graph.
        *   Searchable notes.

    *   **Other Useful UI Features:**
        *   **Global Search:** Search across all node names, IDs, packages, and potentially notes.
        *   **Legend:** Clear, dynamic legend explaining node colors, shapes, and any other visual encodings.
        *   **Undo/Redo Stack:** For UI actions like filtering, hiding, grouping.
        *   **Export Options:**
            *   Export current graph view as PNG, SVG.
            *   Export graph data (nodes/edges of current view) as CSV or JSON.
        *   **Side-by-Side View:** (Advanced) Ability to show two graphs or subgraphs side-by-side for comparison.
        *   **Path Finding UI:** Select two nodes and have the UI highlight one or all simple paths between them.
        *   **Loading Indicators/Progress Bars:** For graph loading and analysis operations.
        *   **Theming:** Light/dark mode.
        *   **Help/Documentation Panel:** Quick access to explanations of features and metrics.

This detailed plan should provide a good roadmap for enhancing the `dependency_analyzer`. Remember to prioritize features based on what provides the most value for the PL/SQL to Java migration task. Good luck!

## Me
Lets focus on `1. Advanced Graph Analysis`

Study the current implementation of `PLSQ_CodeObject` and what we are currently extracting and storing, the Graph Constructor, of what all is their in the graph.

For each point/subpoint mentioned - Do a feasibility analysis and create a thorough implementation plan (with required lib and tools) and point out missing data. Also note the pros and cons and use of that particular feature in detail. Do required research and be thorugh and detailed.

## Gemini
### Thinking
The user wants a detailed breakdown of each "Advanced Graph Analysis" feature.
For each feature, I need to:
1.  **Analyze Feasibility:**
    *   Check if `PLSQL_CodeObject` (as defined in `plsql_analyzer/core/code_object.py`) and the `GraphConstructor` (from `dependency_analyzer/builder/graph_constructor.py`) provide the necessary data.
    *   Identify any missing data points that would need to be extracted by `plsql_analyzer` or computed.
2.  **Create a Thorough Implementation Plan:**
    *   Outline the steps to implement the feature.
    *   Suggest relevant Python libraries (primarily NetworkX functions if applicable, or others).
    *   Mention any specific algorithms or techniques.
3.  **Point Out Missing Data:** Explicitly list what's not currently available.
4.  **Detail Pros, Cons, and Use Cases:**
    *   **Pros:** Benefits of having this feature.
    *   **Cons:** Potential drawbacks, complexities, or limitations.
    *   **Use Case:** How this feature aids in the PL/SQL to Java SpringBoot migration.

Let's examine the current state first:

**Current Data in `PLSQL_CodeObject`:**
*   `id`: String (e.g., `package_name.name` or `package_name.name-hash_if_overloaded`)
*   `name`: String (casefolded)
*   `package_name`: String (casefolded, or empty)
*   `clean_code`: Optional String (cleaned PL/SQL source)
*   `literal_map`: Optional Dict (mapping placeholders in `clean_code` to original literals)
*   `type`: `CodeObjectType` (PACKAGE, PROCEDURE, FUNCTION, TRIGGER, TYPE, UNKNOWN)
*   `overloaded`: Boolean
*   `parsed_parameters`: List of Dicts (e.g., `{'name': 'p_id', 'type': 'NUMBER', 'mode': 'IN', 'default_value': '1'}`)
*   `parsed_return_type`: Optional String
*   `extracted_calls`: List of `CallDetailsTuple` (`call_name`, `line_no`, `start_idx`, `end_idx`, `positional_params`, `named_params`)
*   `start_line`: Optional Int
*   `end_line`: Optional Int

**Current Graph Structure (from `GraphConstructor`):**
*   Nodes: Node ID is `PLSQL_CodeObject.id`.
*   Node Attributes: `object` (the `PLSQL_CodeObject` instance itself).
*   Edges: Represent a call from the source object to the target object. Edges are unweighted and don't currently store call-specific details (like parameters used in that specific call instance).

**Current Analysis Capabilities (from `analyzer.py`):**
*   `find_unused_objects` (in-degree 0)
*   `find_circular_dependencies` (simple cycles)
*   `generate_subgraph_for_node` (based on upstream/downstream depth)
*   `find_entry_points` (same as unused)
*   `find_terminal_nodes` (out-degree 0, can exclude placeholders)
*   `get_node_degrees`
*   `find_all_paths`
*   `get_connected_components` (strongly/weakly)

Now, let's go through each advanced analysis feature.

### Output
Okay, let's dive deep into each "Advanced Graph Analysis" feature, considering your current `PLSQL_CodeObject` structure and `GraphConstructor`.

**Recap of Available Data:**

*   **`PLSQL_CodeObject` Attributes:** `id`, `name`, `package_name`, `clean_code`, `literal_map`, `type` (enum), `overloaded` (bool), `parsed_parameters` (list of dicts with name, type, mode, default), `parsed_return_type`, `extracted_calls` (list of `CallDetailsTuple` including call name and *parsed actual parameters* of the call), `start_line`, `end_line`.
*   **Graph Node Attributes:** The full `PLSQL_CodeObject` instance is stored under the `object` attribute of each node.
*   **Graph Edge Attributes:** Currently, edges are simple connections without additional attributes from `CallDetailsTuple` (e.g., the specific parameters used for *that specific call instance* that forms the edge).

---

#### 1. Branch/Path Analysis

#### a. Execution Path Tracing

*   **Description:** From a selected entry point (or any node), trace all possible execution paths downstream.
*   **Feasibility:**
    *   **Current Data:** Sufficient. The graph structure (nodes and directed edges) directly represents call sequences.
    *   **Missing Data:** None for basic path tracing.
*   **Implementation Plan:**
    *   **Tool:** NetworkX.
    *   **Algorithm:**
        1.  Identify the starting node.
        2.  Use graph traversal algorithms like Depth-First Search (DFS) or Breadth-First Search (BFS) to find all reachable nodes.
        3.  NetworkX has `nx.all_simple_paths(graph, source, target)` if a specific target is known. To find all paths *from* a source without a predefined target, you'd typically use DFS and collect paths as you traverse.
        4.  `nx.dfs_edges(graph, source, depth_limit)` or `nx.bfs_edges(graph, source, depth_limit)` can give edges in traversal order, which can be used to reconstruct paths.
        5.  For "all possible execution paths," if cycles exist, this can mean infinite paths. The focus should be on *simple paths* (no repeated nodes, except possibly the start/end for a cycle containing the start) or paths up to a certain length/depth.
*   **Pros:**
    *   Helps understand the full scope of functionality initiated by an entry point.
    *   Useful for identifying all components involved in a specific business process if the entry point maps to one.
    *   Aids in test case generation for the migrated system by showing all reachable code.
*   **Cons:**
    *   Can be computationally intensive and visually overwhelming for large graphs or nodes with high fan-out.
    *   Infinite paths in case of cycles need careful handling (e.g., limiting path length or showing only simple paths).
*   **Use Case (Migration):**
    *   When migrating a specific feature, tracing from its main PL/SQL entry points helps define the boundary of that feature's code.
    *   Helps ensure all dependent procedures/functions are considered during the migration of a particular module.

#### b. Critical Path Identification

*   **Description:** Identify paths that are "critical," potentially based on node/edge weights (complexity, migration effort, runtime).
*   **Feasibility:**
    *   **Current Data:** Graph structure is available. Node/edge weights are *missing*.
    *   **Missing Data:**
        *   **Node Complexity:** Need a metric for PL/SQL object complexity.
            *   `PLSQL_CodeObject.clean_code` (length can be a proxy: Lines of Code - LOC).
            *   Number of parameters (`len(PLSQL_CodeObject.parsed_parameters)`).
            *   Number of calls made (`len(PLSQL_CodeObject.extracted_calls)`).
            *   (Ideal but hard for PL/SQL without dedicated tools: Cyclomatic Complexity).
        *   **Edge Weight/Importance:**
            *   Could be uniform (1 for each call).
            *   Could be based on the complexity of the *target* node.
            *   (Ideal but complex: frequency of call if dynamic analysis data were available, or perhaps LLM-estimated importance).
        *   **Migration Effort (Manual/Estimated):** Users might need to annotate nodes/edges with estimated effort.
*   **Implementation Plan:**
    *   **Step 1: Define & Compute Weights:**
        *   Add a function to calculate a complexity score for each `PLSQL_CodeObject` and store it as a node attribute (e.g., `graph.nodes[node_id]['complexity_score']`).
        *   Define how edge weights will be determined (e.g., `1/complexity_score` if looking for shortest paths of complex objects, or just `complexity_score` if summing path complexity).
    *   **Tool:** NetworkX.
    *   **Algorithm:**
        1.  Once weights are assigned (e.g., edge weight representing "cost" or "length").
        2.  Use algorithms like `nx.shortest_path(graph, source, target, weight='weight')` or `nx.all_shortest_paths()`.
        3.  If "critical" means "longest path" in an acyclic graph (DAG), this can be found. For graphs with cycles, "longest simple path" is NP-hard.
        4.  Alternatively, path "criticality" could be the sum of node complexities along the path. Iterate through paths from `nx.all_simple_paths` and sum node weights.
*   **Pros:**
    *   Focuses migration efforts on the most complex or impactful parts of the application first.
    *   Helps in risk assessment by identifying high-effort or high-dependency paths.
*   **Cons:**
    *   Defining accurate weights can be subjective or require significant upfront effort.
    *   "Longest path" is computationally hard for general graphs. Focus on critical paths between specific start/end points or based on accumulated weights.
*   **Use Case (Migration):**
    *   Prioritize migrating procedures/functions that lie on paths with high cumulative complexity.
    *   Helps in phasing the migration: tackle critical backbone paths first.

#### c. Reachability Analysis

*   **Description:** Determine all nodes reachable from a given node (and vice-versa).
*   **Feasibility:**
    *   **Current Data:** Sufficient.
    *   **Missing Data:** None.
*   **Implementation Plan:**
    *   **Tool:** NetworkX.
    *   **Algorithm:**
        *   **Downstream Reachability:** `nx.descendants(graph, source_node)` returns a set of all nodes reachable from `source_node`.
        *   **Upstream Reachability (who can reach a node):** `nx.ancestors(graph, target_node)` returns a set of all nodes that have a path to `target_node`.
        *   **Within N degrees:**
            *   Use `nx.bfs_tree(graph, source, depth_limit=N)` to get a tree of reachable nodes within N levels. Nodes of this tree are the reachable nodes.
            *   For upstream within N degrees, use `nx.bfs_tree(graph.reverse(), target, depth_limit=N)`.
*   **Pros:**
    *   Essential for impact analysis: "If I change X, what is affected downstream?"
    *   Helps define module boundaries: "What components are tightly coupled with X?"
*   **Cons:**
    *   For highly connected graphs, the set of reachable nodes can be very large.
*   **Use Case (Migration):**
    *   When planning to migrate a specific PL/SQL object, `descendants` shows everything that might break if its interface changes.
    *   `ancestors` shows all code that would need to be updated if this object is replaced or its calling signature changes in the new Java system.

---

#### 2. Grouping & Clustering

#### a. Package-Based Grouping (Visual & Analytical)

*   **Description:** Allow collapsing/expanding package groups in visualizations. Analyze dependencies between and within packages.
*   **Feasibility:**
    *   **Current Data:** `PLSQL_CodeObject.package_name` is available.
    *   **Missing Data:** None for basic grouping.
*   **Implementation Plan:**
    *   **Visual (Frontend):** The frontend visualization library (React Flow, Cytoscape.js, Dash Cytoscape) would handle this. Nodes can be tagged with their package name, and the library can provide functionality to group/collapse nodes based on this tag.
    *   **Analytical (Backend):**
        1.  Create a "meta-graph" where each node is a package.
        2.  An edge exists between package A and package B if any object in A calls an object in B.
        3.  Edge weight could be the number of such inter-package calls.
        4.  Analyze this meta-graph for metrics like inter-package coupling (number of edges/dependencies between packages) and intra-package cohesion (density of calls within objects of the same package).
        *   **Cohesion Formula (Example):** For a package, (actual internal edges) / (max possible internal edges).
        *   **Coupling Metric:** Number of external dependencies (in/out) for a package.
*   **Pros:**
    *   Aligns with common PL/SQL organizational structure.
    *   Helps identify packages that are good candidates for migration as a whole unit.
    *   Highlights overly coupled packages that might need refactoring before or during migration.
*   **Cons:**
    *   Packages can be very large; simply grouping by package might still result in large visual clusters.
*   **Use Case (Migration):**
    *   Migrate cohesive, loosely coupled packages as individual modules/microservices.
    *   Identify packages with high external dependencies that might require careful interface design during migration.

#### b. Community Detection

*   **Description:** Automatically detect densely connected subgraphs (communities/modules).
*   **Feasibility:**
    *   **Current Data:** Graph structure is sufficient.
    *   **Missing Data:** None, though edge weights (if meaningful ones could be derived) could improve some algorithms.
*   **Implementation Plan:**
    *   **Tool:** NetworkX `algorithms.community`.
    *   **Algorithms:**
        *   **Louvain Algorithm:** `nx.community.louvain_communities(graph, weight=None, resolution=1.0)` - Fast and widely used for large networks. Resolution parameter can be tuned.
        *   **Girvan-Newman:** `nx.community.girvan_newman(graph)` - Edge-betweenness based, good quality but computationally expensive for large graphs. Yields a hierarchy of communities.
        *   **Label Propagation:** `nx.community.label_propagation_communities(graph)` - Very fast.
    *   **Output:** These algorithms typically return a list of sets, where each set contains the node IDs belonging to a community.
    *   **Integration:** Store community membership as a node attribute (e.g., `graph.nodes[node_id]['community_id'] = community_label`).
*   **Pros:**
    *   Objectively identifies potential logical modules within the codebase, even if not explicitly structured as such by packages.
    *   Can reveal hidden structures or relationships.
    *   Provides data-driven suggestions for microservice boundaries.
*   **Cons:**
    *   Choice of algorithm and its parameters (like resolution in Louvain) can significantly affect results. Experimentation is needed.
    *   Detected communities may not always align perfectly with business domain logic.
*   **Use Case (Migration):**
    *   Detected communities can be strong candidates for initial microservice decomposition in the target Java architecture.
    *   Helps understand the "natural" seams in the legacy system for splitting migration efforts.

#### c. User-Defined Grouping

*   **Description:** Allow users to manually group nodes and save these logical groupings.
*   **Feasibility:**
    *   **Current Data:** Node IDs are available.
    *   **Missing Data:** A mechanism to store and retrieve these user-defined groups is needed (likely in a separate database table or as graph attributes if the graph storage format supports complex attributes well).
*   **Implementation Plan:**
    *   **Backend (FastAPI):**
        *   Endpoints to create, read, update, delete groups.
        *   A group could be: `group_id`, `group_name`, `list_of_node_ids`.
        *   Store this in a new SQLite table or a NoSQL document store.
    *   **Frontend:** UI to select multiple nodes and assign them to a new or existing group. Display nodes with group-based coloring/styling.
    *   **Graph Integration:** When loading a graph, also load its associated user-defined groups and add a `user_group_id` attribute to relevant nodes.
*   **Pros:**
    *   Allows overlaying crucial business domain knowledge onto the technical call graph.
    *   Facilitates collaborative understanding and planning among team members.
    *   Groups can directly inform migration waves or team assignments.
*   **Cons:**
    *   Manual effort required.
    *   Consistency of grouping depends on user understanding.
*   **Use Case (Migration):**
    *   Developers can group objects based on features (e.g., "All PL/SQL related to 'Order Processing'").
    *   Plan migration by these logical groups, making it easier to communicate scope.

---

#### 3. Node Classification & Metrics

#### a. Automated Classification

*   **Entry Points:**
    *   **Current:** `find_entry_points` (in-degree 0) exists. Sufficient.
*   **Terminal Points:**
    *   **Current:** `find_terminal_nodes` (out-degree 0, can exclude UNKNOWN type) exists. Sufficient.
*   **Hubs/Connectors:**
    *   **Description:** Nodes critical for connectivity (high degree, betweenness centrality, PageRank).
    *   **Feasibility:**
        *   **Current Data:** Graph structure is sufficient.
        *   **Missing Data:** None.
    *   **Implementation Plan (Tool: NetworkX):**
        *   **Degree Centrality:** `nx.degree_centrality(graph)` (or just `graph.degree()`).
        *   **Betweenness Centrality:** `nx.betweenness_centrality(graph, k=None, normalized=True, weight=None)` (Can be slow for large graphs; `k` can sample paths for approximation).
        *   **PageRank:** `nx.pagerank(graph, alpha=0.85)`.
        *   Define thresholds or take top N% to classify nodes as hubs. Store as a node attribute (e.g., `node_role: 'hub'`).
    *   **Pros:** Identifies critical integration points or overly central objects.
    *   **Cons:** Centrality calculations can be slow on very large graphs.
    *   **Use Case (Migration):** Hubs might be complex to migrate due to many dependencies or might become key API gateways in the new architecture. They require careful planning.
*   **Utility Nodes:**
    *   **Description:** High fan-out, relatively low complexity, called by many.
    *   **Feasibility:**
        *   **Current Data:** Out-degree available. Complexity metric is *missing*.
        *   **Missing Data:** Node complexity score (see "Critical Path Identification").
    *   **Implementation Plan:**
        1.  Calculate node complexity (e.g., LOC from `clean_code`, num_params, num_calls_made).
        2.  Identify nodes with out-degree > threshold_out AND complexity < threshold_complexity.
        3.  Store as `node_role: 'utility'`.
    *   **Pros:** Highlights reusable components.
    *   **Cons:** Defining "low complexity" can be subjective.
    *   **Use Case (Migration):** Utility procedures/functions are often good candidates for early migration to shared Java libraries.
*   **Orphaned Components:**
    *   **Description:** Small, weakly connected components not linked to the main graph.
    *   **Feasibility:**
        *   **Current Data:** `get_connected_components(graph, strongly_connected=False)` provides WCCs.
        *   **Missing Data:** None.
    *   **Implementation Plan:**
        1.  Get all Weakly Connected Components (WCCs).
        2.  Identify the largest WCC as the "main graph."
        3.  Other WCCs, especially if small (e.g., < 5 nodes), are potential orphans.
        4.  Store as `node_role: 'orphan_component_member'`.
    *   **Pros:** Helps find potentially dead or obsolete code.
    *   **Cons:** Small WCCs might still be valid, externally called utilities not linked in the static analysis.
    *   **Use Case (Migration):** Orphaned components should be investigated; they might not need migration or could be deprecated.

#### b. Complexity Metrics per Node

*   **Description:** Quantify complexity of each PL/SQL object.
*   **Feasibility:**
    *   **Current Data:**
        *   `PLSQL_CodeObject.clean_code`: Can be used for Lines of Code (LOC).
        *   `PLSQL_CodeObject.parsed_parameters`: `len()` gives number of parameters.
        *   `PLSQL_CodeObject.extracted_calls`: `len()` gives number of distinct calls made from this object.
        *   `graph.in_degree(node_id)`, `graph.out_degree(node_id)`.
    *   **Missing Data:**
        *   **Cyclomatic Complexity:** Very hard to calculate accurately for PL/SQL without a dedicated parser for its control flow graph. An approximation might be possible by counting keywords like `IF`, `LOOP`, `CASE`, `GOTO`, etc., in `clean_code`.
*   **Implementation Plan:**
    1.  **LOC:** `loc = len(obj.clean_code.splitlines()) if obj.clean_code else 0`.
    2.  **NumParams:** `num_params = len(obj.parsed_parameters)`.
    3.  **NumCallsMade:** `num_calls_made = len(obj.extracted_calls)`.
    4.  **Approximate Cyclomatic Complexity (ACC):**
        *   Count occurrences of keywords (`IF`, `ELSIF`, `CASE WHEN`, `LOOP`, `FOR`, `WHILE`, `EXCEPTION WHEN`) in `clean_code`.
        *   ACC = (count of decision points) + 1. This is a very rough estimate.
    5.  Store these as node attributes: `graph.nodes[node_id]['loc']`, `graph.nodes[node_id]['num_params']`, etc.
*   **Pros:** Provides quantitative measures for comparing and prioritizing objects.
*   **Cons:** ACC is a rough estimate. LOC can be misleading (e.g., lots of comments vs. dense logic).
*   **Use Case (Migration):** High complexity objects require more effort and testing. Can be used to distribute work or identify refactoring candidates *before* migration.

#### c. Depth/Reach

*   **Description:** Max call stack depth originating from/leading to this node.
*   **Feasibility:**
    *   **Current Data:** Sufficient.
    *   **Missing Data:** None.
*   **Implementation Plan (Tool: NetworkX):**
    *   **Max Downstream Depth (Longest path *from* this node in a DAG):**
        1.  If the graph is a DAG: `nx.dag_longest_path_length(graph, source_node)` (if you consider each node as a source, or overall if you mean longest path starting at `source_node`).
        2.  For a specific node, find the length of the longest simple path starting from it. Can be complex if cycles. A simpler metric: number of descendants.
    *   **Max Upstream Depth (Longest path *to* this node in a DAG):**
        1.  Similar to downstream, but on `graph.reverse()`.
    *   A more practical approach for general graphs might be to define "reach" as the number of descendants/ancestors, or the depth limit required in BFS/DFS to reach all of them.
*   **Pros:** Indicates how deeply embedded a function is within call chains.
*   **Cons:** "Longest path" is tricky with cycles. Number of descendants/ancestors might be more robust.
*   **Use Case (Migration):** Deeply nested functions might be harder to test in isolation. Understanding their call depth helps in planning integration testing.

---

#### 4. Breaking Graph into Migration Units

#### a. Identifying Cohesive Subgraphs

*   **Description:** Use community detection or user-defined groups.
*   **Feasibility:**
    *   **Current Data:** Covered by Community Detection and User-Defined Grouping.
    *   **Missing Data:** None beyond what's needed for those features.
*   **Implementation Plan:** This is more about *applying* the results of community detection and user-defined grouping. The UI would allow users to select a community/group and visualize it as a distinct unit.
*   **Pros:** Provides natural, data-driven or domain-driven units for migration.
*   **Cons:** Boundaries might still need manual adjustment.
*   **Use Case (Migration):** These subgraphs become the primary candidates for "migration waves" or assignment to specific development teams.

#### b. Minimizing Inter-Unit Dependencies

*   **Description:** Analyze how "chopping" the graph affects dependencies between chunks.
*   **Feasibility:**
    *   **Current Data:** Graph structure. Relies on having defined "chunks" (from communities, packages, or user groups).
    *   **Missing Data:** None, assuming chunks are defined.
*   **Implementation Plan:**
    1.  Given a partitioning of nodes into chunks (e.g., list of lists of node IDs).
    2.  For each pair of chunks (C1, C2), count the number of edges going from a node in C1 to a node in C2. This is inter-chunk dependency.
    3.  The goal is to find partitions that minimize this sum. This is related to graph partitioning algorithms (e.g., Kernighan-Lin, spectral partitioning), which can be complex.
    4.  A simpler approach: start with an initial partitioning (e.g., from Louvain) and provide metrics on inter-chunk calls. Allow users to iteratively refine by moving nodes between chunks and see updated metrics.
    *   **Tool:** NetworkX for graph manipulation. Custom logic for metrics.
*   **Pros:** Leads to more independent, less coupled microservices or modules in the target architecture. Reduces ripple effects of changes during and after migration.
*   **Cons:** Optimal graph partitioning is NP-hard. Heuristics or iterative refinement are needed.
*   **Use Case (Migration):** Design Java services/modules that correspond to these low-dependency chunks, minimizing the need for complex inter-service communication or shared libraries during the initial migration phases.

#### c. Strangler Fig Pattern Support

*   **Description:** Identify service interface candidates – objects called by many external parts, suitable for wrapping or early reimplementation.
*   **Feasibility:**
    *   **Current Data:** In-degree of nodes. Package information.
    *   **Missing Data:** None for a basic identification.
*   **Implementation Plan:**
    1.  Identify nodes with high in-degree, especially those called by objects from *different* packages or communities (these are cross-cutting concerns).
    2.  These are potential candidates for the "strangler fig" facade.
    3.  The `PLSQL_CodeObject.parsed_parameters` and `parsed_return_type` are crucial for defining the Java interface for the new service that will replace/wrap this PL/SQL object.
*   **Pros:** Provides a clear strategy for incremental migration, reducing risk.
*   **Cons:** Identifying the *right* facade requires domain knowledge in addition to graph metrics.
*   **Use Case (Migration):** Select a high-traffic, widely used PL/SQL procedure. Create a Java Spring Boot service that exposes the same functionality (either by calling the old PL/SQL via JDBC initially, or by reimplementing it). Gradually redirect callers to the new Java service.

---

#### 5. Other Advanced Analysis Ideas

#### a. Circular Dependency Analysis

*   **Description:** Beyond detection, visualize cycles clearly, rank them, suggest break points.
*   **Feasibility:**
    *   **Current Data:** `find_circular_dependencies` exists.
    *   **Missing Data:** Node complexity/importance for ranking cycles.
*   **Implementation Plan:**
    *   **Visualization:** Frontend task. Highlight nodes and edges forming a cycle.
    *   **Ranking:**
        *   Rank by size (number of nodes/edges in the cycle).
        *   Rank by "average complexity" of nodes in the cycle (needs node complexity metric).
    *   **Suggest Break Points:** This is challenging. Heuristics could be:
        *   The edge within the cycle whose removal would result in the "least important" link being broken (e.g., based on complexity of involved nodes, or an edge with fewest parameters if that data were on edges).
        *   Nodes within the cycle that have the fewest dependencies *outside* the cycle.
        *   Requires more sophisticated analysis, possibly interactive user input.
*   **Pros:** Helps untangle complex parts of the codebase, which is crucial for migration to a typically less cycle-prone architecture like Spring Boot services.
*   **Cons:** Automatically suggesting good break points is non-trivial.
*   **Use Case (Migration):** Cycles must be broken for a clean migration. This feature helps prioritize which cycles to tackle and how.

#### b. Impact Analysis ("What if?")

*   **Description:** Select a node, simulate removal/change, highlight affected upstream/downstream.
*   **Feasibility:**
    *   **Current Data:** `nx.descendants` and `nx.ancestors` (from Reachability Analysis) provide this.
    *   **Missing Data:** None for basic impact.
*   **Implementation Plan:**
    *   UI selects a node.
    *   Backend uses `nx.descendants(graph, node)` for downstream impact.
    *   Backend uses `nx.ancestors(graph, node)` for upstream impact.
    *   Frontend highlights these sets of nodes.
*   **Pros:** Excellent for planning changes and understanding risks.
*   **Cons:** Can be visually noisy if the impact set is large.
*   **Use Case (Migration):** "If we migrate `PROC_A` to Java and its interface changes, which PL/SQL callers (`ancestors`) need to be updated to call the Java version? Which PL/SQL procedures called by `PROC_A` (`descendants`) also need to be considered in this migration unit?"

#### c. Anti-Pattern Detection

*   **Description:** Look for known PL/SQL anti-patterns.
*   **Feasibility:**
    *   **Current Data:** Some can be inferred:
        *   **Overly Large Packages:** Number of `PLSQL_CodeObject`s with the same `package_name`.
        *   **"God" Procedures:** High complexity score, high in-degree, high out-degree.
    *   **Missing Data:**
        *   **Global Package State:** `plsql_analyzer` would need to identify package-level variables and track their usage (reads/writes) across procedures/functions within that package. This is a significant addition.
        *   Specific DML patterns, cursor usage patterns within `clean_code`.
*   **Implementation Plan:**
    *   Define rules for each anti-pattern based on available metrics and graph structure.
    *   Example Rule (God Procedure): `complexity_score > X AND in_degree > Y AND out_degree > Z`.
    *   For global state, `plsql_analyzer` would need enhancement. Then, `dependency_analyzer` would look for packages where many internal objects reference these package-level variables.
*   **Pros:** Proactively identifies problematic code structures that will be difficult to migrate directly.
*   **Cons:** Defining robust rules for anti-patterns can be complex. Analysis of `clean_code` content can be slow.
*   **Use Case (Migration):** Anti-patterns often require significant refactoring *before* or *as part of* the migration to fit into a well-structured Java application.

#### d. Code Similarity/Clustering (Content-Based)

*   **Description:** Find structurally or semantically similar code objects using `clean_code`.
*   **Feasibility:**
    *   **Current Data:** `PLSQL_CodeObject.clean_code` is available.
    *   **Missing Data:** None for basic text-based similarity.
*   **Implementation Plan:**
    *   **Techniques:**
        *   **Syntactic Similarity:**
            *   Levenshtein distance or Jaccard similarity on tokenized `clean_code`.
            *   Abstract Syntax Tree (AST) diffing (very complex for PL/SQL without a full AST parser, `plsql_analyzer`'s structural parse is not a full AST).
        *   **Semantic Similarity (LLM-based):**
            *   Generate embeddings for each `clean_code` snippet using a code-aware LLM (e.g., Sentence Transformers with a code model, or OpenAI embeddings).
            *   Cluster these embeddings (e.g., K-Means, DBSCAN).
    *   **Tools:** `textdistance` library for string metrics. `scikit-learn` for clustering. LLM APIs/libraries.
*   **Pros:** Can find duplicated or near-duplicated logic, which can be consolidated into shared Java utilities.
*   **Cons:**
    *   Purely syntactic similarity can be noisy.
    *   Semantic similarity requires LLMs, adding complexity and cost.
    *   Defining "similar enough" is a thresholding problem.
*   **Use Case (Migration):** Identify redundant PL/SQL code that can be implemented once as a reusable Java component, reducing migration effort and improving maintainability of the target system.

#### e.Change Propagation Path

*   **Description:** Visualize shortest/common paths for change propagation.
*   **Feasibility:**
    *   **Current Data:** Covered by `nx.all_simple_paths` or `nx.shortest_path`.
    *   **Missing Data:** None.
*   **Implementation Plan:**
    *   UI to select a "source of change" node and a "potentially impacted" node.
    *   Backend uses `nx.all_simple_paths(graph, source, target)` or `nx.shortest_path(graph, source, target)`.
    *   Frontend highlights these paths.
*   **Pros:** Helps understand how changes in one area might ripple through the system.
*   **Cons:** If many paths exist, visualization can be cluttered.
*   **Use Case (Migration):** "If we change `UTIL_FUNC`, what are the most direct ways it could impact `CORE_BUSINESS_PROC`?" This helps in targeted testing after changes or migration of `UTIL_FUNC`.

---

This detailed analysis should give you a solid foundation for planning the implementation of these advanced graph analysis features. The key will be to iteratively build upon the existing data and add new data extraction capabilities to `plsql_analyzer` as needed (especially for node complexity and deeper anti-pattern detection).

## Me
Lets focus on `2. FastAPI Backend`

Study the current and planned implementation dependency_analyzer package.

Design a robust FastAPI backend structure keeping in mind:
- All the current, planned and future features (classes and functions) of dependency_analyzer
- The Future UI (React) designing requirements
- The data models, storage plan, etc

For each planned endpoint - Do a feasibility analysis and create a thorough implementation plan (with required lib, tools, required data models, data storage strategy, etc) and point out missing data, features, etc.
Also note the pros and cons and use of that particular feature in detail. Do required research and be thorough and detailed. Donot write any code, this is planning and brainstorming session

## Gemini
### Thinking
Here's a breakdown of the thinking process to generate the FastAPI backend design:

1.  **Understand the Core Request:** The user wants a detailed FastAPI backend design for the `dependency_analyzer` package, considering current/future features, UI needs, data models, and storage. The output should be a plan, not code, with feasibility, implementation details, pros/cons, and use cases for each endpoint.

2.  **Deconstruct "Dependency Analyzer":**
    *   **Input:** PL/SQL code objects (from `plsql_analyzer`).
    *   **Core Process:** Build a dependency graph (nodes are code objects, edges are calls).
    *   **Output/Features:**
        *   Graph storage/retrieval.
        *   Subgraph generation.
        *   Visualization data export (for frontend to render).
        *   Graph analysis (cycles, entry points, complexity, communities, paths, etc.).
        *   User annotations (notes, groups).

3.  **Consider the UI (React Frontend):**
    *   Needs graph data in a web-friendly format (node-link).
    *   Interactive: Click nodes for details, request subgraphs, trigger analyses.
    *   Needs to display PL/SQL code.
    *   Needs to save/load user-generated content (notes, groups).
    *   Needs a way to select/manage different graphs (if multiple analyses are run/saved).

4.  **Overall Backend Architecture Principles:**
    *   **RESTful API:** Standard HTTP methods, clear resource paths.
    *   **Stateless (mostly):** Each request should be self-contained if possible. Session state for UI preferences might be frontend-managed (localStorage) or light backend session if needed for complex workflows. User-generated data (notes, groups) will be persisted.
    *   **Modularity:** Separate concerns (e.g., graph operations, analysis, user data).
    *   **Scalability (Future):** While not explicitly asked for heavy scaling, think about how long-running tasks (complex analyses) might be handled (async, background tasks).
    *   **Data Validation:** Use Pydantic for request/response models.
    *   **Error Handling:** Consistent error responses.
    *   **Configuration:** Easy to configure (db paths, etc.).

5.  **Data Models (Pydantic):**
    *   `PLSQLCodeObjectResponse`: What details of a code object does the UI need? Probably most of it, but potentially strip `clean_code` from general graph responses to reduce payload, and have a separate endpoint for it.
    *   `NodeResponse`: ID, attributes (including `PLSQLCodeObjectResponse` or a summary).
    *   `EdgeResponse`: Source, target, attributes.
    *   `GraphResponse`: List of nodes, list of edges (node-link format).
    *   `SubgraphRequest`: Node ID, depths.
    *   `AnalysisRequest/Response`: Specific to each analysis type.
    *   `NoteRequest/Response`: Node/edge ID, text, user, timestamp.
    *   `GroupRequest/Response`: Group name, list of node IDs.

6.  **Storage Strategy:**
    *   **Graphs:**
        *   `GRAPHS_DIR` (from `dependency_analyzer.config`) for serialized graph files (e.g., gpickle, graphml). The API will list/load these.
        *   Consider a small metadata DB (SQLite) to store info *about* these graph files (ID, creation date, source DB, description) rather than just relying on filesystem listing. This makes management easier.
    *   **PL/SQL Analyzer Database:** The primary source for `PLSQL_CodeObject` data. The FastAPI backend will *read* from this when populating graphs or fetching code.
    *   **User-Generated Data (Notes, Groups):** A new SQLite database managed by the FastAPI backend. This keeps it separate from the `plsql_analyzer` DB and the graph files. Tables: `notes`, `user_groups`, `graph_metadata`.
    *   **Analysis Results:**
        *   Simple results (e.g., list of cycle nodes) can be returned directly.
        *   Complex results or results that need to be persisted for later viewing (e.g., community assignments) could be stored as attributes on the graph file (if resaved) or in the metadata DB. For computationally intensive ones, cache results.

7.  **Directory Structure for FastAPI App (Mental Outline):**
    *   `fastapi_app/`
        *   `main.py` (FastAPI app instance)
        *   `routers/` (separate files for graph routes, analysis routes, user_data routes)
        *   `models/` (Pydantic models)
        *   `services/` (business logic, e.g., interacting with `GraphConstructor`, `analyzer`, `GraphStorage`)
        *   `crud/` (database operations for user data)
        *   `db/` (database session management for user data DB)
        *   `config.py` (FastAPI specific config, possibly importing from `dependency_analyzer.config`)

8.  **Endpoint Design - Iterative Process (for each feature):**

    *   **Identify the Resource:** Graph, Node, Analysis, Note, Group.
    *   **Determine Actions (CRUD):**
        *   `GET /graphs`: List available graph files.
        *   `GET /graphs/{graph_name}`: Load a specific graph.
        *   `POST /graphs/{graph_name}/subgraph`: Create a subgraph.
        *   ...and so on.

    *   **For each endpoint:**
        *   **HTTP Method & Path:**
        *   **Request Body/Query Params:** What does it need? (Pydantic model).
        *   **Response Body:** What does it return? (Pydantic model).
        *   **Feasibility:**
            *   Does `dependency_analyzer` have the functions to support this?
            *   What data is needed? Is it available?
        *   **Implementation Plan:**
            *   Outline the steps the endpoint handler would take.
            *   Which `dependency_analyzer` modules/classes would it call?
            *   Which libraries (FastAPI, Pydantic, NetworkX)?
            *   Data storage interaction.
        *   **Missing Data/Features:** Identify gaps.
        *   **Pros/Cons:** Benefits vs. drawbacks.
        *   **Use Case:** How does this help the user/UI?

9.  **Detailed Endpoint Breakdown (Example thinking for one endpoint):**

    *   **Endpoint:** `GET /graphs/{graph_name}`
    *   **Resource:** A specific graph.
    *   **Action:** Retrieve/Load.
    *   **Request:** Path param `graph_name`. Query params: `structure_only=bool` (default False), `populate_objects=bool` (default True, only relevant if structure_only was saved).
    *   **Response:** `GraphResponse` (nodes, edges).
    *   **Feasibility:**
        *   `GraphStorage.load_graph()` exists.
        *   `GraphStorage.load_and_populate()` exists.
        *   `PLSQL_CodeObject` data available from `plsql_analyzer` DB via `DatabaseLoader`.
    *   **Implementation Plan:**
        1.  Receive `graph_name`. Construct path from `GRAPHS_DIR`.
        2.  If `structure_only=true` in query, load structure.
        3.  Else, if `populate_objects=true` (and graph file likely structure-only), use `GraphStorage.load_and_populate()`. Needs `DatabaseLoader` instance, which needs `DatabaseManager` from `plsql_analyzer`.
        4.  Else, use `GraphStorage.load_graph()` (full graph).
        5.  Convert NetworkX graph to node-link JSON (Pydantic model). `nx.node_link_data()`.
        6.  Return JSON.
    *   **Missing Data:** Perhaps a way to know *if* a saved graph file *is* structure-only without trying to load it fully. (Could be in filename convention or metadata DB).
    *   **Pros:** Central way to get graph data for UI.
    *   **Cons:** Large graphs can mean large JSON payloads. (Future: pagination for nodes/edges, or streaming).
    *   **Use Case:** UI needs this to display a graph.

10. **Refine and Organize:**
    *   Group endpoints logically (e.g., by resource).
    *   Ensure consistency in naming and style.
    *   Add sections for overall design considerations (auth, error handling, async).
    *   Review against the original requirements. Ensure all current/planned `dependency_analyzer` features are exposed if relevant. Ensure UI needs are met.

11. **Self-Correction/Improvements during the process:**
    *   Initially, I might think of just listing files in `GRAPHS_DIR`. Then realize a metadata DB for graphs is better for richer info (description, source, etc.).
    *   Consider if `PLSQL_CodeObject.clean_code` should always be sent. Probably not for large graphs. So, add a separate endpoint for fetching code for a *specific* node.
    *   Think about how `DatabaseLoader` and `DatabaseManager` from `plsql_analyzer` would be instantiated and used by the FastAPI app. They might need to be initialized globally or per request (with dependency injection).
    *   Realize that some analyses can be slow, so flag them for potential async processing.
    *   Separate user-generated data (notes, groups) into its own DB to avoid polluting graph files or the `plsql_analyzer` DB.

By following this structured thinking, we can cover all the bases and produce a comprehensive design document like the example you're looking for.

### Output
Okay, let's architect a robust FastAPI backend for the `dependency_analyzer`, keeping the current capabilities, planned features, and future UI needs in mind.

#### FastAPI Backend Design for `dependency_analyzer`

**Guiding Principles:**

1.  **Statelessness (where possible):** API calls should be self-contained. State related to user sessions or specific views will largely be managed by the React frontend, with the backend persisting user-generated data.
2.  **Modularity:** Organize routers and services logically.
3.  **Clear Contracts:** Use Pydantic for request and response validation and serialization.
4.  **Asynchronous Operations:** Leverage FastAPI's async capabilities, especially for potentially long-running graph analysis tasks.
5.  **Configuration:** Centralized configuration for paths and database connections.
6.  **Separation of Concerns:** The FastAPI layer orchestrates calls to the `dependency_analyzer` core logic.

---

##### Overall Backend Structure (Conceptual)

```
fastapi_app/
├── main.py                 # FastAPI app initialization, middleware
├── routers/                # API endpoint definitions
│   ├── graphs.py           # Endpoints for graph listing, loading, subgraph creation
│   ├── analysis.py         # Endpoints for triggering graph analyses
│   ├── nodes.py            # Endpoints for node-specific data (e.g., code)
│   └── user_data.py      # Endpoints for notes, user-defined groups
├── services/               # Business logic layer
│   ├── graph_service.py    # Interacts with GraphStorage, GraphConstructor
│   ├── analysis_service.py # Interacts with analyzer.py
│   └── user_data_service.py # Manages notes and groups
├── models/                 # Pydantic models for request/response
│   ├── graph_models.py
│   ├── analysis_models.py
│   ├── node_models.py
│   └── user_data_models.py
├── crud/                   # Database Create, Read, Update, Delete operations (for user_data)
│   └── user_data_crud.py
├── db/                     # Database session management (for user_data_db)
│   └── session.py
├── core/                   # Shared utilities, configuration access for FastAPI
│   └── config.py           # FastAPI specific config, potentially loads from dependency_analyzer.config
└── utils/
    └── response_utils.py   # Helper for consistent API responses
```

---

##### Data Models (Pydantic - in `fastapi_app/models/`)

*   **`PLSQLCodeObjectMinimalResponse`**: A summarized version for graph display.
    *   `id: str`
    *   `name: str`
    *   `package_name: Optional[str]`
    *   `type: str` (enum value)
    *   `overloaded: bool`
    *   `loc: Optional[int]` (Lines of Code, if calculated)
    *   `complexity_score: Optional[float]` (if calculated)
*   **`PLSQLCodeObjectFullResponse(PLSQLCodeObjectMinimalResponse)`**: Complete details for node info panel.
    *   `parsed_parameters: List[Dict]`
    *   `parsed_return_type: Optional[str]`
    *   `extracted_calls_summary: List[Dict]` (e.g., just call names and target types)
    *   `start_line: Optional[int]`
    *   `end_line: Optional[int]`
    *   `has_source_code: bool` (indicate if `clean_code` is available via another endpoint)
*   **`NodeResponse`**:
    *   `id: str` (node ID in the graph)
    *   `attributes: PLSQLCodeObjectMinimalResponse` (or just a dict of its fields)
    *   `group_id: Optional[str]` (community/package/user group)
    *   `node_role: Optional[str]` (e.g., 'entry_point', 'hub', 'terminal')
*   **`EdgeResponse`**:
    *   `source: str`
    *   `target: str`
    *   `attributes: Optional[Dict]` (e.g., call count, type of call if available)
*   **`GraphResponse`**: (Node-link format)
    *   `graph_id: str`
    *   `description: Optional[str]`
    *   `nodes: List[NodeResponse]`
    *   `edges: List[EdgeResponse]`
    *   `metadata: Optional[Dict]` (e.g., creation_date, source_db)
*   **`GraphInfo`**: For listing available graphs.
    *   `id: str` (e.g., filename without extension)
    *   `path: str`
    *   `size_kb: Optional[float]`
    *   `node_count: Optional[int]` (from metadata or quick parse)
    *   `edge_count: Optional[int]`
    *   `created_at: Optional[datetime]` (from file system or metadata)
    *   `description: Optional[str]` (from metadata)
*   **`SubgraphRequest`**:
    *   `node_id: str`
    *   `upstream_depth: int = 0`
    *   `downstream_depth: Optional[int] = None`
    *   `load_with_objects: bool = True` (default to true for UI utility)
*   **`NodeCodeResponse`**:
    *   `node_id: str`
    *   `clean_code: Optional[str]`
    *   `literal_map: Optional[Dict[str, str]]`
*   **`NoteRequest`**:
    *   `target_type: str` ('node', 'edge', 'group', 'graph')
    *   `target_id: str`
    *   `text: str`
    *   `author: Optional[str]`
*   **`NoteResponse(NoteRequest)`**:
    *   `note_id: str`
    *   `created_at: datetime`
    *   `updated_at: datetime`
*   **`GroupRequest`**:
    *   `name: str`
    *   `node_ids: List[str]`
    *   `description: Optional[str]`
*   **`GroupResponse(GroupRequest)`**:
    *   `group_id: str`
    *   `graph_id: str`
*   **Analysis specific request/response models** (e.g., `CycleAnalysisResponse`, `CommunityAnalysisResponse`).

---

##### Data Storage Strategy

1.  **Dependency Analyzer Output (`plsql_analyzer` DB):**
    *   The FastAPI backend will **read** from the SQLite database generated by `plsql_analyzer` (via `dependency_analyzer.config.DATABASE_PATH`).
    *   This DB contains the canonical `PLSQL_CodeObject` data.
    *   The FastAPI backend will use `DatabaseLoader` (from `dependency_analyzer`) to fetch these objects when needed (e.g., for `load_and_populate` or fetching source code).

2.  **Serialized Graphs:**
    *   Full dependency graphs and subgraphs generated by `dependency_analyzer.cli` or through API calls will be stored as files in `dependency_analyzer.config.GRAPHS_DIR` (e.g., `.gpickle` or `.graphml`).
    *   The API will list these files and load them using `dependency_analyzer.persistence.GraphStorage`.

3.  **FastAPI Application Database (New SQLite DB):**
    *   A *new, separate* SQLite database will be managed by the FastAPI application itself.
    *   **Purpose:** Store metadata about graphs, user-generated notes, and user-defined groups.
    *   **Tables:**
        *   `graph_metadata`:
            *   `graph_id: TEXT PRIMARY KEY` (e.g., filename without extension of the graph file)
            *   `file_path: TEXT UNIQUE NOT NULL` (path to the graph file in `GRAPHS_DIR`)
            *   `description: TEXT`
            *   `source_plsql_db_path: TEXT` (path to the `plsql_analyzer` DB used to build this graph)
            *   `created_at: DATETIME`
            *   `node_count: INTEGER`
            *   `edge_count: INTEGER`
            *   `tags: TEXT` (JSON list of tags)
        *   `notes`:
            *   `note_id: TEXT PRIMARY KEY` (UUID)
            *   `graph_id: TEXT` (references `graph_metadata.graph_id`)
            *   `target_type: TEXT NOT NULL` ('node', 'edge', 'group', 'graph_itself')
            *   `target_id: TEXT NOT NULL` (node_id, edge_tuple_str, group_id, or graph_id)
            *   `text: TEXT NOT NULL`
            *   `author: TEXT`
            *   `created_at: DATETIME`
            *   `updated_at: DATETIME`
        *   `user_groups`:
            *   `group_id: TEXT PRIMARY KEY` (UUID)
            *   `graph_id: TEXT NOT NULL` (references `graph_metadata.graph_id`)
            *   `name: TEXT NOT NULL`
            *   `description: TEXT`
            *   `node_ids: TEXT NOT NULL` (JSON list of node IDs)
            *   `created_at: DATETIME`
            *   `updated_at: DATETIME`
    *   **ORM/Query Builder:** SQLAlchemy Core (for schema definition and complex queries) or a simple CRUD layer with direct SQL. Given the relatively simple structure, direct SQL with Pydantic for validation might be sufficient initially.

---

##### Planned Endpoints (`fastapi_app/routers/`)

###### 1. Graph Management (`graphs.py`)

*   **`GET /graphs`**
    *   **Description:** List all available processed dependency graphs.
    *   **Response:** `List[GraphInfo]`
    *   **Feasibility:** High.
    *   **Implementation Plan:**
        1.  Read from the `graph_metadata` table in the FastAPI app DB.
        2.  Fallback: If metadata table is empty or not fully populated, could scan `GRAPHS_DIR` and attempt to extract minimal info (filename as ID, file size, modified time). A background task could populate/update metadata.
    *   **Missing Data:** A robust way to initially populate `graph_metadata` if graphs are generated outside the API (e.g., by CLI). A "scan and register graphs" endpoint or CLI command for the FastAPI app might be needed.
    *   **Pros:** Central place to discover usable graphs.
    *   **Cons:** Filesystem scan can be slow if metadata DB isn't used or up-to-date.
    *   **Use Case:** UI dropdown to select a graph to load and analyze.

*   **`POST /graphs/register`** (Optional utility)
    *   **Description:** Manually register an existing graph file from `GRAPHS_DIR` into the `graph_metadata` table or trigger a scan.
    *   **Request:** `path_to_graph_file: str` or `scan_directory: bool`
    *   **Response:** `GraphInfo` or `List[GraphInfo]`
    *   **Feasibility:** Medium (needs careful file system interaction and error handling).
    *   **Implementation Plan:** Parse graph file for node/edge counts, prompt for description.
    *   **Pros:** Helps bootstrap the metadata.
    *   **Cons:** Potential security risk if paths are arbitrary; restrict to `GRAPHS_DIR`.

*   **`GET /graphs/{graph_id}`**
    *   **Description:** Retrieve a specific graph's data (nodes and edges).
    *   **Path Param:** `graph_id: str`
    *   **Query Params:**
        *   `details: str = "minimal"` ('minimal', 'full' for `PLSQLCodeObject` in nodes)
        *   `format: str = "node_link"` (e.g. node_link for UI)
    *   **Response:** `GraphResponse`
    *   **Feasibility:** High.
    *   **Implementation Plan:**
        1.  Lookup `graph_id` in `graph_metadata` to get `file_path`.
        2.  Use `GraphStorage.load_graph(file_path)`. If the graph was saved as structure-only and `details="full"` is requested, use `GraphStorage.load_and_populate()`, which needs a `DatabaseLoader` initialized with the `source_plsql_db_path` from metadata.
        3.  Iterate through graph nodes/edges, create `NodeResponse` / `EdgeResponse` list using appropriate `PLSQLCodeObject...Response` model.
        4.  Return `GraphResponse`.
    *   **Missing Data:** Clear indication in `graph_metadata` if a graph file is "structure-only" or "full".
    *   **Pros:** Primary way for UI to fetch graph data.
    *   **Cons:** Large graphs can lead to large JSON responses. Consider pagination for nodes/edges in the future if performance becomes an issue.
    *   **Use Case:** UI displays the selected graph.

*   **`POST /graphs/{source_graph_id}/subgraph`**
    *   **Description:** Create and return a subgraph from a larger source graph.
    *   **Path Param:** `source_graph_id: str`
    *   **Request Body:** `SubgraphRequest`
    *   **Response:** `GraphResponse` (for the new subgraph)
    *   **Feasibility:** High.
    *   **Implementation Plan:**
        1.  Load the `source_graph_id` (potentially with `load_and_populate` if needed, based on request or source graph type).
        2.  Call `dependency_analyzer.analysis.analyzer.generate_subgraph_for_node()` with parameters from `SubgraphRequest`.
        3.  Convert the resulting NetworkX subgraph to `GraphResponse`.
        4.  *Optional:* Save the generated subgraph to `GRAPHS_DIR` and register it in `graph_metadata`. If saved, return its new `graph_id`.
    *   **Missing Data:** Strategy for naming/managing these dynamically generated subgraphs if they are persisted.
    *   **Pros:** Allows focused exploration by the UI.
    *   **Cons:** Computation can be intensive for deep/wide subgraphs from a very large source graph.
    *   **Use Case:** UI user right-clicks a node and requests to see its local dependencies.

###### 2. Graph Analysis (`analysis.py`)

*   **General Pattern:** `GET /graphs/{graph_id}/analysis/{analysis_type}`
    *   **Path Params:** `graph_id: str`, `analysis_type: str` (e.g., "cycles", "entry_points", "communities", "node_metrics")
    *   **Query Params:** Specific to each analysis (e.g., for communities: `algorithm: str = "louvain"`, `resolution: float = 1.0`).
    *   **Response:** Analysis-specific Pydantic model (e.g., `CycleAnalysisResponse`, `NodeMetricsResponse`).

*   **Specific Analysis Endpoints:**

    *   **`GET /graphs/{graph_id}/analysis/cycles`**
        *   **Response:** `List[List[str]]` (list of node ID lists, each representing a cycle).
        *   **Feasibility:** High (`find_circular_dependencies`).
        *   **Implementation:** Load graph, call `analyzer.find_circular_dependencies()`.
    *   **`GET /graphs/{graph_id}/analysis/entry_points`**
        *   **Response:** `List[str]` (list of node IDs).
        *   **Feasibility:** High (`find_entry_points`).
    *   **`GET /graphs/{graph_id}/analysis/terminal_nodes`**
        *   **Query Param:** `exclude_placeholders: bool = True`
        *   **Response:** `List[str]`
        *   **Feasibility:** High (`find_terminal_nodes`).
    *   **`GET /graphs/{graph_id}/analysis/node_degrees/{node_id}`**
        *   **Response:** `Dict[str, int]` (e.g., `{"in_degree": x, "out_degree": y, "total_degree": z}`)
        *   **Feasibility:** High (`get_node_degrees`).
    *   **`GET /graphs/{graph_id}/analysis/paths`**
        *   **Query Params:** `source_node: str`, `target_node: str`, `cutoff: Optional[int] = None`
        *   **Response:** `List[List[str]]`
        *   **Feasibility:** High (`find_all_paths`).
    *   **`GET /graphs/{graph_id}/analysis/connected_components`**
        *   **Query Param:** `strongly_connected: bool = True`
        *   **Response:** `List[List[str]]` (list of sets of node IDs)
        *   **Feasibility:** High (`get_connected_components`).
    *   **`GET /graphs/{graph_id}/analysis/communities`**
        *   **Query Params:** `algorithm: str = "louvain"`, `resolution: Optional[float] = 1.0`, `weight: Optional[str] = None`
        *   **Response:** `List[List[str]]` (communities) or `Dict[str, int]` (node_id to community_id mapping).
        *   **Feasibility:** Medium (depends on NetworkX community algorithms).
        *   **Implementation:** Load graph, call appropriate `nx.community` function.
        *   **Pros:** Identifies modules.
        *   **Cons:** Can be slow for large graphs (e.g., Girvan-Newman). Parameter tuning might be needed.
    *   **`GET /graphs/{graph_id}/analysis/node_metrics`**
        *   **Query Param:** `metrics: List[str]` (e.g., `["degree_centrality", "betweenness", "pagerank", "loc", "complexity_score_approx"]`)
        *   **Response:** `Dict[str, Dict[str, float]]` (node_id -> metric_name -> value).
        *   **Feasibility:** Medium to High (centrality is built-in, LOC easy, complexity_score_approx needs a defined heuristic from `PLSQLCodeObject.clean_code`).
        *   **Implementation:** Load graph. For each requested metric, compute and collect.
        *   **Missing Data:** Defined heuristic for `complexity_score_approx`.
    *   **`GET /graphs/{graph_id}/analysis/reachability/{node_id}`**
        *   **Query Params:** `direction: str = "downstream"` ('downstream', 'upstream'), `depth_limit: Optional[int] = None`.
        *   **Response:** `List[str]` (set of reachable node IDs).
        *   **Feasibility:** High (`nx.descendants`, `nx.ancestors`, `nx.bfs_tree`).
    *   **`POST /graphs/{graph_id}/analysis/impact`** (POST because it might involve more params or be seen as an action)
        *   **Request Body:** `node_id: str`, `change_type: str = "modify"` ('modify', 'remove')
        *   **Response:** `Dict[str, List[str]]` (e.g. `{"downstream_impact": [...], "upstream_impact": [...]}`)
        *   **Feasibility:** High.
        *   **Implementation:** Uses reachability.

*   **Pros (General for Analysis Endpoints):** Moves computation to the backend, allows UI to be lighter. Centralizes analysis logic.
*   **Cons (General):** Some analyses can be slow; consider async tasks and caching for results if they are expensive and don't change often for a given graph.
*   **Use Case:** Powers all the advanced analysis features in the UI.

###### 3. Node-Specific Data (`nodes.py`)

*   **`GET /graphs/{graph_id}/nodes/{node_id}/code`**
    *   **Description:** Fetch the `clean_code` and `literal_map` for a specific PL/SQL object.
    *   **Response:** `NodeCodeResponse`
    *   **Feasibility:** High.
    *   **Implementation Plan:**
        1.  Load the graph (potentially just the node if `GraphStorage` supports partial load, or load the whole graph's objects). Better: Directly query the `plsql_analyzer` DB for the specific object's `clean_code` and `literal_map` using its ID if the `PLSQLCodeObject` in the graph doesn't store it.
        2.  If `PLSQLCodeObject` in the graph *does* contain `clean_code`, extract it.
        3.  If not, and `source_plsql_db_path` is known for the graph:
            *   Use `DatabaseManager(source_plsql_db_path).get_codeobject_by_id(node_id)` (needs new method in `DatabaseManager`).
            *   Extract `clean_code` and `literal_map`.
    *   **Missing Data/Features:** A `get_codeobject_by_id(object_id)` method in `plsql_analyzer.persistence.DatabaseManager`.
    *   **Pros:** Provides source code for UI display without bloating the main graph response.
    *   **Cons:** Requires efficient way to fetch code for a single object.
    *   **Use Case:** UI displays source code when a node is clicked.

*   **`GET /graphs/{graph_id}/nodes/{node_id}/details`**
    *   **Description:** Fetch full details for a specific node.
    *   **Response:** `PLSQLCodeObjectFullResponse` (or a model containing it).
    *   **Feasibility:** High.
    *   **Implementation Plan:** Similar to `/code`, fetch the object data (either from the loaded graph or `plsql_analyzer` DB) and serialize using `PLSQLCodeObjectFullResponse`.
    *   **Pros:** Provides all necessary details for the node information panel in the UI.
    *   **Use Case:** Populating the detailed information view for a selected node.

###### 4. User-Generated Data (`user_data.py`)

*   **`POST /graphs/{graph_id}/notes`**
    *   **Request Body:** `NoteRequest`
    *   **Response:** `NoteResponse` (with generated `note_id`, `created_at`, `updated_at`)
    *   **Feasibility:** High.
    *   **Implementation Plan:**
        1.  Validate request.
        2.  Store note in the FastAPI app's SQLite DB (`notes` table) using CRUD operations.
    *   **Pros:** Allows users to annotate graph elements.
    *   **Cons:** Requires DB setup for the FastAPI app.
    *   **Use Case:** Developer adds migration-specific comments to a procedure node.

*   **`GET /graphs/{graph_id}/notes`**
    *   **Query Params:** `target_type: Optional[str]`, `target_id: Optional[str]`
    *   **Response:** `List[NoteResponse]`
    *   **Feasibility:** High.
    *   **Implementation Plan:** Query the `notes` table, filtering by `graph_id` and optionally by `target_type` and `target_id`.
    *   **Pros:** UI can display relevant notes.

*   **`PUT /graphs/{graph_id}/notes/{note_id}`**
    *   **Request Body:** `NoteRequest` (only `text` and `author` would typically be updatable)
    *   **Response:** `NoteResponse`
    *   **Feasibility:** High.
    *   **Implementation Plan:** Update note in DB.

*   **`DELETE /graphs/{graph_id}/notes/{note_id}`**
    *   **Response:** HTTP 204 No Content.
    *   **Feasibility:** High.
    *   **Implementation Plan:** Delete note from DB.

*   **`POST /graphs/{graph_id}/groups`**
    *   **Request Body:** `GroupRequest`
    *   **Response:** `GroupResponse` (with generated `group_id`)
    *   **Feasibility:** High.
    *   **Implementation Plan:** Store group in `user_groups` table.
    *   **Pros:** Enables powerful user-driven organization.
    *   **Cons:** Managing consistency if nodes are removed from the underlying graph can be tricky (soft delete or cleanup job).
    *   **Use Case:** User groups related PL/SQL objects into a "Billing Module" for focused analysis or migration planning.

*   **`GET /graphs/{graph_id}/groups`**
    *   **Response:** `List[GroupResponse]`
    *   **Feasibility:** High.
    *   **Implementation Plan:** Query `user_groups` table by `graph_id`.

*   **`GET /graphs/{graph_id}/groups/{group_id}`**
    *   **Response:** `GroupResponse`
    *   **Feasibility:** High.

*   **`PUT /graphs/{graph_id}/groups/{group_id}`**
    *   **Request Body:** `GroupRequest`
    *   **Response:** `GroupResponse`
    *   **Feasibility:** High.

*   **`DELETE /graphs/{graph_id}/groups/{group_id}`**
    *   **Response:** HTTP 204 No Content.
    *   **Feasibility:** High.

---

**Initialization and Shared Components:**

*   The FastAPI `main.py` will initialize:
    *   An instance of `DatabaseManager` (from `plsql_analyzer`) for accessing the PL/SQL object data. This might need to be configurable if multiple PL/SQL analysis DBs exist.
    *   An instance of `DatabaseLoader` using the above `DatabaseManager`.
    *   An instance of `GraphStorage`.
    *   These instances can be made available to router functions via FastAPI's dependency injection system.
*   The FastAPI app DB (for notes/groups/metadata) will be set up (e.g., using SQLAlchemy models and Alembic for migrations, or simpler direct DDL execution on startup).

**Async Considerations:**

*   For endpoints like `/analysis/{analysis_type}` where computation might be lengthy (e.g., complex community detection, betweenness centrality on huge graphs):
    *   Define the endpoint handler as `async def`.
    *   Use `await asyncio.to_thread(blocking_analysis_function, args)` to run blocking NetworkX/analyzer functions in a separate thread pool, preventing the main event loop from blocking.
    *   For very long tasks (>30-60 seconds), consider implementing a task queue system (e.g., Celery with Redis/RabbitMQ) where the API endpoint submits a job and the UI polls for results or uses WebSockets. This is likely overkill for V1 unless graphs are truly massive and analyses are very slow.

This detailed plan should cover the major aspects of the FastAPI backend. The key is to leverage the existing `dependency_analyzer` logic effectively and build a clean API layer on top, with a dedicated persistence mechanism for user-specific data.

## Me
Create a detailed roadmap document (properly structured, very detailed) for all of the above discussed features.
Arrange the roadmap in feature-releases to be implemented first according to a ranking scheme (Plan what should be implemented when - consider which would work best here).

Each feature should be noted down in a detailed fashion, think of robust structure for it.

But is should include:
- Changed/Updated Repo structure (filenames and locations)
- Simple summary followed by detailed description talking about the needs, requirements and other details.
- Detailed implementation plan (which all files / objects should be updated/created - What to use and how to implement it in most optimized fashion)
- Tools and other python libraries, and other code snippents (from elsewhere in CodeMorph) required.
- Other info according to your planned structure.

Do not write any code - This is a brainstorming and planning stage!

## Gemini

### Thinking
No THINKING

### Output
Okay, let's craft a detailed roadmap for the `dependency_analyzer` enhancements, focusing on feature releases prioritized for maximum impact and logical progression.

#### CodeMorph: `dependency_analyzer` Enhancement Roadmap

**Project Goal:** To transform `dependency_analyzer` into a powerful tool supporting semi-automated code migration from PL/SQL to Java SpringBoot, featuring advanced graph analysis, a FastAPI backend, and a rich React frontend.

**Prioritization Strategy:**

The roadmap is structured in releases, prioritizing features based on:

1.  **Core Value:** Features directly aiding migration understanding and planning.
2.  **Foundation First:** Backend capabilities before complex UI features that depend on them.
3.  **Iterative Complexity:** Start with essential analysis and gradually add more advanced features.
4.  **User Feedback Loop (Implied):** Ideally, after each major release, feedback would inform subsequent priorities.

---

##### Release 1.0: Core Analysis & API Foundation

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

###### Feature 1.1: FastAPI App Setup & Graph Metadata Persistence

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

###### Feature 1.2: API Endpoints for Graph Listing and Loading

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

###### Feature 1.3: API Endpoint for Subgraph Generation

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

###### Feature 1.4: Basic Server-Side Graph Analysis API Endpoints

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

###### Feature 1.5: API Endpoint for Node Source Code

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

##### Release 1.5: Basic UI Integration & Advanced Node Metrics

**Theme:** Develop a basic React UI that can consume the Release 1.0 APIs for graph display and interaction. Enhance backend with more detailed node metrics.

(UI development is out of scope for this detailed `dependency_analyzer` backend plan, but its needs inform the API).

###### Feature 1.5.1: Advanced Node Metrics Calculation & API

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

##### Release 2.0: User Interactivity & Deeper Analysis

**Theme:** Enable user-driven organization (notes, groups) and more sophisticated graph analysis like community detection and automated node classification.

###### Feature 2.1: User Notes and Grouping API & Persistence

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

###### Feature 2.2: Community Detection & Node Role Classification API

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

##### Future Releases (Beyond 2.0 - High-Level Ideas)

*   **Release 3.0: Advanced Path Analysis & Migration Unit Support**
    *   Critical Path Identification (with user-definable weights).
    *   Identifying Cohesive Subgraphs for Migration (UI assists this).
    *   Minimizing Inter-Unit Dependencies (metrics for proposed partitions).
    *   Strangler Fig Pattern Candidate Identification.
*   **Release 3.5: Deeper Code Insights & Anti-Patterns**
    *   Code Similarity/Clustering (requires significant backend work, possibly LLMs).
    *   Anti-Pattern Detection (needs more data from `plsql_analyzer` or complex heuristics).
*   **Release 4.0: Full UI Polish & Advanced Features**
    *   Side-by-side views, rich export options, undo/redo, theming.
    *   Potentially collaborative features (real-time updates for notes/groups if multiple users - adds significant complexity with WebSockets).

This roadmap provides a structured approach. Each feature within a release can be broken down further into smaller tasks. The key is to build a solid API foundation first, then iteratively add analytical power and enable richer UI interactions.

## Me
For releases beyond 2.0, we also need a detailed roadmap just like others:

Make use of the future planned part of `dependency_analyzer` Advance Graph Analysis Roadmap

### Tier 3: Migration Strategy & Planning Aids

*(Features in this tier often leverage outputs from Tier 1 & 2)*

##### 3.1 Feature: Impact Analysis ("What if?")

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

##### 3.2 Feature: Critical Path Identification

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

##### 3.3 Feature: Strangler Fig Pattern Support (Candidate Identification)

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

##### 3.4 Feature: User-Defined Grouping (Backend)

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

### Tier 4: Advanced/Future Enhancements

*(These features are generally more complex or build heavily on previous tiers)*

#### 4.1 Feature: Minimizing Inter-Unit Dependencies (Analysis)

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

#### 4.2 Feature: Change Propagation Path Visualization

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

#### 4.3 Feature: Anti-Pattern Detection

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

#### 4.4 Feature: Code Similarity/Clustering (Content-Based)

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

## Model
### Thinking
No THINKING

### Output
Okay, this is a comprehensive set of features! Let's structure the roadmap for releases beyond 2.0, keeping the same detailed format.

#### CodeMorph: `dependency_analyzer` Enhancement Roadmap (Continued)

---

##### Release 3.0: Advanced Migration Strategy & Planning Aids

**Theme:** Provide sophisticated tools to directly support migration planning, including detailed impact analysis, identification of critical code paths, and support for common migration patterns like Strangler Fig. This release heavily leverages the foundational analysis and user interaction capabilities built in previous releases.

**Target Repo Structure Changes:**

*   Minor additions within `fastapi_app/routers/analysis.py` and `fastapi_app/services/analysis_service.py`.
*   Enhancements primarily within `dependency_analyzer/analysis/analyzer.py`.
*   New database tables within the FastAPI app's DB for storing user-defined group metadata if not already fully implemented in 2.x.

---

###### Feature 3.1: Impact Analysis ("What if?") Integration

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

###### Feature 3.2: Critical Path Identification (Weighted Paths)

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

###### Feature 3.3: Strangler Fig Pattern Support (Candidate Identification)

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

###### Feature 3.4: User-Defined Grouping Enhancement (Backend Persistence & API Finalization)

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

##### Release 4.0: Advanced & Future Enhancements

**Theme:** Introduce more sophisticated analytical capabilities, including deeper code analysis (anti-patterns, similarity) and optimizing migration unit boundaries. These features often require more complex algorithms or data from `plsql_analyzer`.

---

###### Feature 4.1: Minimizing Inter-Unit Dependencies (Analysis & Heuristics)

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

###### Feature 4.2: Change Propagation Path Visualization (API Enhancement)

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

###### Feature 4.3: Anti-Pattern Detection (Initial Rules)

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

###### Feature 4.4: Code Similarity/Clustering (Basic Syntactic)

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