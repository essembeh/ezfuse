#!/usr/bin/env python3

from setuptools import find_packages, setup


def readfile(file):
    with open(file) as f:
        return f.read()


def readlines(file):
    return [
        line
        for line in map(str.strip, readfile(file).splitlines())
        if not line.startswith("#")
    ]


setup(
    name="ezfuse",
    description="Quickly mount fuse filesystems in temporary directories",
    url="https://github.com/essembeh/ezfuse",
    license="Mozilla Public License Version 2.0",
    author="Sébastien MB",
    author_email="seb@essembeh.org",
    long_description=readfile("README.md"),
    long_description_content_type="text/markdown",
    python_requires=">=3.6.0",
    setup_requires=["setuptools_scm"],
    use_scm_version={"version_scheme": "post-release"},
    package_dir={"": "src"},
    packages=find_packages("src", exclude=["*_tests"]),
    install_requires=readlines("requirements.txt"),
    entry_points={"console_scripts": ["ezfuse = ezfuse.__main__:main"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
    ],
)
