from setuptools import setup, find_packages

setup(
    name="semantic-memory-search",
    version="0.1.0",
    description="Local semantic search for AI agent memory files",
    author="Computer",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "sentencepiece",
        "safetensors",
        "numpy",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "semantic-memory=semantic_memory.cli:main",
        ],
    },
    python_requires=">=3.9",
)
