from pathlib import Path

from setuptools import setup


README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")


setup(
    name="prompt-snapshot",
    version="0.1.0",
    description="Generate project snapshots in markdown for AI context.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="",
    py_modules=[],
    scripts=["prompt-snapshot.py"],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
