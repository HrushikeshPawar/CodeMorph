from __future__ import annotations
import networkx as nx
import loguru as lg
from tqdm.auto import tqdm
from typing import List, Dict, Set, Tuple, Any, Optional

# Assuming plsql_analyzer is a package accessible in the Python path.
# Based on your file structure:
# packages/plsql_analyzer/src/plsql_analyzer/core/code_object.py
from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType
from plsql_analyzer.parsing.call_extractor import CallDetailsTuple
from dependency_analyzer.builder.overload_resolver import resolve_overloaded_call

class GraphConstructor:
    """
    Constructs a dependency graph from a list of PLSQL_CodeObject instances.

    The class handles normal and overloaded procedure/function calls, builds
    a graph representing dependencies, and identifies out-of-scope calls.
    """

    def __init__(
            self,
            code_objects: List[PLSQL_CodeObject],
            logger: lg.Logger,
            verbose: bool = False
        ):
        """
        Initializes the GraphConstructor.

        Args:
            code_objects: A list of PLSQL_CodeObject instances to build the graph from.
            logger: A Loguru logger instance for logging messages.
            verbose: If True, enables more detailed console output via the logger
                     (though logger levels should primarily control this).
        """
        self.code_objects: List[PLSQL_CodeObject] = code_objects
        self.logger: lg.Logger = logger.bind(class_name=self.__class__.__name__) # Bind class context to logger
        self.verbose: bool = verbose # Verbose flag can be used for conditional tqdm or specific debug logs

        self.dependency_graph: nx.DiGraph = nx.DiGraph()
        self.out_of_scope_calls: Set[str] = set()

        # Internal lookup structures, populated by _initialize_lookup_structures
        # Maps a globally resolvable call name to a single PLSQL_CodeObject (non-overloaded)
        self._code_object_call_names: Dict[str, PLSQL_CodeObject] = {}
        # Maps a globally resolvable call name to a set of overloaded PLSQL_CodeObject instances
        self._overloaded_code_object_call_names: Dict[str, Set[PLSQL_CodeObject]] = {}
        # Maps package name to its local objects (simple name -> object/set of objects)
        # Structure: { "pkg_name": {"normal": {"obj_name": PLSQL_CodeObject}, "overloaded": {"obj_name": {PLSQL_CodeObject,...}}} }
        self._package_wise_code_object_names: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # List of call names that are ambiguous or conflicting at a global level
        self._skip_call_names: List[str] = [] # Should ideally be a Set for faster lookups

        self.logger.info(f"GraphConstructor initialized with {len(code_objects)} code objects.")

    def _register_globally(self, call_name_to_register: str, current_codeobject: PLSQL_CodeObject):
        """
        Attempts to register a call_name for a codeobject in the global lookup maps (_code_object_call_names
        or _overloaded_code_object_call_names).

        Stricter Cleaner Global Rule Enforcement:
        - For packaged objects: Only their fully qualified name (e.g., "pkg.sub.proc") is registered globally.
          Shorter aliases (e.g., "sub.proc", "proc") are NOT registered globally.
        - For non-packaged (truly global) objects: Their simple name (which is their FQ name) is registered globally.
        - Handles conflicts by adding the call_name to _skip_call_names and removing any conflicting entries
          from the global maps.

        Args:
            call_name_to_register: The specific call name (e.g., "pkg.proc", "proc") to consider for global registration.
            current_codeobject: The PLSQL_CodeObject instance being processed.
        """
        is_codeobject_packaged = bool(current_codeobject.package_name)

        # Enforce Stricter Cleaner Global Rule:
        if is_codeobject_packaged:
            # For packaged objects, only their fully qualified name is considered for global registration.
            # All shorter aliases (sub-package.name, simple_name) are skipped for global maps.
            fully_qualified_name_of_current_obj = f"{current_codeobject.package_name}.{current_codeobject.name}"
            if call_name_to_register != fully_qualified_name_of_current_obj:
                self.logger.trace(f"Skipping global registration of alias '{call_name_to_register}' for packaged object {current_codeobject.id} (FQ: {fully_qualified_name_of_current_obj}) as per stricter cleaner global strategy.")
                return

        # If not packaged, all generated names (which will typically only be the simple name for non-packaged objects) are considered.
        # If packaged and it IS the fully_qualified_name, it's also considered for global registration.


        if call_name_to_register in self._skip_call_names:
            self.logger.trace(f"Global call name '{call_name_to_register}' is already in skip list. Ignoring for {current_codeobject.id}.")
            return

        if current_codeobject.overloaded:
            # Current object is OVERLOADED
            if call_name_to_register in self._code_object_call_names:
                # Conflict: This overloaded object's call name clashes with an existing NON-OVERLOADED object.
                conflicting_normal_obj = self._code_object_call_names[call_name_to_register]
                self.logger.warning(
                    f"Name conflict for '{call_name_to_register}': Overloaded object '{current_codeobject.id}' clashes with existing non-overloaded object '{conflicting_normal_obj.id}'. "
                    f"Adding '{call_name_to_register}' to skip list and removing non-overloaded entry."
                )
                if call_name_to_register not in self._skip_call_names:
                    self._skip_call_names.append(call_name_to_register)
                del self._code_object_call_names[call_name_to_register]
                return # Do not register this conflicting name for the current overloaded object in this state.
            
            self._overloaded_code_object_call_names.setdefault(call_name_to_register, set()).add(current_codeobject)
            self.logger.trace(f"Registered globally (overloaded): '{call_name_to_register}' for object {current_codeobject.id}")

        else:
            # Current object is NOT OVERLOADED
            if call_name_to_register in self._code_object_call_names:
                # Conflict: This non-overloaded object's call name clashes with another existing NON-OVERLOADED object.
                existing_obj = self._code_object_call_names[call_name_to_register]
                if existing_obj.id != current_codeobject.id: # Ensure it's a different object causing the conflict
                    self.logger.warning(
                        f"Ambiguous non-overloaded global call name '{call_name_to_register}'. "
                        f"Existing ID: {existing_obj.id}, New ID: {current_codeobject.id}. Adding to skip list."
                    )
                    if call_name_to_register not in self._skip_call_names:
                        self._skip_call_names.append(call_name_to_register)
                    del self._code_object_call_names[call_name_to_register]
                    return # Do not register this conflicting name
            
            elif call_name_to_register in self._overloaded_code_object_call_names:
                # Conflict: This non-overloaded object's call name clashes with an existing OVERLOADED set.
                self.logger.warning(
                    f"Name conflict for '{call_name_to_register}': Non-overloaded object '{current_codeobject.id}' clashes with an existing overloaded set. "
                    f"Adding '{call_name_to_register}' to skip list and removing overloaded entry."
                )
                if call_name_to_register not in self._skip_call_names:
                    self._skip_call_names.append(call_name_to_register)
                del self._overloaded_code_object_call_names[call_name_to_register]
                return # Do not register this conflicting name
            else:
                # No conflict, safe to add to the normal map.
                self._code_object_call_names[call_name_to_register] = current_codeobject
                self.logger.trace(f"Registered globally (normal): '{call_name_to_register}' for object {current_codeobject.id}")

    def _initialize_lookup_structures(self):
        """
        Populates internal lookup dictionaries for efficient access to code objects.
        Implements a "Cleaner Global Strategy":
        - Package-wise lookups store simple names within their package context.
        - Global lookups (_code_object_call_names, _overloaded_code_object_call_names):
            - Store fully qualified names (e.g., pkg.obj) and intermediate qualified names (e.g., sub_pkg.obj).
            - Store simple names (e.g., obj) ONLY for truly global objects (no package).
            - Simple names of packaged objects are NOT added to global lookups.
        - Validates that _overloaded_code_object_call_names entries represent true overloads (>=2 objects).
        """
        self.logger.info("Initializing lookup structures with Cleaner Global Strategy...")
        # Clear existing structures in case of re-initialization
        self._code_object_call_names.clear()
        self._overloaded_code_object_call_names.clear()
        self._package_wise_code_object_names.clear()
        self._skip_call_names.clear()

        for codeobject in self.code_objects:
            if not codeobject.id: # Should be generated by PLSQL_CodeObject itself
                self.logger.warning(f"Code object {codeobject.name} (pkg: {codeobject.package_name}) has no ID. Generating one.")
                codeobject.generate_id()
            self.logger.trace(f"Processing code object: {codeobject.id} (Type: {codeobject.type.value})")

            # package_name is already casefolded by PLSQL_CodeObject
            current_package_context = codeobject.package_name if codeobject.package_name else "" # Use empty string for None package
            object_simple_name = codeobject.name

            package_name_parts = current_package_context.split('.') if current_package_context else []
            if len(package_name_parts) == 2:
                _, package_name = package_name_parts
            else:
                _ = current_package_context
                package_name = None
            

            # Ensure package context exists in the package-wise map
            # 1. Register in package-wise structure (always uses simple_name within its package context)
            if current_package_context not in self._package_wise_code_object_names:
                self._package_wise_code_object_names[current_package_context] = {
                    "normal": {},
                    "overloaded": {}
                }
                self.logger.trace(f"Created new entry for package context: '{current_package_context}'")

            if codeobject.overloaded:
                self._package_wise_code_object_names[current_package_context]["overloaded"].setdefault(object_simple_name, set()).add(codeobject)
                self.logger.trace(f"Registered package-wise (overloaded): '{current_package_context}'.'{object_simple_name}' for {codeobject.id}")

                if package_name:
                    # If the package name is present, we can also register it in the global overloaded map
                    # This allows for package-local resolution of overloaded calls
                    self._overloaded_code_object_call_names.setdefault(f"{package_name}.{object_simple_name}", set()).add(codeobject)
                    self.logger.trace(f"Registered globally (overloaded): '{package_name}.{object_simple_name}' for {codeobject.id}")

            else: # Not overloaded
                if object_simple_name in self._package_wise_code_object_names[current_package_context]["normal"]:
                    existing_pkg_obj = self._package_wise_code_object_names[current_package_context]["normal"][object_simple_name]
                    if existing_pkg_obj.id != codeobject.id: # Should ideally not happen if IDs are unique
                        self.logger.warning(
                            f"Ambiguous non-overloaded name '{object_simple_name}' in package '{current_package_context}'. "
                            f"Existing ID: {existing_pkg_obj.id}, New ID: {codeobject.id}. Overwriting with new one for package-local resolution."
                        ) # This overwrite is the current behavior for package-local conflicts.

                self._package_wise_code_object_names[current_package_context]["normal"][object_simple_name] = codeobject
                self.logger.trace(f"Registered package-wise (normal): '{current_package_context}'.'{object_simple_name}' for {codeobject.id}")

                if package_name:
                    # If the package name is present, we can also register it in the global normal map
                    # This allows for package-local resolution of non-overloaded calls
                    self._code_object_call_names[f"{package_name}.{object_simple_name}"] = codeobject
                    self.logger.trace(f"Registered globally (normal): '{package_name}.{object_simple_name}' for {codeobject.id}")


            # 2. Register globally (fully qualified names, intermediate names, and simple names for truly global objects)
            package_name_parts = current_package_context.split('.') if current_package_context else []
            for i in range(len(package_name_parts) + 1):
                prefix_parts = package_name_parts[i:]
                call_name_prefix = ".".join(filter(None, prefix_parts))
                
                code_object_call_name = f"{call_name_prefix}.{object_simple_name}" if call_name_prefix else object_simple_name
                
                self._register_globally(code_object_call_name, codeobject)

        # 3. Validate _overloaded_code_object_call_names to ensure sets have >= 2 objects
        self.logger.debug("Validating global overloaded map for true overloads (>= 2 objects per call name).")
        invalid_overload_names_to_reclassify: Dict[str, PLSQL_CodeObject] = {}
        call_names_to_remove_from_overloaded_map: List[str] = []

        for call_name, obj_set in list(self._overloaded_code_object_call_names.items()): # Iterate on a copy
            if len(obj_set) < 2:
                self.logger.warning(
                    f"Global call name '{call_name}' is in the overloaded map but contains only {len(obj_set)} object(s) ({[obj.id for obj in obj_set]}). "
                    f"This is not a valid overload set. Attempting to reclassify."
                )
                call_names_to_remove_from_overloaded_map.append(call_name)
                if len(obj_set) == 1:
                    single_obj = list(obj_set)[0]
                    invalid_overload_names_to_reclassify[call_name] = single_obj
        
        for call_name in call_names_to_remove_from_overloaded_map:
            if call_name in self._overloaded_code_object_call_names:
                del self._overloaded_code_object_call_names[call_name]
                self.logger.trace(f"Removed '{call_name}' from overloaded map due to invalid member count.")

        for call_name, single_obj in invalid_overload_names_to_reclassify.items():
            if call_name in self._skip_call_names:
                self.logger.info(f"Skipping reclassification of '{call_name}' (from invalid overload of {single_obj.id}) as it's already in the global skip list.")
                continue
            
            if call_name in self._code_object_call_names:
                existing_normal_obj = self._code_object_call_names[call_name]
                if existing_normal_obj.id != single_obj.id:
                    self.logger.warning(
                        f"Conflict during reclassification of '{call_name}' (object {single_obj.id} from invalid overload). "
                        f"It already exists in the normal map with a different object '{existing_normal_obj.id}'. "
                        f"Adding '{call_name}' to skip list and removing existing normal entry."
                    )
                    if call_name not in self._skip_call_names:
                        self._skip_call_names.append(call_name)
                    del self._code_object_call_names[call_name]
            elif call_name in self._overloaded_code_object_call_names: 
                self.logger.error(f"Internal logic error: '{call_name}' (for {single_obj.id}) found in overloaded map during reclassification fixup, should have been removed.")
            else:
                self.logger.info(f"Reclassifying '{call_name}' (object: {single_obj.id}) from invalid overload set to normal global map.")
                self._code_object_call_names[call_name] = single_obj

        self.logger.info("Lookup structures initialized.")
        if self._skip_call_names:
            unique_skipped_names = sorted(list(set(self._skip_call_names)))
            self.logger.warning(f"Skipped {len(unique_skipped_names)} unique ambiguous/conflicting global call name(s): {unique_skipped_names}")

    def _add_nodes_to_graph(self):
        """Adds all processed PLSQL_CodeObject instances as nodes to the dependency graph."""
        self.logger.info(f"Adding {len(self.code_objects)} code objects as nodes to the graph.")
        for codeobject in self.code_objects:
            if codeobject.id not in self.dependency_graph.nodes:
                self.dependency_graph.add_node(codeobject.id, object=codeobject)
                self.logger.trace(f"Added node: {codeobject.id} (Name: {codeobject.name}, Pkg: {codeobject.package_name})")
            else:
                self.logger.trace(f"Node {codeobject.id} already exists in graph.")
        self.logger.info(f"Finished adding nodes. Graph now has {self.dependency_graph.number_of_nodes()} nodes.")

    def _add_new_edge(self, source_node_id: str, target_node_id: str):
        """
        Helper method to add an edge to the dependency graph.
        Avoids self-loops and logs if the target node doesn't exist (though it should).
        """
        if source_node_id == target_node_id:
            self.logger.trace(f"Skipping self-loop edge from {source_node_id} to itself.")
            return

        if self.dependency_graph.has_node(target_node_id):
            if not self.dependency_graph.has_edge(source_node_id, target_node_id):
                self.dependency_graph.add_edge(source_node_id, target_node_id)
                self.logger.trace(f"Added edge: {source_node_id} -> {target_node_id}")
            else:
                self.logger.trace(f"Edge {source_node_id} -> {target_node_id} already exists.")
        else:
            # This case should ideally be handled by creating placeholder nodes for out-of-scope calls.
            self.logger.warning(f"Attempted to add edge from {source_node_id} to non-existent target node: {target_node_id}. This might indicate an out-of-scope call not yet represented as a placeholder.")
            # Optionally, create a placeholder here if not handled elsewhere
            if target_node_id not in self.dependency_graph:
                 # Create a minimal PLSQL_CodeObject for this unknown dependency
                dep_split = target_node_id.split('.') # Assuming target_node_id is a qualified name
                obj_name = dep_split[-1]
                pkg_name = ".".join(dep_split[:-1]) if len(dep_split) > 1 else ""
                placeholder_obj = PLSQL_CodeObject(name=obj_name, package_name=pkg_name, type=CodeObjectType.UNKNOWN)
                placeholder_obj.id = target_node_id # Explicitly set ID
                self.dependency_graph.add_node(target_node_id, object=placeholder_obj)
                self.logger.info(f"Created placeholder node for out-of-scope target: {target_node_id}")
                self.dependency_graph.add_edge(source_node_id, target_node_id)
                self.logger.trace(f"Added edge to new placeholder: {source_node_id} -> {target_node_id}")

    def _resolve_and_add_dependencies_for_call(
        self,
        source_code_object: PLSQL_CodeObject,
        extracted_call: CallDetailsTuple
    ):
        """
        Resolves a single extracted call and adds the corresponding dependency edge.
        Handles normal calls, overloaded calls, and out-of-scope calls.
        Resolution order:
        1. Global exact match for dep_call_name (Normal).
        2. Package-local simple name match for dep_call_name (Normal).
        3. Contextual FQN (current_pkg + dep_call_name) global match (Normal).
        4. Global exact match for dep_call_name (Overloaded).
        5. Package-local simple name match for dep_call_name (Overloaded).
        6. Contextual FQN (current_pkg + dep_call_name) global match (Overloaded).
        """

        # call_name from ExtractedCallTuple should be used for lookup.
        # It's assumed to be case-normalized if necessary by the extractor, or normalize here.
        
        dep_call_name = extracted_call.call_name.casefold() # Normalize for lookup
        source_node_id = source_code_object.id
        current_pkg_context = source_code_object.package_name # Already casefolded

        self.logger.trace(f"Resolving call '{dep_call_name}' from {source_node_id} (in pkg '{current_pkg_context}')")

        target_node_id: Optional[str] = None
        resolved_object: Optional[PLSQL_CodeObject] = None
        candidate_objects_for_overload: Optional[Set[PLSQL_CodeObject]] = None
        
        # This flag tracks if we entered an overload resolution path,
        # regardless of whether it was successful or found candidates.
        an_overload_resolution_path_was_attempted = False

        # --- Stage 1: Attempt to resolve as a NON-OVERLOADED call ---
        # 1.1 Check globally defined non-overloaded calls (exact match for dep_call_name)
        # This uses the `_code_object_call_names` which, after the stricter `_register_globally`,
        # should only contain FQNs for packaged objects or simple names for non-packaged objects.
        if dep_call_name in self._code_object_call_names:
            resolved_object = self._code_object_call_names[dep_call_name]
            self.logger.trace(f"Call '{dep_call_name}' resolved via global normal map to: {resolved_object.id}")
        
        # 1.2 Check package-local non-overloaded calls (dep_call_name as simple name)
        # This implies dep_call_name would be a simple name here (e.g., "proc" not "pkg.proc").
        # `_package_wise_code_object_names` stores simple names under their full package context.
        elif current_pkg_context and dep_call_name in self._package_wise_code_object_names.get(current_pkg_context, {}).get("normal", {}):
            resolved_object = self._package_wise_code_object_names[current_pkg_context]["normal"][dep_call_name]
            self.logger.trace(f"Call '{dep_call_name}' resolved via package-local ('{current_pkg_context}') normal map to: {resolved_object.id}")
        
        # 1.3 Try constructing FQN with current package context (if dep_call_name is not already an FQN found above)
        # This handles calls like `sub_proc()` from `pkg.main_proc` resolving to `pkg.sub_proc`,
        # or `sub_pkg.sub_proc()` from `main_pkg` resolving to `main_pkg.sub_pkg.sub_proc`.
        # The `dep_call_name` itself might be partially qualified (e.g. "sub_pkg.sub_proc").
        # We only try this if `current_pkg_context` exists.
        elif current_pkg_context:
            # Avoid redundant construction if dep_call_name already starts with the context (e.g. call is "pkg.sub" from "pkg")
            # However, a call like "sub_pkg.another_proc" from "pkg" should form "pkg.sub_pkg.another_proc"
            potential_fqn = f"{current_pkg_context}.{dep_call_name}"
            if potential_fqn in self._code_object_call_names:
                resolved_object = self._code_object_call_names[potential_fqn]
                self.logger.trace(f"Call '{dep_call_name}' (from '{current_pkg_context}') resolved by constructing FQN '{potential_fqn}' via global normal map to: {resolved_object.id}")

        if resolved_object:
            target_node_id = resolved_object.id
            # Fallthrough to add edge if target_node_id is set

        # --- Stage 2: If not resolved as non-overloaded, attempt as OVERLOADED call ---
        if not target_node_id: 
            an_overload_resolution_path_was_attempted = True # Mark that we are now trying overload resolution paths
            
            # 2.1 Check globally defined overloaded calls (exact match for dep_call_name)
            if dep_call_name in self._overloaded_code_object_call_names:
                candidate_objects_for_overload = self._overloaded_code_object_call_names[dep_call_name]
                self.logger.trace(f"Call '{dep_call_name}' found in global overloaded map. Candidates: {[c.id for c in candidate_objects_for_overload] if candidate_objects_for_overload else 'None'}")
            
            # 2.2 Check package-local overloaded calls (dep_call_name as simple name)
            elif current_pkg_context and dep_call_name in self._package_wise_code_object_names.get(current_pkg_context, {}).get("overloaded", {}):
                candidate_objects_for_overload = self._package_wise_code_object_names[current_pkg_context]["overloaded"][dep_call_name]
                self.logger.trace(f"Call '{dep_call_name}' found in package-local ('{current_pkg_context}') overloaded map. Candidates: {[c.id for c in candidate_objects_for_overload] if candidate_objects_for_overload else 'None'}")
            
            # 2.3 Try constructing FQN with current package context for overloaded calls
            elif current_pkg_context:
                potential_fqn = f"{current_pkg_context}.{dep_call_name}"
                if potential_fqn in self._overloaded_code_object_call_names:
                    candidate_objects_for_overload = self._overloaded_code_object_call_names[potential_fqn]
                    self.logger.trace(f"Call '{dep_call_name}' (from '{current_pkg_context}') resolved by constructing FQN '{potential_fqn}' via global overloaded map. Candidates: {[c.id for c in candidate_objects_for_overload] if candidate_objects_for_overload else 'None'}")

            if candidate_objects_for_overload:
                # _handle_overloaded_call_resolution will add the edge if successful,
                # or add to out_of_scope_calls if it fails.
                self._handle_overloaded_call_resolution(source_code_object, dep_call_name, extracted_call, candidate_objects_for_overload)
                return # Resolution (successful or failed and logged) is handled by the call above.
            # If no candidates were found by any overload lookup, an_overload_resolution_path_was_attempted is true,
            # but candidate_objects_for_overload is None. We fall through to out-of-scope handling.

        # --- Stage 3: Add edge or handle out-of-scope ---
        if target_node_id: # This means a non-overloaded call was successfully resolved directly in Stage 1
            self._add_new_edge(source_node_id, target_node_id)
        elif not an_overload_resolution_path_was_attempted or \
             (an_overload_resolution_path_was_attempted and not candidate_objects_for_overload):
            # This covers:
            # 1. The call name was not found in any normal map (target_node_id is None) AND
            #    it was also not found in any overload map (an_overload_resolution_path_was_attempted is True but candidate_objects_for_overload is None).
            # 2. The call name was not found in any normal map AND it was not even attempted as an overload because the name didn't appear in overload maps
            #    (an_overload_resolution_path_was_attempted would be False if we restructured logic, but with current flow, it's simpler).
            # Essentially, if we are here, no successful resolution (normal or overloaded) occurred and no candidates for overload were even found.
            
            self.logger.debug(f"Call '{dep_call_name}' from {source_node_id} is out of scope (not found in any lookup structure or no overload candidates identified). Adding to out_of_scope_calls.")
            self.out_of_scope_calls.add(dep_call_name)
            
            # Create a placeholder node for this out-of-scope call if it looks like a qualified name
            # This helps visualize unresolved dependencies to potentially known external entities.
            if '.' in dep_call_name: # Heuristic: could be schema.pkg.obj or pkg.obj
                placeholder_id = dep_call_name # Use the call name itself as ID
                if placeholder_id not in self.dependency_graph:
                    dep_split = dep_call_name.split('.')
                    obj_name_for_placeholder = dep_split[-1]
                    pkg_name_for_placeholder = ".".join(dep_split[:-1]) if len(dep_split) > 1 else ""
                    
                    # Create a minimal PLSQL_CodeObject for this unknown dependency
                    placeholder_obj = PLSQL_CodeObject(
                        name=obj_name_for_placeholder, 
                        package_name=pkg_name_for_placeholder, 
                        type=CodeObjectType.UNKNOWN
                    )
                    placeholder_obj.id = placeholder_id # Explicitly set ID
                    
                    self.dependency_graph.add_node(placeholder_id, object=placeholder_obj)
                    self.logger.info(f"Created placeholder node for out-of-scope call: {placeholder_id}")
                
                # Add edge to placeholder if it's not a self-reference to a placeholder
                # (e.g. if source_code_object itself was a placeholder for some reason)
                if source_node_id != placeholder_id:
                    self._add_new_edge(source_node_id, placeholder_id)
        # If an_overload_resolution_path_was_attempted was True and candidate_objects_for_overload was populated,
        # then _handle_overloaded_call_resolution was called and it returned, so we don't reach here.

    def _handle_overloaded_call_resolution(
        self,
        source_code_object: PLSQL_CodeObject,
        dep_call_name: str,
        extracted_call: CallDetailsTuple,
        candidate_objects: Set[PLSQL_CodeObject]
    ):
        """
        Handles the resolution logic for an overloaded call.
        """
        self.logger.trace(f"Attempting to resolve overloaded call '{dep_call_name}' from {source_code_object.id}. Candidates: {[c.id for c in candidate_objects]}")

        # if not self._find_correct_overloaded_codeobject_func:
        #     self.logger.warning(f"Overload resolver function not provided. Cannot resolve '{dep_call_name}'. Adding to out_of_scope.")
        #     self.out_of_scope_calls.add(f"\"{dep_call_name} (overloaded, resolver_unavailable)\"")
        #     return

        if source_code_object.clean_code is None:
            self.logger.warning(f"Source code for {source_code_object.id} is None. Cannot extract parameters for call '{dep_call_name}'.")
            self.out_of_scope_calls.add(f"\"{dep_call_name} (overloaded, source_unavailable)\"")
            return


        # # Prepare candidate parameters map: Dict[object_id, List[Dict[str, Any]]]
        # # The PLSQL_CodeObject.parsed_parameters is List[Dict[str, Any]]
        # candidates_params_map: Dict[str, List[Dict[str, Any]]] = {
        #     cand.id: cand.parsed_parameters
        #     for cand in candidate_objects
        #     if cand.id != source_code_object.id  # Exclude direct self-reference from candidates
        # }

        if not candidate_objects:
            self.logger.trace(f"No valid candidates for overloaded call '{dep_call_name}' after filtering self-reference.")
            self.out_of_scope_calls.add(f"{dep_call_name} (overloaded, no_candidates)")
            return

        try:
            resolved_target = resolve_overloaded_call(
                candidate_objects, extracted_call, self.logger
            )
            resolved_target_id = resolved_target.id if resolved_target else resolved_target
            if resolved_target_id:
                self.logger.info(f"Overloaded call '{dep_call_name}' (params: \"{extracted_call}\") resolved to ID: {resolved_target_id}")
                self._add_new_edge(source_code_object.id, resolved_target_id)
            else:
                self.logger.warning(f"Could not resolve overloaded call '{dep_call_name}' (params: \"{extracted_call}\") from {source_code_object.id}. No matching signature found among candidates.")
                self.out_of_scope_calls.add(f"{dep_call_name} (overloaded, resolution_failed: {extracted_call})")
        except Exception as e:
            self.logger.error(f"Exception during overload resolution for '{dep_call_name}' (params: \"{extracted_call}\") from {source_code_object.id}: {e}", exc_info=True)
            self.out_of_scope_calls.add(f"{dep_call_name} (overloaded, resolution_exception: {extracted_call})")

    def _add_edges_to_graph(self):
        """
        Identifies and adds dependency edges between code objects based on extracted calls.
        This adapts the main loop of 'create_dependency_graph' from dummy.py.
        """
        self.logger.info("Starting to add dependency edges to the graph...")
        nodes_to_process = list(self.dependency_graph.nodes) # Process a static list of nodes
        
        for source_node_id in tqdm(nodes_to_process, desc="Building Edges", disable=not self.verbose):
            source_code_object: PLSQL_CodeObject = self.dependency_graph.nodes[source_node_id]['object']
            self.logger.trace(f"Processing source object for edges: {source_node_id} (Name: {source_code_object.name})")

            if not source_code_object.extracted_calls:
                self.logger.trace(f"No extracted calls for {source_node_id}. Skipping.")
                continue

            if source_code_object.clean_code is None:
                self.logger.warning(f"Source code for {source_node_id} is None. Cannot process its calls for parameter extraction.")
                # Add all its extracted calls (by name only) to out_of_scope if this happens
                for call in source_code_object.extracted_calls:
                    self.out_of_scope_calls.add(f"{call.call_name.lower()} (source_unavailable_for_params)")
                continue

            for extracted_call in source_code_object.extracted_calls:
                # extracted_call is ExtractedCallTuple(call_name, line_no, start_idx, end_idx)
                self._resolve_and_add_dependencies_for_call(source_code_object, extracted_call)

        self.logger.info(f"Finished adding edges. Graph now has {self.dependency_graph.number_of_edges()} edges.")

    def build_graph(self) -> Tuple[nx.DiGraph, Set[str]]:
        """
        Orchestrates the entire graph construction process:
        1. Initializes lookup structures.
        2. Adds nodes (code objects) to the graph.
        3. Adds edges (dependencies) to the graph by resolving calls.

        Returns:
            A tuple containing the constructed NetworkX DiGraph and a set of
            out-of-scope call names encountered during the process.
        """
        self.logger.info("Starting dependency graph construction...")

        self._initialize_lookup_structures()
        self._add_nodes_to_graph()
        self._add_edges_to_graph()

        self.logger.info(
            f"Graph construction complete. "
            f"Nodes: {self.dependency_graph.number_of_nodes()}, "
            f"Edges: {self.dependency_graph.number_of_edges()}."
        )
        if self.out_of_scope_calls:
            self.logger.warning(f"Encountered {len(self.out_of_scope_calls)} out-of-scope/unresolved calls. See details in logs or returned set.")
            for i, call_name in enumerate(list(self.out_of_scope_calls)[:10]): # Log a few examples
                 self.logger.debug(f"  Example out-of-scope call [{i+1}]: {call_name}")
            if len(self.out_of_scope_calls) > 10:
                 self.logger.debug(f"  ... and {len(self.out_of_scope_calls) - 10} more.")


        return self.dependency_graph, self.out_of_scope_calls

