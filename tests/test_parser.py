"""
Unit tests for Git Diff Parser and AST Analyzer.
"""

import unittest
from src.parser.diff_parser import DiffParser, detect_language
from src.parser.ast_analyzer import PythonASTAnalyzer

SAMPLE_DIFF = """diff --git a/app/routes/users.py b/app/routes/users.py
index 1029384..5647382 100644
--- a/app/routes/users.py
+++ b/app/routes/users.py
@@ -10,4 +10,6 @@ def get_user():
-    return db.query()
+    # added line
+    query = f"SELECT * FROM users WHERE id = '{user_id}'"
+    return db.execute(query)
"""

class TestDiffParser(unittest.TestCase):
    def test_detect_language(self):
        self.assertEqual(detect_language("src/main.py"), "python")
        self.assertEqual(detect_language("frontend/App.tsx"), "typescript")
        self.assertEqual(detect_language("db/schema.sql"), "sql")
        self.assertEqual(detect_language("unknown.xyz"), "unknown")

    def test_parse_patch(self):
        files = DiffParser.parse_patch(SAMPLE_DIFF)
        self.assertEqual(len(files), 1)
        file_diff = files[0]
        self.assertEqual(file_diff.new_path, "app/routes/users.py")
        self.assertEqual(file_diff.language, "python")
        self.assertEqual(len(file_diff.hunks), 1)

        hunk = file_diff.hunks[0]
        self.assertEqual(hunk.new_start, 10)
        added_lines = [l for l in hunk.lines if l.line_type == "add"]
        self.assertEqual(len(added_lines), 3)
        self.assertEqual(added_lines[0].new_line_number, 10)
        self.assertEqual(added_lines[1].new_line_number, 11)

class TestASTAnalyzer(unittest.TestCase):
    def test_analyze_python_ast(self):
        code = '''
def fetch_user_data(user_id):
    """Docstring for fetch."""
    query = f"SELECT * FROM users WHERE id = {user_id}"
    eval("2 + 2")
    return query
'''
        analysis = PythonASTAnalyzer.analyze_source(code)
        self.assertIn("scopes", analysis)
        self.assertEqual(len(analysis["scopes"]), 1)
        self.assertEqual(analysis["scopes"][0]["function_name"], "fetch_user_data")
        self.assertEqual(analysis["scopes"][0]["parameters"], ["user_id"])

        # Check AST flags
        flag_types = [f["type"] for f in analysis["ast_flags"]]
        self.assertIn("SQL_INJECTION_RISK", flag_types)
        self.assertIn("DANGEROUS_CALL", flag_types)

if __name__ == "__main__":
    unittest.main()
