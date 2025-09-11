#!/usr/bin/env python3
"""
Comprehensive dependency listing tool for AI Foundry Lab project.

This script provides multiple ways to view and analyze project dependencies:
1. Direct dependencies from requirements.txt
2. All installed packages with versions
3. Import analysis of Python files
4. Dependency tree view
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse


def read_requirements_txt() -> List[str]:
    """Read and parse requirements.txt file."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        return []
    
    with open(requirements_path, 'r') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
        return requirements


def get_installed_packages() -> Dict[str, str]:
    """Get all installed packages with their versions."""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, check=True)
        packages = {}
        lines = result.stdout.strip().split('\n')[2:]  # Skip header lines
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                packages[parts[0]] = parts[1]
        return packages
    except subprocess.CalledProcessError:
        return {}


def analyze_imports() -> Set[str]:
    """Analyze Python files to find imported modules."""
    imports = set()
    python_files = list(Path(__file__).parent.glob("*.py"))
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find import statements
            import_patterns = [
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import'
            ]
            
            for line in content.split('\n'):
                line = line.strip()
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        module = match.group(1).split('.')[0]  # Get top-level module
                        imports.add(module)
        except Exception as e:
            print(f"Warning: Could not analyze {py_file}: {e}")
    
    return imports


def categorize_dependencies(requirements: List[str], installed: Dict[str, str], 
                          imports: Set[str]) -> Dict[str, List[Tuple[str, str]]]:
    """Categorize dependencies into different groups."""
    categories = {
        'direct': [],           # From requirements.txt
        'azure': [],           # Azure-related packages
        'streamlit': [],       # Streamlit and related
        'data_science': [],    # Data science packages
        'monitoring': [],      # Telemetry and monitoring
        'development': [],     # Development tools
        'other': []           # Other packages
    }
    
    # Process direct requirements
    for req in requirements:
        # Parse requirement (handle version specifiers and extras like [prompts])
        package_name = re.split(r'[<>=!]', req)[0]
        if '[' in package_name:
            package_name = package_name.split('[')[0]
        version = installed.get(package_name, 'Not installed')
        categories['direct'].append((package_name, version))
    
    # Categorize all installed packages
    for package, version in installed.items():
        package_lower = package.lower()
        
        if package_lower.startswith('azure-'):
            categories['azure'].append((package, version))
        elif package_lower.startswith('streamlit') or package_lower.startswith('st-'):
            categories['streamlit'].append((package, version))
        elif package_lower in ['pandas', 'numpy', 'matplotlib', 'plotly', 'pyarrow']:
            categories['data_science'].append((package, version))
        elif package_lower.startswith('opentelemetry') or 'telemetry' in package_lower or 'monitor' in package_lower:
            categories['monitoring'].append((package, version))
        elif package_lower in ['pip', 'setuptools', 'wheel', 'build', 'pytest', 'black', 'flake8']:
            categories['development'].append((package, version))
        elif package not in [req.split('[')[0].split('<')[0].split('>')[0].split('=')[0].split('!')[0] for req in requirements]:
            categories['other'].append((package, version))
    
    return categories


