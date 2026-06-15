#!/usr/bin/env python3
"""Generate a Mermaid module dependency graph for local Python files."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "site-packages",
    "node_modules",
    "build",
    "dist",
}


@dataclass(frozen=True)
class ModuleFile:
    path: Path
    module: str


def should_skip_dir(dir_name: str) -> bool:
    if dir_name in IGNORED_DIRS:
        return True
    return dir_name.endswith(".egg-info")


def module_name_for_file(root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(root)
    parts = list(rel.parts)

    if parts[-1] == "__init__.py":
        return ".".join(parts[:-1])

    parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def collect_local_modules(root: Path) -> tuple[dict[str, ModuleFile], set[str]]:
    modules: dict[str, ModuleFile] = {}
    package_names: set[str] = set()

    for path in root.rglob("*.py"):
        if any(should_skip_dir(part) for part in path.relative_to(root).parts[:-1]):
            continue

        module = module_name_for_file(root, path)
        if not module:
            continue

        modules[module] = ModuleFile(path=path, module=module)

        parts = module.split(".")
        for i in range(1, len(parts) + 1):
            package_names.add(".".join(parts[:i]))

    return modules, package_names


def parse_file_imports(path: Path) -> list[ast.stmt]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    return [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]


def resolve_relative_base(
    current_module: str, level: int, module: str | None, is_package: bool
) -> str:
    if is_package:
        package_parts = current_module.split(".")
    else:
        package_parts = current_module.split(".")[:-1]

    if level > 0:
        trim = level - 1
        if trim > len(package_parts):
            base_parts: list[str] = []
        else:
            base_parts = package_parts[: len(package_parts) - trim]
    else:
        base_parts = []

    if module:
        base_parts.extend(module.split("."))

    return ".".join(part for part in base_parts if part)


def pick_local_target(candidate: str, local_symbols: set[str]) -> str | None:
    if not candidate:
        return None

    if candidate in local_symbols:
        return candidate

    parts = candidate.split(".")
    for i in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:i])
        if prefix in local_symbols:
            return prefix

    return None


def module_dependencies(
    importer: str,
    nodes: list[ast.stmt],
    local_modules: set[str],
    local_symbols: set[str],
    is_package: bool,
) -> set[str]:
    deps: set[str] = set()

    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(" as ", 1)[0].strip()
                target = pick_local_target(name, local_symbols)
                if target and target != importer and target in local_modules:
                    deps.add(target)

        elif isinstance(node, ast.ImportFrom):
            base = resolve_relative_base(importer, node.level, node.module, is_package)

            for alias in node.names:
                if alias.name == "*":
                    target = pick_local_target(base, local_symbols)
                    if target and target != importer and target in local_modules:
                        deps.add(target)
                    continue

                qualified = f"{base}.{alias.name}" if base else alias.name

                target = pick_local_target(qualified, local_symbols)
                if target is None:
                    target = pick_local_target(base, local_symbols)

                if target and target != importer and target in local_modules:
                    deps.add(target)

    return deps


def sanitize_node_id(module_name: str) -> str:
    return "m_" + module_name.replace(".", "_").replace("-", "_")


def mermaid_graph(deps: dict[str, set[str]]) -> str:
    lines = ["graph TD"]

    all_nodes = set(deps)
    for targets in deps.values():
        all_nodes.update(targets)

    for module in sorted(all_nodes):
        lines.append(f'    {sanitize_node_id(module)}["{module}"]')

    edges: list[tuple[str, str]] = []
    for src, targets in deps.items():
        for dst in sorted(targets):
            edges.append((src, dst))

    for src, dst in sorted(edges):
        lines.append(f"    {sanitize_node_id(src)} --> {sanitize_node_id(dst)}")

    return "\n".join(lines) + "\n"


def build_dependency_map(root: Path) -> dict[str, set[str]]:
    modules, package_names = collect_local_modules(root)
    local_modules = set(modules)
    local_symbols = local_modules | package_names
    deps: dict[str, set[str]] = {module: set() for module in local_modules}

    for module, info in modules.items():
        try:
            nodes = parse_file_imports(info.path)
        except (SyntaxError, UnicodeDecodeError):
            # Skip files that cannot be parsed as Python source.
            continue

        deps[module] = module_dependencies(
            module,
            nodes,
            local_modules,
            local_symbols,
            is_package=info.path.name == "__init__.py",
        )

    return deps


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid module dependency graph for local Python imports."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root to scan (default: current directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dependency_graph.mmd"),
        help="Output Mermaid file path (default: dependency_graph.mmd).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    dependency_map = build_dependency_map(root)
    content = mermaid_graph(dependency_map)

    output_path = args.output
    if not output_path.is_absolute():
        output_path = root / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    edge_count = sum(len(v) for v in dependency_map.values())
    print(f"Wrote Mermaid dependency graph to {output_path}")
    print(f"Modules: {len(dependency_map)}, Edges: {edge_count}")


if __name__ == "__main__":
    main()
