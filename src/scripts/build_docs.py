import os
import shutil
import subprocess
from pathlib import Path

def build_docs():
    """Build documentation using Sphinx."""
    docs_dir = Path(__file__).parent.parent / 'docs'

    # Install doc requirements
    subprocess.check_call(['pip', 'install', 'sphinx', 'sphinx-rtd-theme'])

    # Create API documentation
    subprocess.check_call(['sphinx-apidoc', '-o', str(docs_dir / 'api'), '../src/algame'])

    # Build HTML documentation
    subprocess.check_call(['sphinx-build', '-b', 'html', str(docs_dir), str(docs_dir / '_build' / 'html')])

    print("\nDocumentation built successfully!")
    print(f"Open {docs_dir}/_build/html/index.html to view")

if __name__ == "__main__":
    build_docs()
