#!/usr/bin/env python
"""Setup script for lancedb-cli."""

from setuptools import setup, find_packages

# Read the README for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lancedb-cli",
    version="0.1.0",
    author="Davide Dal Farra",
    author_email="davide@codref.org",
    description="A minimal command line application for managing LanceDB databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codref/lancedb-cli",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "lancedb>=0.1.0",
        "duckdb>=0.5.0",
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
        "prompt-toolkit>=3.0.0",
        "pygments>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "isort>=5.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lsql=lancedb_cli.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Utilities",
    ],
    keywords="lancedb cli database duckdb",
    project_urls={
        "Bug Tracker": "https://github.com/codref/lancedb-cli/issues",
        "Documentation": "https://github.com/codref/lancedb-cli#readme",
        "Source Code": "https://github.com/codref/lancedb-cli",
    },
)
