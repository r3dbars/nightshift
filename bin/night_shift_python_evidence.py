"""Conservative Python call evidence shared by queue and draft verification."""
from __future__ import annotations

import ast


def owner_symbol_call_count_text(text: str, owner: str, symbol: str) -> int | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    aliases = {owner} if owner else set()
    aliases.update(
        alias.asname or alias.name
        for node in tree.body if isinstance(node, ast.ImportFrom)
        for alias in node.names if alias.name == owner
    )
    trusted_qualifiers = {
        target.id
        for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Name)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "module_from_spec"
    }

    def expression_calls(node: ast.AST, instances: set[str], qualifiers: set[str]) -> int:
        count = 0

        class Calls(ast.NodeVisitor):
            def visit_FunctionDef(self, _node):
                return None

            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef
            visit_Lambda = visit_FunctionDef

            def visit_Call(self, call: ast.Call):
                nonlocal count
                function = call.func
                if not owner and isinstance(function, ast.Name) and function.id == symbol:
                    count += 1
                if isinstance(function, ast.Attribute) and function.attr == symbol:
                    receiver = function.value
                    direct = (
                        isinstance(receiver, ast.Call)
                        and (
                            (isinstance(receiver.func, ast.Name) and receiver.func.id in aliases)
                            or (
                                isinstance(receiver.func, ast.Attribute)
                                and receiver.func.attr == owner
                                and isinstance(receiver.func.value, ast.Name)
                                and receiver.func.value.id in qualifiers
                            )
                        )
                    )
                    named = isinstance(receiver, ast.Name) and receiver.id in instances
                    count += int(direct or named)
                self.generic_visit(call)

        Calls().visit(node)
        return count

    def assigned_names(node: ast.Assign | ast.AnnAssign) -> set[str]:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return {target.id for target in targets if isinstance(target, ast.Name)}

    def direct_owner_constructor(node: ast.AST | None, qualifiers: set[str]) -> bool:
        return isinstance(node, ast.Call) and (
            (isinstance(node.func, ast.Name) and node.func.id in aliases)
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == owner
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in qualifiers
            )
        )

    def owner_constructor(
        node: ast.AST | None, qualifiers: set[str], factory_methods: set[str]
    ) -> bool:
        if direct_owner_constructor(node, qualifiers):
            return True
        return bool(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in factory_methods
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
        )

    def proven_class_factories(node: ast.ClassDef, qualifiers: set[str]) -> set[str]:
        proven: set[str] = set()
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            returns = [value for value in ast.walk(child) if isinstance(value, ast.Return)]
            if len(returns) == 1 and direct_owner_constructor(returns[0].value, qualifiers):
                proven.add(child.name)
        return proven

    def compound_rebindings(node: ast.AST) -> set[str]:
        names: set[str] = set()

        class Bindings(ast.NodeVisitor):
            def visit_FunctionDef(self, _node):
                return None

            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef
            visit_Lambda = visit_FunctionDef

            def visit_Name(self, value: ast.Name):
                if isinstance(value.ctx, (ast.Store, ast.Del)):
                    names.add(value.id)

        Bindings().visit(node)
        return names

    def scan(
        body: list[ast.stmt], initial: set[str] | None = None,
        qualifiers: set[str] | None = None, factory_methods: set[str] | None = None,
    ) -> int:
        instances = set(initial or ())
        active_qualifiers = set(trusted_qualifiers if qualifiers is None else qualifiers)
        active_factories = set(factory_methods or ())
        count = 0
        for statement in body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                rebound = set().union(*(compound_rebindings(item) for item in statement.body))
                nested_factories = (
                    proven_class_factories(statement, active_qualifiers - rebound)
                    if isinstance(statement, ast.ClassDef) else active_factories
                )
                count += scan(
                    statement.body, qualifiers=active_qualifiers - rebound,
                    factory_methods=nested_factories,
                )
                continue
            compound = isinstance(
                statement, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)
            )
            if isinstance(statement, (ast.If, ast.While)):
                count += expression_calls(statement.test, instances, active_qualifiers)
            elif isinstance(statement, (ast.For, ast.AsyncFor)):
                count += expression_calls(statement.iter, instances, active_qualifiers)
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                count += sum(expression_calls(item.context_expr, instances, active_qualifiers) for item in statement.items)
            elif not compound:
                count += expression_calls(statement, instances, active_qualifiers)
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                names = assigned_names(statement)
                instances.difference_update(names)
                if owner_constructor(statement.value, active_qualifiers, active_factories):
                    instances.update(names)
            elif isinstance(statement, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)):
                branches = []
                for attribute in ("body", "orelse", "finalbody"):
                    branches.append(getattr(statement, attribute, []))
                branches.extend(handler.body for handler in getattr(statement, "handlers", []))
                count += sum(
                    scan(branch, instances, active_qualifiers, active_factories) for branch in branches
                )
                instances.difference_update(compound_rebindings(statement))
        return count

    return scan(tree.body)


def semantic_test_contract_reasons(
    texts: list[str], contract: dict, owner: str, symbol: str
) -> list[str]:
    reasons: list[str] = []
    calls = 0
    assertion_rows: list[tuple[int, str]] = []
    boolean_outcomes: set[bool] = set()
    for text in texts:
        counted = owner_symbol_call_count_text(text, owner, symbol)
        if counted is None:
            return ["patched test could not be parsed for semantic proof"]
        calls += counted
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return ["patched test could not be parsed for semantic proof"]
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                assertion_rows.append((node.lineno, ast.get_source_segment(text, node) or ""))
                boolean_outcomes.update(
                    value.value for value in ast.walk(node)
                    if isinstance(value, ast.Constant) and isinstance(value.value, bool)
                )
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                name = node.func.attr
                if name.startswith("assert"):
                    assertion_rows.append((node.lineno, ast.get_source_segment(text, node) or ""))
                if name == "assertTrue":
                    boolean_outcomes.add(True)
                elif name == "assertFalse":
                    boolean_outcomes.add(False)
    minimum = int(contract.get("minimum_target_invocations") or 0)
    if minimum and calls < minimum:
        reasons.append(f"semantic contract requires at least {minimum} target invocations; found {calls}")
    required_bools = set(contract.get("required_boolean_outcomes") or [])
    if required_bools and not required_bools.issubset(boolean_outcomes):
        reasons.append("semantic contract requires assertions for both boolean outcomes")
    ordered = [str(term).lower() for term in contract.get("ordered_terms") or []]
    if len(ordered) == 2:
        first_lines = [line for line, source in assertion_rows if ordered[0] in source.lower()]
        second_lines = [line for line, source in assertion_rows if ordered[1] in source.lower()]
        if not first_lines or not second_lines or min(first_lines) >= max(second_lines):
            reasons.append(f"semantic contract requires ordered assertions for {ordered[0]} then {ordered[1]}")
    return reasons