# Example Usage (Illustrative - requires actual functions for overload/param extraction)
if __name__ == '__main__':
    # --- Basic Logger Setup for Example ---
    import sys
    example_logger = lg.logger
    example_logger.remove()
    example_logger.add(
        sys.stderr,
        level="TRACE", # Set to TRACE for detailed output from example
        colorize=True,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
    )
    example_logger.info("Running GraphConstructor example...")

    # --- Sample Code Objects ---
    # Object 1: Calls proc2 and an overloaded procedure
    obj1_params = [{"name": "p1", "type": "VARCHAR2", "mode": "IN"}]
    obj1_source = "BEGIN pkg1.proc2(123); pkg1.overloaded_proc('param_for_v1'); pkg1.overloaded_proc(p_arg => 'version2_val'); END;"
    obj1 = PLSQL_CodeObject(name="proc1", package_name="pkg1", clean_code=obj1_source,
                            type=CodeObjectType.PROCEDURE, parsed_parameters=obj1_params)
    obj1.extracted_calls = [ # Manually create CallDetailsTuple instances
        CallDetailsTuple(call_name='pkg1.proc2', line_no=1, start_idx=6, end_idx=16, positional_params=[], named_params={}),
        CallDetailsTuple(call_name='pkg1.overloaded_proc', line_no=1, start_idx=23, end_idx=43, positional_params=['param_for_v1'], named_params={}),
        CallDetailsTuple(call_name='pkg1.overloaded_proc', line_no=1, start_idx=65, end_idx=85, positional_params=[], named_params={'p_arg': "'version2_val'"})
    ]

    # Object 2: A simple procedure
    obj2_params = [{"name": "p_val", "type": "NUMBER"}]
    obj2_source = "BEGIN DBMS_OUTPUT.PUT_LINE('Hello from proc2'); END;"
    obj2 = PLSQL_CodeObject(name="proc2", package_name="pkg1", clean_code=obj2_source,
                            type=CodeObjectType.PROCEDURE, parsed_parameters=obj2_params)
    obj2.extracted_calls = [
        CallDetailsTuple(call_name='DBMS_OUTPUT.PUT_LINE', line_no=1, start_idx=6, end_idx=26, positional_params=[], named_params={})
    ]

    # Overloaded Procedure - Version 1 (e.g., takes a VARCHAR2)
    over1_v1_params = [{"name": "op_text", "type": "VARCHAR2", "mode": "IN"}]
    over1_v1 = PLSQL_CodeObject(name="overloaded_proc", package_name="pkg1", clean_code="-- Source for overloaded_proc V1 (text)",
                                type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=over1_v1_params)

    # Overloaded Procedure - Version 2 (e.g., takes a NUMBER or different named param)
    over1_v2_params = [{"name": "p_arg", "type": "VARCHAR2", "mode": "IN"}] # Changed param name for mock
    over1_v2 = PLSQL_CodeObject(name="overloaded_proc", package_name="pkg1", clean_code="-- Source for overloaded_proc V2 (numeric)",
                                type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=over1_v2_params)
    # Explicitly set different ID for mock, though generate_id would do this based on params
    # over1_v2.id = "pkg1.overloaded_proc-version2_sig_hash"


    # Unknown/External call
    obj3_source = "BEGIN unknown_package.external_call(SYSDATE); unknown_internal_call(); END;"
    obj3 = PLSQL_CodeObject(name="proc3", package_name="pkg1", clean_code=obj3_source, type=CodeObjectType.PROCEDURE)
    obj3.extracted_calls = [
        CallDetailsTuple(call_name='unknown_package.external_call', line_no=1, start_idx=6, end_idx=35, positional_params=['SYSDATE'], named_params={}),
        CallDetailsTuple(call_name='unknown_internal_call', line_no=1, start_idx=37, end_idx=61, positional_params=[], named_params={})
    ]


    all_code_objects = [obj1, obj2, over1_v1, over1_v2, obj3]
    for co in all_code_objects:
        if not co.id: # Ensure IDs are generated if not manually set for mocks
            co.generate_id()
        example_logger.debug(f"Prepared CO: {co.id}, Name: {co.name}, Pkg: {co.package_name}, Overloaded: {co.overloaded}, Params: {co.parsed_parameters}")


    # --- Instantiate and Run GraphConstructor ---
    constructor = GraphConstructor(
        code_objects=all_code_objects,
        logger=example_logger,
        # find_correct_overloaded_codeobject_func=mock_find_correct_overloaded_codeobject,
        verbose=True # Enables tqdm in build_graph if constructor uses it
    )

    graph, out_of_scope = constructor.build_graph()

    # --- Print Results ---
    example_logger.info("\n--- Graph Construction Results ---")
    example_logger.info(f"Number of nodes in graph: {graph.number_of_nodes()}")
    example_logger.info(f"Number of edges in graph: {graph.number_of_edges()}")

    example_logger.info("\nNodes:")
    for node_id, node_data in graph.nodes(data=True):
        obj_instance = node_data.get('object')
        obj_type_val = obj_instance.type.value if obj_instance else "N/A"
        example_logger.info(f"  Node ID: {node_id} (Type: {obj_type_val})")

    example_logger.info("\nEdges:")
    for source, target, data in graph.edges(data=True):
        example_logger.info(f"  Edge: {source} ---> {target}")

    example_logger.info(f"\nOut-of-Scope Calls ({len(out_of_scope)}):")
    for i, call_name in enumerate(out_of_scope):
        example_logger.info(f"  [{i+1}] {call_name}")

    example_logger.info("GraphConstructor example finished.")
