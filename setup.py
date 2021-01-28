"""
Setup.py
"""
from setuptools import setup
from BAC0 import infos

requirements = ["bacpypes", "colorama"]

setup(
    name="BAC0",
    version=infos.__version__,
    description="BACnet Scripting Framework for testing DDC Controls",
    author=infos.__author__,
    author_email=infos.__email__,
    url=infos.__url__,
    download_url=infos.__download_url__,
    keywords=["bacnet", "building", "automation", "test"],
    packages=[
        "BAC0",
        "BAC0.core",
        "BAC0.core.app",
        "BAC0.core.io",
        "BAC0.core.functions",
        "BAC0.core.devices",
        "BAC0.core.devices.local",
        "BAC0.core.devices.mixins",
        "BAC0.core.utils",
        "BAC0.core.proprietary_objects",
        "BAC0.scripts",
        "BAC0.tasks",
        "BAC0.web",
        "BAC0.sql",
    ],
    include_package_data=True,
    requires=requirements,
    install_requires=requirements,
    test_suite="tests",
    long_description=open("README.rst").read(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
    ],
)
