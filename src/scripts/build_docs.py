from pathlib import Path
import subprocess
import os

def build_docs():
    """Build documentation using Sphinx."""
    # Get project root directory (where setup.py is)
    root_dir = Path(__file__).parent.parent.parent

    # Set up paths
    docs_dir = root_dir / 'docs'
    source_dir = root_dir / 'src' / 'algame'

    # Create required directories
    docs_dir.mkdir(exist_ok=True)
    api_dir = docs_dir / 'api'
    api_dir.mkdir(exist_ok=True)

    # Generate API documentation
    subprocess.check_call([
        'sphinx-apidoc',
        '-o', str(api_dir),  # Output directory
        str(source_dir),     # Source code directory
        '--separate',        # Create separate pages for modules
        '--force'           # Overwrite existing files
    ])

    # Build HTML documentation
    subprocess.check_call([
        'sphinx-build',
        '-b', 'html',       # Builder to use
        str(docs_dir),      # Source directory
        str(docs_dir / '_build' / 'html')  # Output directory
    ])

if __name__ == '__main__':
    build_docs()
