#!/usr/bin/env python3
"""
ChatterFix CMMS Dependency Analyzer
==================================

Comprehensively analyzes Python dependencies to identify:
1. Used dependencies from imports across all Python files
2. Unused dependencies listed in requirements.txt
3. Missing dependencies that are imported but not listed
4. Duplicate or conflicting dependencies
5. Security issues and version conflicts
6. Development vs production dependency classification
"""

import os
import re
import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")


class DependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.imports_found = defaultdict(set)  # module -> files that import it
        self.local_modules = set()
        self.requirements_deps = {}  # package -> version
        self.dev_requirements_deps = {}
        self.ai_service_deps = {}

        # Standard library detection patterns
        self.stdlib_patterns = {
            "os",
            "sys",
            "json",
            "re",
            "time",
            "datetime",
            "logging",
            "pathlib",
            "collections",
            "typing",
            "functools",
            "itertools",
            "asyncio",
            "contextlib",
            "urllib",
            "http",
            "email",
            "base64",
            "hashlib",
            "secrets",
            "uuid",
            "subprocess",
            "threading",
            "multiprocessing",
            "socket",
            "ssl",
        }

        self.stdlib_modules = self._get_stdlib_modules()

        # Known third-party package mappings (import name -> package name)
        self.package_mappings = {
            "google.cloud": "google-cloud-firestore",
            "google.auth": "google-auth",
            "firebase_admin": "firebase-admin",
            "pyrebase": "pyrebase4",
            "cv2": "opencv-python-headless",
            "PIL": "qrcode[pil]",
            "pyzbar": "pyzbar",
            "sklearn": "scikit-learn",
            "jose": "python-jose[cryptography]",
            "dotenv": "python-dotenv",
            "multipart": "python-multipart",
            "slowapi": "slowapi",
            "grpc": "grpcio",
            "grpcio_tools": "grpcio-tools",
            "grpcio_status": "grpcio-status",
            "autogen": "pyautogen",
            "anthropic": "anthropic",
            "openai": "openai",
            "google.generativeai": "google-generativeai",
        }

    def _get_stdlib_modules(self) -> Set[str]:
        """Get standard library modules for the current Python version"""
        # This is a basic approach - could be enhanced with stdlib-list package
        return self.stdlib_patterns

    def find_all_python_files(self) -> List[Path]:
        """Find all Python files in the project, excluding virtual environments"""
        python_files = []

        # Exclude patterns
        exclude_patterns = {
            "__pycache__",
            ".pytest_cache",
            ".venv",
            "venv",
            ".git",
            "node_modules",
            ".mypy_cache",
            ".tox",
            "build",
            "dist",
            "site-packages",
        }

        for root, dirs, files in os.walk(self.project_root):
            # Remove excluded directories from traversal
            dirs[:] = [
                d for d in dirs if not any(pattern in d for pattern in exclude_patterns)
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    python_files.append(file_path)

        return python_files

    def extract_imports_from_file(self, file_path: Path) -> Set[str]:
        """Extract all imports from a Python file using AST parsing"""
        imports = set()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse with AST
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return imports

    def identify_local_modules(self, python_files: List[Path]) -> Set[str]:
        """Identify local project modules"""
        local_modules = set()

        for file_path in python_files:
            # Get relative path from project root
            rel_path = file_path.relative_to(self.project_root)

            # Extract module path
            parts = rel_path.parts[:-1]  # Remove filename
            if parts:
                module_path = ".".join(parts)
                local_modules.add(parts[0])  # Add top-level module

            # Add filename as module (without .py)
            if file_path.stem != "__init__":
                local_modules.add(file_path.stem)

        return local_modules

    def parse_requirements_file(self, req_file: Path) -> Dict[str, str]:
        """Parse requirements.txt file and extract package versions"""
        requirements = {}

        if not req_file.exists():
            return requirements

        try:
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse package name and version
                    # Handle formats: package>=1.0.0, package==1.0.0, package[extras]>=1.0.0
                    match = re.match(
                        r"([a-zA-Z0-9][a-zA-Z0-9._-]*(?:\[[^\]]+\])?)\s*([><=!]+.*)?",
                        line,
                    )
                    if match:
                        package = match.group(1)
                        version = match.group(2) or "any"

                        # Clean package name (remove extras)
                        clean_package = re.sub(r"\[[^\]]+\]", "", package)
                        requirements[clean_package] = version

        except Exception as e:
            print(f"Warning: Could not parse {req_file}: {e}")

        return requirements

    def map_import_to_package(self, import_name: str) -> Optional[str]:
        """Map an import name to its corresponding package name"""

        # Check direct mapping
        if import_name in self.package_mappings:
            return self.package_mappings[import_name]

        # Check for submodule mappings
        for pattern, package in self.package_mappings.items():
            if "." in pattern and import_name.startswith(pattern.split(".")[0]):
                return package

        # Check if it matches any known package directly
        all_packages = (
            set(self.requirements_deps.keys())
            | set(self.dev_requirements_deps.keys())
            | set(self.ai_service_deps.keys())
        )

        # Direct match
        if import_name in all_packages:
            return import_name

        # Check for common patterns
        if import_name.replace("_", "-") in all_packages:
            return import_name.replace("_", "-")

        if import_name.replace("-", "_") in all_packages:
            return import_name.replace("-", "_")

        return None

    def categorize_imports(self, all_imports: Set[str]) -> Dict[str, Set[str]]:
        """Categorize imports into stdlib, local, and third-party"""
        categories = {
            "stdlib": set(),
            "local": set(),
            "third_party": set(),
            "unknown": set(),
        }

        for import_name in all_imports:
            if import_name in self.stdlib_modules:
                categories["stdlib"].add(import_name)
            elif import_name in self.local_modules:
                categories["local"].add(import_name)
            else:
                mapped_package = self.map_import_to_package(import_name)
                if mapped_package:
                    categories["third_party"].add(import_name)
                else:
                    categories["unknown"].add(import_name)

        return categories

    def find_unused_dependencies(self) -> Dict[str, str]:
        """Find dependencies in requirements.txt that are never imported"""
        unused = {}
        all_imports = set()

        # Collect all imports
        for imports in self.imports_found.values():
            all_imports.update(imports)

        # Check each requirement
        for package, version in self.requirements_deps.items():
            package_imported = False

            # Check direct import
            if package in all_imports:
                package_imported = True

            # Check mapped imports
            for import_name in all_imports:
                mapped_package = self.map_import_to_package(import_name)
                if mapped_package == package:
                    package_imported = True
                    break

            # Check variations
            package_variants = {
                package.replace("-", "_"),
                package.replace("_", "-"),
                package.replace("-", ""),
                package.replace("_", ""),
            }

            if any(variant in all_imports for variant in package_variants):
                package_imported = True

            if not package_imported:
                unused[package] = version

        return unused

    def find_missing_dependencies(self) -> Set[str]:
        """Find imports that don't have corresponding dependencies"""
        missing = set()
        all_imports = set()

        # Collect all third-party imports
        for imports in self.imports_found.values():
            all_imports.update(imports)

        # Filter out stdlib and local modules
        third_party_imports = all_imports - self.stdlib_modules - self.local_modules

        # Check if each import has a corresponding requirement
        for import_name in third_party_imports:
            mapped_package = self.map_import_to_package(import_name)

            if not mapped_package:
                missing.add(import_name)
            else:
                # Check if the mapped package exists in any requirements file
                found = (
                    mapped_package in self.requirements_deps
                    or mapped_package in self.dev_requirements_deps
                    or mapped_package in self.ai_service_deps
                )

                if not found:
                    missing.add(import_name)

        return missing

    def check_for_duplicates(self) -> Dict[str, List[str]]:
        """Check for duplicate dependencies across requirements files"""
        duplicates = defaultdict(list)

        all_deps = {}

        # Check main requirements
        for package in self.requirements_deps:
            if package in all_deps:
                duplicates[package].append("requirements.txt")
            all_deps[package] = "requirements.txt"

        # Check dev requirements
        for package in self.dev_requirements_deps:
            if package in all_deps:
                duplicates[package].append("requirements-dev.txt")
                duplicates[package].append(all_deps[package])
            all_deps[package] = "requirements-dev.txt"

        # Check AI service requirements
        for package in self.ai_service_deps:
            if package in all_deps:
                duplicates[package].append("ai-team-service/requirements.txt")
                duplicates[package].append(all_deps[package])
            all_deps[package] = "ai-team-service/requirements.txt"

        # Remove single occurrences
        return {k: list(set(v)) for k, v in duplicates.items() if len(set(v)) > 1}

    def get_file_import_details(self) -> Dict[str, Dict[str, List[str]]]:
        """Get detailed breakdown of which files import which packages"""
        details = defaultdict(lambda: defaultdict(list))

        for file_path, imports in self.imports_found.items():
            rel_path = str(Path(file_path).relative_to(self.project_root))

            for import_name in imports:
                mapped_package = self.map_import_to_package(import_name)
                if mapped_package:
                    details[mapped_package]["files"].append(rel_path)
                    details[mapped_package]["imports"].append(import_name)
                else:
                    details["unmapped"]["files"].append(rel_path)
                    details["unmapped"]["imports"].append(import_name)

        # Deduplicate
        for package in details:
            details[package]["files"] = list(set(details[package]["files"]))
            details[package]["imports"] = list(set(details[package]["imports"]))

        return dict(details)

    def analyze(self) -> Dict:
        """Run complete dependency analysis"""
        print("🔍 Starting comprehensive dependency analysis...")

        # Find all Python files
        python_files = self.find_all_python_files()
        print(f"📁 Found {len(python_files)} Python files")

        # Identify local modules
        self.local_modules = self.identify_local_modules(python_files)
        print(f"📦 Identified {len(self.local_modules)} local modules")

        # Parse requirements files
        self.requirements_deps = self.parse_requirements_file(
            self.project_root / "requirements.txt"
        )
        self.dev_requirements_deps = self.parse_requirements_file(
            self.project_root / "requirements-dev.txt"
        )
        self.ai_service_deps = self.parse_requirements_file(
            self.project_root / "ai-team-service" / "requirements.txt"
        )

        print(f"📋 Loaded {len(self.requirements_deps)} main dependencies")
        print(f"📋 Loaded {len(self.dev_requirements_deps)} dev dependencies")
        print(f"📋 Loaded {len(self.ai_service_deps)} AI service dependencies")

        # Extract imports from all files
        for file_path in python_files:
            imports = self.extract_imports_from_file(file_path)
            self.imports_found[str(file_path)] = imports

        # Collect all unique imports
        all_imports = set()
        for imports in self.imports_found.values():
            all_imports.update(imports)

        print(f"🔍 Found {len(all_imports)} unique imports")

        # Categorize imports
        import_categories = self.categorize_imports(all_imports)

        # Find issues
        unused_deps = self.find_unused_dependencies()
        missing_deps = self.find_missing_dependencies()
        duplicate_deps = self.check_for_duplicates()
        file_details = self.get_file_import_details()

        return {
            "summary": {
                "total_python_files": len(python_files),
                "total_imports": len(all_imports),
                "stdlib_imports": len(import_categories["stdlib"]),
                "local_imports": len(import_categories["local"]),
                "third_party_imports": len(import_categories["third_party"]),
                "unknown_imports": len(import_categories["unknown"]),
                "total_dependencies": len(self.requirements_deps)
                + len(self.dev_requirements_deps)
                + len(self.ai_service_deps),
                "unused_dependencies": len(unused_deps),
                "missing_dependencies": len(missing_deps),
                "duplicate_dependencies": len(duplicate_deps),
            },
            "import_categories": {
                k: sorted(list(v)) for k, v in import_categories.items()
            },
            "dependencies": {
                "requirements.txt": self.requirements_deps,
                "requirements-dev.txt": self.dev_requirements_deps,
                "ai-team-service/requirements.txt": self.ai_service_deps,
            },
            "unused_dependencies": unused_deps,
            "missing_dependencies": sorted(list(missing_deps)),
            "duplicate_dependencies": duplicate_deps,
            "file_import_details": file_details,
            "recommendations": self._generate_recommendations(
                unused_deps, missing_deps, duplicate_deps, import_categories
            ),
        }

    def _generate_recommendations(
        self,
        unused_deps: Dict,
        missing_deps: Set,
        duplicate_deps: Dict,
        import_categories: Dict,
    ) -> Dict:
        """Generate recommendations for dependency optimization"""
        recommendations = {
            "security": [],
            "cleanup": [],
            "additions": [],
            "organization": [],
        }

        # Cleanup recommendations
        if unused_deps:
            recommendations["cleanup"].append(
                f"Remove {len(unused_deps)} unused dependencies to reduce bundle size"
            )
            for dep in list(unused_deps.keys())[:5]:  # Show first 5
                recommendations["cleanup"].append(f"  - {dep} (never imported)")

        # Addition recommendations
        if missing_deps:
            recommendations["additions"].append(
                f"Add {len(missing_deps)} missing dependencies"
            )
            for dep in list(missing_deps)[:5]:  # Show first 5
                recommendations["additions"].append(
                    f"  - {dep} (imported but not in requirements)"
                )

        # Organization recommendations
        if duplicate_deps:
            recommendations["organization"].append(
                f"Resolve {len(duplicate_deps)} duplicate dependencies"
            )
            for dep, files in duplicate_deps.items():
                recommendations["organization"].append(
                    f"  - {dep} in {', '.join(files)}"
                )

        # Security recommendations
        security_packages = ["cryptography", "requests", "urllib3", "pillow"]
        for pkg in security_packages:
            if pkg in self.requirements_deps:
                recommendations["security"].append(
                    f"Monitor {pkg} for security updates"
                )

        return recommendations


def main():
    """Main execution function"""
    project_root = "/Users/fredtaylor/ChatterFix"

    if not os.path.exists(project_root):
        print(f"❌ Project root not found: {project_root}")
        return

    analyzer = DependencyAnalyzer(project_root)
    results = analyzer.analyze()

    # Save results to JSON file
    output_file = os.path.join(project_root, "dependency_analysis_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✅ Analysis complete! Results saved to {output_file}")

    # Print summary
    print("\n📊 DEPENDENCY ANALYSIS SUMMARY")
    print("=" * 50)

    summary = results["summary"]
    print(f"📁 Total Python files: {summary['total_python_files']}")
    print(f"🔍 Total imports found: {summary['total_imports']}")
    print(f"📦 Dependencies declared: {summary['total_dependencies']}")
    print(f"❌ Unused dependencies: {summary['unused_dependencies']}")
    print(f"➕ Missing dependencies: {summary['missing_dependencies']}")
    print(f"🔄 Duplicate dependencies: {summary['duplicate_dependencies']}")

    # Show critical issues
    if results["unused_dependencies"]:
        print(f"\n🗑️  UNUSED DEPENDENCIES ({len(results['unused_dependencies'])})")
        for dep, version in list(results["unused_dependencies"].items())[:10]:
            print(f"   - {dep} {version}")

    if results["missing_dependencies"]:
        print(f"\n❗ MISSING DEPENDENCIES ({len(results['missing_dependencies'])})")
        for dep in list(results["missing_dependencies"])[:10]:
            print(f"   - {dep}")

    if results["duplicate_dependencies"]:
        print(f"\n🔄 DUPLICATE DEPENDENCIES ({len(results['duplicate_dependencies'])})")
        for dep, files in results["duplicate_dependencies"].items():
            print(f"   - {dep} in {', '.join(files)}")

    print(f"\n📄 Full analysis report: {output_file}")


if __name__ == "__main__":
    main()
