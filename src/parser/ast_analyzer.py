"""
AST (Abstract Syntax Tree) Analyzer.
Extracts enclosing function, class, and architectural context for modified lines
and identifies structural patterns/anti-patterns.
"""

import ast
from typing import Dict, List, Any, Optional

class ASTContext:
    """Stores semantic scope information about a code snippet."""
    def __init__(self, enclosing_function: Optional[str] = None,
                 enclosing_class: Optional[str] = None,
                 docstring: Optional[str] = None,
                 parameters: Optional[List[str]] = None,
                 imported_modules: Optional[List[str]] = None,
                 ast_flags: Optional[List[str]] = None):
        self.enclosing_function = enclosing_function
        self.enclosing_class = enclosing_class
        self.docstring = docstring
        self.parameters = parameters or []
        self.imported_modules = imported_modules or []
        self.ast_flags = ast_flags or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enclosing_function": self.enclosing_function,
            "enclosing_class": self.enclosing_class,
            "docstring": self.docstring,
            "parameters": self.parameters,
            "imported_modules": self.imported_modules,
            "ast_flags": self.ast_flags,
        }

class PythonASTAnalyzer:
    """Analyzes Python code to provide structural AST context for diff hunks."""

    @staticmethod
    def analyze_source(source_code: str) -> Dict[str, Any]:
        """
        Parses source code and indexes all functions, classes, and scopes with their line boundaries.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {"error": "Syntax error parsing source code", "scopes": []}

        scopes = []
        imports = []
        ast_flags = []

        for node in ast.walk(tree):
            # Track imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

            # Detect dangerous functions
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ("eval", "exec"):
                    ast_flags.append({
                        "type": "DANGEROUS_CALL",
                        "name": func_name,
                        "line": getattr(node, "lineno", None),
                        "description": f"Use of potentially unsafe dynamic evaluation: {func_name}"
                    })

            # Detect raw SQL formatting patterns
            if isinstance(node, ast.JoinedStr):  # f-string
                # Check if it contains SQL keywords
                fstring_text = "".join(
                    part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str)
                )
                sql_keywords = ("select ", "insert into ", "update ", "delete from ", "where ")
                if any(kw in fstring_text.lower() for kw in sql_keywords):
                    ast_flags.append({
                        "type": "SQL_INJECTION_RISK",
                        "line": getattr(node, "lineno", None),
                        "description": "SQL query dynamically constructed using f-string interpolation instead of parameterized binding."
                    })

        # Index classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                class_start = node.lineno
                class_end = getattr(node, "end_lineno", node.lineno)

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        params = [arg.arg for arg in item.args.args]
                        scopes.append({
                            "type": "method",
                            "class_name": class_name,
                            "function_name": item.name,
                            "start_line": item.lineno,
                            "end_line": getattr(item, "end_lineno", item.lineno),
                            "parameters": params,
                            "docstring": ast.get_docstring(item)
                        })

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [arg.arg for arg in node.args.args]
                scopes.append({
                    "type": "function",
                    "class_name": None,
                    "function_name": node.name,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "parameters": params,
                    "docstring": ast.get_docstring(node)
                })

        return {
            "scopes": scopes,
            "imports": imports,
            "ast_flags": ast_flags
        }

    @staticmethod
    def get_context_for_line(analysis: Dict[str, Any], line_number: int) -> ASTContext:
        """Finds the enclosing function/class and relevant AST flags for a given line number."""
        scopes = analysis.get("scopes", [])
        matched_scope = None

        for scope in scopes:
            if scope["start_line"] <= line_number <= scope["end_line"]:
                matched_scope = scope
                break

        enclosing_func = matched_scope["function_name"] if matched_scope else None
        enclosing_cls = matched_scope["class_name"] if matched_scope else None
        params = matched_scope["parameters"] if matched_scope else []
        doc = matched_scope["docstring"] if matched_scope else None

        # Filter flags on this line
        flags_on_line = [
            f["description"] for f in analysis.get("ast_flags", [])
            if f.get("line") == line_number
        ]

        return ASTContext(
            enclosing_function=enclosing_func,
            enclosing_class=enclosing_cls,
            docstring=doc,
            parameters=params,
            imported_modules=analysis.get("imports", []),
            ast_flags=flags_on_line
        )
