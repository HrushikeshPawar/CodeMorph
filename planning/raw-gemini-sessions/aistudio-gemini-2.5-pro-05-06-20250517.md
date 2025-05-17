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

# Me
Create a detailed roadmap document (properly structured markdown file) for all of the above discussed features.
Arrange the roadmap in terms of which features to be implemented first according to ranking scheme (consider which would work best here).

Each feature should be noted down in a detailed fashion, think of robust structure for it.

But is should include:
- Changed/Updated Repo structure (filenames and locations)
- Simple summary followed by detailed description talking about the needs, requirements and other details.
- Detailed implementation plan (which all files / objects should be updated/created - What to use and how to implement it in most optimized fashion)
- Other info according to your planned structure.

## Gemini
### Thinking
The user wants a detailed roadmap document in Markdown.
The roadmap should cover all the "Advanced Graph Analysis" features discussed.
It needs a ranking scheme to prioritize features.
For each feature, I need to provide:
    -   **Impact on Repo Structure:** (New files, modified files in `dependency_analyzer`)
    -   **Summary:** Brief overview.
    -   **Detailed Description:** Needs, requirements, benefits.
    -   **Implementation Plan:** Specific files/objects, libraries, algorithms, optimization considerations.
    -   **Data Requirements:** Current data sufficiency, missing data, how to obtain missing data.
    -   **Pros & Cons:**
    -   **Migration Use Case:** How it aids PL/SQL to Java migration.

**Ranking Scheme Considerations:**

1.  **Foundation First:** Features that provide data or capabilities needed by other features.
2.  **High Impact for Migration:** Features that directly provide significant insights for planning or executing the migration.
3.  **Feasibility/Effort:** Features that can be implemented with current data or minimal additions vs. those requiring significant new data extraction.
4.  **User Value:** How immediately useful is this feature to the end-user (developer/architect performing the migration).

**Proposed Ranking Order (Initial thought, will refine):**

1.  **Node Complexity Metrics:** Foundational for many other features (Critical Path, Utility Node classification, Cycle Ranking). Relatively straightforward to implement with current data.
2.  **Reachability Analysis:** Core graph function, essential for impact analysis. Already feasible.
3.  **Execution Path Tracing:** Builds on reachability, very useful for understanding scope. Feasible.
4.  **Package-Based Grouping (Analytical Part):** Leverages existing package data, gives good high-level view. Visual part is frontend.
5.  **Hubs/Connectors, Utility Nodes, Orphaned Components Classification:** Builds on basic graph metrics and complexity.
6.  **Critical Path Identification:** Depends on Node Complexity and/or manual weighting.
7.  **Community Detection:** Powerful but might need tuning.
8.  **Impact Analysis ("What if?"):** UI-driven application of reachability.
9.  **Circular Dependency Analysis (Advanced - Ranking, Break Points):** Builds on detection, ranking needs complexity. Break points are hard.
10. **User-Defined Grouping (Backend):** Involves new storage, but high user value.
11. **Strangler Fig Pattern Support:** Application of other metrics (in-degree, cross-package calls).
12. **Change Propagation Path:** Application of pathfinding.
13. **Anti-Pattern Detection:** Some are feasible, some (like global state) need `plsql_analyzer` changes.
14. **Code Similarity/Clustering:** Most complex, potentially involves LLMs or significant `plsql_analyzer` work.

Let's refine this. Node Complexity Metrics are indeed foundational. Basic path/reachability is core. Classification is also relatively easy and high value.

**Refined Priority Tiers:**

*   **Tier 1 (Foundational & High Immediate Value):**
    1.  Node Complexity Metrics (LOC, NumParams, NumCallsMade, Approx. Cyclomatic)
    2.  Reachability Analysis (Ancestors/Descendants)
    3.  Execution Path Tracing (Simple paths, DFS/BFS based)
    4.  Automated Node Classification (Entry, Terminal - already have; Hubs, Connectors, Utilities, Orphans - add these)

*   **Tier 2 (Structural Insights & Grouping):**
    5.  Package-Based Grouping (Analytical part - inter/intra package calls, cohesion/coupling metrics)
    6.  Community Detection (e.g., Louvain)
    7.  Circular Dependency Analysis (Advanced: Ranking by size/complexity, visualization support)

*   **Tier 3 (Migration Strategy & Planning Aids):**
    8.  Impact Analysis ("What if?") (Leveraging Reachability)
    9.  Critical Path Identification (Using node complexity weights)
    10. Strangler Fig Pattern Support (Identification of candidates)
    11. User-Defined Grouping (Backend storage & API - frontend separate)

*   **Tier 4 (Advanced/Future Enhancements):**
    12. Minimizing Inter-Unit Dependencies (Post-grouping analysis)
    13. Change Propagation Path (Specific path visualization)
    14. Anti-Pattern Detection (More sophisticated rules, potential `plsql_analyzer` enhancements)
    15. Code Similarity/Clustering (Requires significant effort or external tools/LLMs)

This tiered approach seems more logical. I will structure the document based on these tiers. For each feature, I will detail the points requested by the user.

The repo structure changes will mostly be within `packages/dependency_analyzer/src/dependency_analyzer/analysis/`. New files might be added for specific complex analyses or if a module grows too large. The `analyzer.py` might be split.

I'll make sure the implementation plan is specific enough (e.g., "modify `analyzer.py` to add function `calculate_node_complexity(graph) -> None` which iterates nodes, computes metrics, and adds them as attributes").

### Output
Okay, here's a detailed roadmap document for the "Advanced Graph Analysis" features for your `dependency_analyzer` package.

```markdown
# CodeMorph: `dependency_analyzer` - Advanced Graph Analysis Roadmap

## Document Version: 1.0
## Date: 2025-05-16

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
```