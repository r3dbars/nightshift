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

    def owner_constructor(node: ast.AST | None, qualifiers: set[str]) -> bool:
        return isinstance(node, ast.Call) and (
            (isinstance(node.func, ast.Name) and node.func.id in aliases)
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == owner
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in qualifiers
            )
        )

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
        body: list[ast.stmt], initial: set[str] | None = None, qualifiers: set[str] | None = None
    ) -> int:
        instances = set(initial or ())
        active_qualifiers = set(trusted_qualifiers if qualifiers is None else qualifiers)
        count = 0
        for statement in body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                rebound = set().union(*(compound_rebindings(item) for item in statement.body))
                count += scan(statement.body, qualifiers=active_qualifiers - rebound)
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
                if owner_constructor(statement.value, active_qualifiers):
                    instances.update(names)
            elif isinstance(statement, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)):
                branches = []
                for attribute in ("body", "orelse", "finalbody"):
                    branches.append(getattr(statement, attribute, []))
                branches.extend(handler.body for handler in getattr(statement, "handlers", []))
                count += sum(scan(branch, instances, active_qualifiers) for branch in branches)
                instances.difference_update(compound_rebindings(statement))
        return count

    return scan(tree.body)
