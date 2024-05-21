from setuptools import find_packages, setup


# Get the README content
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Function to read the version from version.py
def get_version():
    version = {}
    with open("src/csm/version.py") as fp:
        exec(fp.read(), version)
    return version['__version__']

# Setup
setup(
    name="csm-ai",
    version=get_version(),
    description="The official Python library for the CSM API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Common Sense Machines",
    author_email="support@csm.ai",
    url="https://github.com/CommonSenseMachines/csm-ai",
    packages=find_packages('./src'),
    package_dir={'': 'src'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=[
        'requests',
        'pillow',
    ],
)
