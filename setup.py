"""Fallback setup.py for older pip versions (pip < 23)."""
from setuptools import setup, find_packages

setup(
    name="vault-graph",
    version="0.5.0",
    packages=find_packages(),
    install_requires=["networkx>=3.0", "matplotlib>=3.6"],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "vault-graph=vault_graph.main:main",
        ],
    },
    author="Bian Vigano",
    description="Turn Vault .md files into an interactive D3.js knowledge graph",
    license="MIT",
    keywords="knowledge-graph vault markdown d3 wiki-links",
)
