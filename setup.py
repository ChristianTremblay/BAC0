import os
from setuptools import setup

#
#   read
#

def readReadme(fname):
    """Utility function to read the contents of the README.txt file."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

#
#   __main__
#

setup(name='BAC0',
    version='0.2',
    description='BACnet Scripting Library',
    author='Christian Tremblay',
    author_email='christian.tremblay@servisys.com',
    url='http://www.servisys.com/',
    packages=['BAC0',
              'BAC0.core',
              'BAC0.core.app',
              'BAC0.core.io',
              'BAC0.core.functions',
              'BAC0.scripts'],
    long_description=open('README.txt').read(),
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

