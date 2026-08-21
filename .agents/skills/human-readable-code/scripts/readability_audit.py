#!/usr/bin/env python3
"""Heuristic Python readability audit using only the standard library.

Usage:
    python readability_audit.py path/to/file_or_directory
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

LONG_FUNCTION_LINES = 60
MANY_PARAMS = 7
DEEP_NESTING = 4

class Audit(ast.NodeVisitor):
    def __init__(self):
        self.findings = []

    def add(self, node, kind, msg):
        self.findings.append((getattr(node, "lineno", 0), kind, msg))

    def visit_FunctionDef(self, node):
        end = getattr(node, "end_lineno", node.lineno)
        length = end - node.lineno + 1
        if length > LONG_FUNCTION_LINES:
            self.add(node, "LONG_FUNCTION", f"{node.name}: {length} lines")
        total_args = len(node.args.posonlyargs) + len(node.args.args) + len(node.args.kwonlyargs)
        if node.args.vararg:
            total_args += 1
        if node.args.kwarg:
            total_args += 1
        if total_args > MANY_PARAMS:
            self.add(node, "MANY_PARAMS", f"{node.name}: {total_args} parameters")
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def nesting_depth(self, node, depth=1):
        if depth > DEEP_NESTING:
            self.add(node, "DEEP_NESTING", f"nesting depth >= {depth}")
            return
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.Match)):
                self.nesting_depth(child, depth + 1)

    def visit_If(self, node):
        self.nesting_depth(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.add(node, "BARE_EXCEPT", "bare except hides failure type")
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            self.add(node, "BROAD_EXCEPT", "verify broad exception handling is intentional")
        self.generic_visit(node)

def iter_python(path: Path):
    if path.is_file() and path.suffix == ".py":
        yield path
    elif path.is_dir():
        for item in sorted(path.rglob("*.py")):
            if ".venv" not in item.parts and "venv" not in item.parts:
                yield item

def main(raw_path: str) -> int:
    target = Path(raw_path)
    if not target.exists():
        print(f"ERROR: not found: {target}", file=sys.stderr)
        return 2

    files_scanned = 0
    total_findings = 0

    for path in iter_python(target):
        files_scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as exc:
            print(f"{path}: PARSE_ERROR: {exc}")
            continue

        audit = Audit()
        audit.visit(tree)

        if audit.findings:
            print(f"\n{path}")
            for line, kind, msg in sorted(audit.findings):
                total_findings += 1
                print(f"  L{line}: {kind}: {msg}")

    print(f"\nFILES_SCANNED: {files_scanned}")
    print(f"FINDINGS: {total_findings}")
    print("NOTE: findings are heuristic review prompts, not automatic failures.")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python readability_audit.py FILE_OR_DIRECTORY", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