def print_dependencies(show_all: bool = False, show_imports: bool = False, 
                      show_tree: bool = False, format_type: str = 'table'):
    """Print dependency information in various formats."""
    print("=" * 80)
    print("AI FOUNDRY LAB - DEPENDENCY ANALYSIS")
    print("=" * 80)
    
    # Get data
    requirements = read_requirements_txt()
    installed = get_installed_packages()
    imports = analyze_imports() if show_imports else set()
    
    # Direct dependencies from requirements.txt
    print(f"\n📋 DIRECT DEPENDENCIES ({len(requirements)} packages)")
    print("-" * 50)
    if format_type == 'table':
        print(f"{'Package':<30} {'Version':<15} {'Status'}")
        print("-" * 50)
        for req in requirements:
            package_name = re.split(r'[<>=!]', req)[0]
            if '[' in package_name:
                package_name = package_name.split('[')[0]
            version = installed.get(package_name, 'Not installed')
            status = "✅ Installed" if package_name in installed else "❌ Missing"
            print(f"{package_name:<30} {version:<15} {status}")
    else:  # list format
        for req in requirements:
            print(f"  • {req}")
    
    if show_all:
        categories = categorize_dependencies(requirements, installed, imports)
        
        # Azure packages
        if categories['azure']:
            print(f"\n☁️  AZURE PACKAGES ({len(categories['azure'])} packages)")
            print("-" * 50)
            for package, version in sorted(categories['azure']):
                print(f"  • {package:<40} {version}")
        
        # Streamlit packages
        if categories['streamlit']:
            print(f"\n🎨 STREAMLIT PACKAGES ({len(categories['streamlit'])} packages)")
            print("-" * 50)
            for package, version in sorted(categories['streamlit']):
                print(f"  • {package:<40} {version}")
        
        # Data science packages
        if categories['data_science']:
            print(f"\n📊 DATA SCIENCE PACKAGES ({len(categories['data_science'])} packages)")
            print("-" * 50)
            for package, version in sorted(categories['data_science']):
                print(f"  • {package:<40} {version}")
        
        # Monitoring packages
        if categories['monitoring']:
            print(f"\n📡 MONITORING & TELEMETRY ({len(categories['monitoring'])} packages)")
            print("-" * 50)
            for package, version in sorted(categories['monitoring']):
                print(f"  • {package:<40} {version}")
        
        # All packages summary
        print(f"\n📦 SUMMARY")
        print("-" * 50)
        print(f"  • Total installed packages: {len(installed)}")
        print(f"  • Direct dependencies: {len(requirements)}")
        print(f"  • Azure packages: {len(categories['azure'])}")
        print(f"  • Streamlit packages: {len(categories['streamlit'])}")
        print(f"  • Data science packages: {len(categories['data_science'])}")
        print(f"  • Monitoring packages: {len(categories['monitoring'])}")
        print(f"  • Other packages: {len(categories['other'])}")
    
    if show_imports:
        print(f"\n🔍 IMPORT ANALYSIS ({len(imports)} unique top-level imports)")
        print("-" * 50)
        builtin_modules = {'os', 'sys', 'pathlib', 'logging', 'argparse', 'typing', 're'}
        external_imports = imports - builtin_modules
        
        print("Built-in modules:")
        for module in sorted(builtin_modules & imports):
            print(f"  • {module}")
        
        print("\nExternal packages:")
        for module in sorted(external_imports):
            status = "✅" if module in installed or any(module in pkg for pkg in installed) else "❓"
            print(f"  • {module:<30} {status}")
    
    if show_tree:
        print(f"\n🌳 DEPENDENCY TREE")
        print("-" * 50)
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show'] + 
                                  [req.split('[')[0].split('<')[0].split('>')[0].split('=')[0].split('!')[0] 
                                   for req in requirements[:5]], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print("Could not generate dependency tree. Install 'pipdeptree' for better tree view:")
                print("  pip install pipdeptree")
                print("  pipdeptree")
        except Exception as e:
            print(f"Error generating dependency tree: {e}")


def export_dependencies(format_type: str = 'txt') -> str:
    """Export dependencies to a file."""
    requirements = read_requirements_txt()
    installed = get_installed_packages()
    
    if format_type == 'txt':
        # Create a comprehensive requirements file
        output_path = Path(__file__).parent / "all_dependencies.txt"
        with open(output_path, 'w') as f:
            f.write("# AI Foundry Lab - Complete Dependency List\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            f.write("# Direct dependencies from requirements.txt:\n")
            for req in requirements:
                f.write(f"{req}\n")
            
            f.write(f"\n# All installed packages ({len(installed)} total):\n")
            for package, version in sorted(installed.items()):
                f.write(f"# {package}=={version}\n")
        
        return str(output_path)
    
    return ""


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="List and analyze dependencies for AI Foundry Lab project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python list_dependencies.py                    # Show direct dependencies
  python list_dependencies.py --all             # Show all packages
  python list_dependencies.py --imports         # Include import analysis  
  python list_dependencies.py --all --imports   # Complete analysis
  python list_dependencies.py --export          # Export to file
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Show all installed packages categorized')
    parser.add_argument('--imports', action='store_true',
                       help='Analyze import statements in Python files')
    parser.add_argument('--tree', action='store_true',
                       help='Show dependency tree')
    parser.add_argument('--export', action='store_true',
                       help='Export dependencies to file')
    parser.add_argument('--format', choices=['table', 'list'], default='table',
                       help='Output format')
    
    args = parser.parse_args()
    
    if args.export:
        output_file = export_dependencies()
        print(f"Dependencies exported to: {output_file}")
    else:
        print_dependencies(
            show_all=args.all,
            show_imports=args.imports,
            show_tree=args.tree,
            format_type=args.format
        )


if __name__ == "__main__":
    main()