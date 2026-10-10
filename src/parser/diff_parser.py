"""
Git Unified Diff Parser.
Parses unified diff outputs into structured FileDiff, DiffHunk, and DiffLine instances.
"""

import re
from typing import List, Optional
from ..schemas.models import FileDiff, DiffHunk, DiffLine

LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".sql": "sql",
    ".java": "java",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sh": "bash",
}

HUNK_HEADER_REGEX = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@(.*)")

def detect_language(file_path: str) -> str:
    """Detects programming language from file extension."""
    for ext, lang in LANGUAGE_EXTENSIONS.items():
        if file_path.endswith(ext):
            return lang
    return "unknown"

class DiffParser:
    """Parses standard unified git diff format into structured FileDiff models."""

    @staticmethod
    def parse_patch(patch_text: str) -> List[FileDiff]:
        """
        Parses a full multi-file unified git diff string.
        If raw source code without git headers is provided, automatically normalizes it into a synthetic diff.
        """
        if not patch_text or not patch_text.strip():
            return []

        # Auto-detect if input is raw source code rather than a unified diff
        clean_text = patch_text.strip()
        if not re.search(r"^(?:diff --git|--- |\+\+\+ |@@ )", clean_text, re.MULTILINE):
            lines = clean_text.splitlines()
            synthetic_header = [
                "diff --git a/custom_input.py b/custom_input.py",
                "--- /dev/null",
                "+++ b/custom_input.py",
                f"@@ -0,0 +1,{max(1, len(lines))} @@",
            ]
            synthetic_body = ["+" + l for l in lines]
            patch_text = "\n".join(synthetic_header + synthetic_body)

        files: List[FileDiff] = []
        raw_file_chunks = re.split(r"(?=diff --git )", patch_text)

        for chunk in raw_file_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            parsed_file = DiffParser._parse_single_file_diff(chunk)
            if parsed_file:
                files.append(parsed_file)

        return files

    @staticmethod
    def _parse_single_file_diff(chunk: str) -> Optional[FileDiff]:
        lines = chunk.splitlines()
        if not lines:
            return None

        old_path: Optional[str] = None
        new_path: Optional[str] = None
        is_new = False
        is_deleted = False
        is_binary = "Binary files" in chunk

        # Parse header lines
        diff_git_match = re.match(r"^diff --git a/(.*?) b/(.*?)$", lines[0])
        if diff_git_match:
            old_path = diff_git_match.group(1)
            new_path = diff_git_match.group(2)

        hunk_start_idx = 0
        for idx, line in enumerate(lines):
            if line.startswith("--- "):
                p = line[4:].strip()
                if p == "/dev/null":
                    is_new = True
                elif p.startswith("a/"):
                    old_path = p[2:]
            elif line.startswith("+++ "):
                p = line[4:].strip()
                if p == "/dev/null":
                    is_deleted = True
                elif p.startswith("b/"):
                    new_path = p[2:]
            elif line.startswith("new file mode"):
                is_new = True
            elif line.startswith("deleted file mode"):
                is_deleted = True
            elif line.startswith("@@ "):
                hunk_start_idx = idx
                break

        if not new_path and not old_path:
            # Fallback if diff format was abbreviated
            return None

        target_path = new_path or old_path or "unknown"
        language = detect_language(target_path)

        # Parse hunks
        hunks: List[DiffHunk] = []
        current_hunk: Optional[DiffHunk] = None
        old_lineno = 0
        new_lineno = 0

        for line in lines[hunk_start_idx:]:
            if line.startswith("@@ "):
                m = HUNK_HEADER_REGEX.match(line)
                if m:
                    old_start = int(m.group(1))
                    old_lines = int(m.group(2)) if m.group(2) else 1
                    new_start = int(m.group(3))
                    new_lines = int(m.group(4)) if m.group(4) else 1
                    header = m.group(5).strip()

                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_lines=old_lines,
                        new_start=new_start,
                        new_lines=new_lines,
                        header=header,
                        lines=[]
                    )
                    hunks.append(current_hunk)
                    old_lineno = old_start
                    new_lineno = new_start
                continue

            if current_hunk is None:
                continue

            if line.startswith("+"):
                diff_line = DiffLine(
                    line_type="add",
                    old_line_number=None,
                    new_line_number=new_lineno,
                    content=line[1:]
                )
                current_hunk.lines.append(diff_line)
                new_lineno += 1
            elif line.startswith("-"):
                diff_line = DiffLine(
                    line_type="del",
                    old_line_number=old_lineno,
                    new_line_number=None,
                    content=line[1:]
                )
                current_hunk.lines.append(diff_line)
                old_lineno += 1
            elif line.startswith(" "):
                diff_line = DiffLine(
                    line_type="context",
                    old_line_number=old_lineno,
                    new_line_number=new_lineno,
                    content=line[1:]
                )
                current_hunk.lines.append(diff_line)
                old_lineno += 1
                new_lineno += 1
            elif line.startswith("\\ No newline"):
                continue

        return FileDiff(
            old_path=old_path,
            new_path=target_path,
            is_new=is_new,
            is_deleted=is_deleted,
            is_binary=is_binary,
            language=language,
            hunks=hunks,
            raw_diff=chunk
        )
