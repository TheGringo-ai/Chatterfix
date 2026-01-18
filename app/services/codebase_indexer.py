"""
Codebase Indexer - Builds a complete map of the ChatterFix codebase
for the AI team to understand and navigate.

Part of the Self-Orchestrating AI Team system.
"""

import os
import ast
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Information about a function/method."""
    name: str
    file_path: str
    line_number: int
    docstring: Optional[str]
    parameters: List[str]
    is_async: bool
    decorators: List[str]


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    file_path: str
    line_number: int
    docstring: Optional[str]
    methods: List[str]
    base_classes: List[str]


@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    relative_path: str
    size_bytes: int
    line_count: int
    imports: List[str]
    functions: List[str]
    classes: List[str]
    summary: str
    last_modified: str
    content_hash: str


class CodebaseIndexer:
    """
    Indexes the entire codebase to provide AI team with full context.

    Features:
    - Extracts all functions, classes, and their signatures
    - Maps file dependencies
    - Creates searchable summaries
    - Caches for fast lookup
    """

    IGNORED_DIRS = {
        'node_modules', '__pycache__', '.git', '.venv', 'venv',
        'build', 'dist', '.next', 'coverage', '.pytest_cache'
    }

    SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx'}

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.index: Dict[str, FileInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        self.classes: Dict[str, ClassInfo] = {}
        self.file_map: Dict[str, str] = {}  # short name -> full path
        self._last_indexed: Optional[datetime] = None

    def build_index(self) -> Dict[str, Any]:
        """Build complete codebase index."""
        logger.info(f"🔍 Indexing codebase at {self.project_root}...")

        start_time = datetime.now()
        file_count = 0

        for file_path in self._find_code_files():
            try:
                file_info = self._index_file(file_path)
                if file_info:
                    self.index[file_info.relative_path] = file_info
                    self.file_map[file_path.name] = file_info.relative_path
                    file_count += 1
            except Exception as e:
                logger.warning(f"Failed to index {file_path}: {e}")

        self._last_indexed = datetime.now()
        elapsed = (self._last_indexed - start_time).total_seconds()

        summary = self._generate_summary()

        logger.info(f"✅ Indexed {file_count} files in {elapsed:.2f}s")
        logger.info(f"   Functions: {len(self.functions)}")
        logger.info(f"   Classes: {len(self.classes)}")

        return summary

    def _find_code_files(self):
        """Find all code files in the project."""
        for root, dirs, files in os.walk(self.project_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in self.SUPPORTED_EXTENSIONS:
                    yield file_path

    def _index_file(self, file_path: Path) -> Optional[FileInfo]:
        """Index a single file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

        relative_path = str(file_path.relative_to(self.project_root))

        # Parse Python files for detailed info
        functions = []
        classes = []
        imports = []

        if file_path.suffix == '.py':
            try:
                tree = ast.parse(content)
                functions, classes, imports = self._parse_python_ast(tree, relative_path)
            except SyntaxError:
                pass

        # Generate content hash for change detection (not used for security)
        content_hash = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:8]

        # Generate summary
        summary = self._generate_file_summary(file_path.name, functions, classes)

        return FileInfo(
            path=str(file_path),
            relative_path=relative_path,
            size_bytes=len(content),
            line_count=content.count('\n') + 1,
            imports=imports,
            functions=functions,
            classes=classes,
            summary=summary,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            content_hash=content_hash
        )

    def _parse_python_ast(self, tree: ast.AST, file_path: str):
        """Parse Python AST for functions, classes, imports."""
        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = FunctionInfo(
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=ast.get_docstring(node),
                    parameters=[arg.arg for arg in node.args.args],
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list]
                )
                self.functions[f"{file_path}:{node.name}"] = func_info
                functions.append(node.name)

            elif isinstance(node, ast.ClassDef):
                class_info = ClassInfo(
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=ast.get_docstring(node),
                    methods=[n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                    base_classes=[self._get_base_name(b) for b in node.bases]
                )
                self.classes[f"{file_path}:{node.name}"] = class_info
                classes.append(node.name)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return functions, classes, imports

    def _get_decorator_name(self, node) -> str:
        """Get decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "unknown"

    def _get_base_name(self, node) -> str:
        """Get base class name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return "unknown"

    def _generate_file_summary(self, filename: str, functions: List[str], classes: List[str]) -> str:
        """Generate a brief summary of what a file does."""
        parts = []
        if classes:
            parts.append(f"Classes: {', '.join(classes[:3])}")
        if functions:
            parts.append(f"Functions: {', '.join(functions[:5])}")
        return "; ".join(parts) if parts else "No public API"

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate overall codebase summary for AI context."""
        # Group files by directory
        by_dir = {}
        for path, info in self.index.items():
            dir_name = str(Path(path).parent)
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(info)

        return {
            "project_root": str(self.project_root),
            "indexed_at": self._last_indexed.isoformat() if self._last_indexed else None,
            "total_files": len(self.index),
            "total_functions": len(self.functions),
            "total_classes": len(self.classes),
            "directories": {
                dir_name: {
                    "files": len(files),
                    "file_names": [Path(f.relative_path).name for f in files]
                }
                for dir_name, files in by_dir.items()
            },
            "key_files": self._identify_key_files()
        }

    def _identify_key_files(self) -> List[Dict[str, str]]:
        """Identify the most important files in the codebase."""
        key_patterns = [
            ('main.py', 'Application entry point'),
            ('auth.py', 'Authentication system'),
            ('work_orders.py', 'Work order management'),
            ('assets.py', 'Asset management'),
            ('ai_team_intelligence.py', 'AI team coordination'),
            ('firestore_db.py', 'Database operations'),
        ]

        key_files = []
        for pattern, description in key_patterns:
            for path in self.file_map:
                if pattern in path:
                    key_files.append({
                        "file": self.file_map.get(path, path),
                        "description": description
                    })
                    break

        return key_files

    def get_context_for_query(self, query: str) -> str:
        """Get relevant codebase context for a query."""
        # Simple keyword matching for now
        query_lower = query.lower()
        relevant_files = []

        keywords = {
            'work order': ['work_orders.py', 'work_order'],
            'asset': ['assets.py', 'asset'],
            'auth': ['auth.py', 'login', 'session'],
            'inventory': ['inventory.py', 'parts'],
            'ai': ['ai_team', 'ai_service', 'gemini'],
            'dashboard': ['dashboard.py'],
            'training': ['training.py', 'linesmart'],
        }

        for keyword, file_patterns in keywords.items():
            if keyword in query_lower:
                for path, info in self.index.items():
                    if any(p in path.lower() for p in file_patterns):
                        relevant_files.append(info)

        if not relevant_files:
            # Return key files as default context
            relevant_files = list(self.index.values())[:10]

        context_parts = ["## Relevant Codebase Files\n"]
        for file_info in relevant_files[:10]:
            context_parts.append(f"- `{file_info.relative_path}`: {file_info.summary}")

        return "\n".join(context_parts)

    def find_function(self, name: str) -> Optional[FunctionInfo]:
        """Find a function by name."""
        for key, func in self.functions.items():
            if func.name == name:
                return func
        return None

    def find_class(self, name: str) -> Optional[ClassInfo]:
        """Find a class by name."""
        for key, cls in self.classes.items():
            if cls.name == name:
                return cls
        return None

    def to_json(self) -> str:
        """Export index to JSON."""
        return json.dumps({
            "summary": self._generate_summary(),
            "files": {k: asdict(v) for k, v in self.index.items()}
        }, indent=2, default=str)


# Singleton instance
_indexer: Optional[CodebaseIndexer] = None


def get_codebase_indexer() -> CodebaseIndexer:
    """Get or create the codebase indexer."""
    global _indexer
    if _indexer is None:
        _indexer = CodebaseIndexer()
        _indexer.build_index()
    return _indexer
