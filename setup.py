from setuptools import find_packages, setup


# Get the README content
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Get requirements from requirements.txt. TODO: remove this
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f.readlines()]

# Function to read the version from version.py
def get_version():
    version = {}
    with open("src/csm/version.py") as fp:
        exec(fp.read(), version)
    return version['__version__']

# Setup
setup(
    name="csm",
    version=get_version(),
    description="The official Python library for the csm API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Common Sense Machines",
    author_email="support@csm.ai",
    url="https://docs.csm.ai",
    packages=find_packages('./src'),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=requirements,
)
