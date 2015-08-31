"""
Setup.py
"""
from setuptools import setup
from BAC0 import infos as infos

setup(name='BAC0',
      version=infos.__version__,
      description='BACnet Scripting Library',
      author=infos.__author__,
      author_email=infos.__email__,
      url=infos.__url__,
      packages=[
          'BAC0',
          'BAC0.core',
          'BAC0.core.app',
          'BAC0.core.io',
          'BAC0.core.functions',
          'BAC0.core.devices',
          'BAC0.scripts'
          ],
      install_requires=[
          'pandas',
          ],
      dependency_links=[
          'git://github.com/ChristianTremblay/bacnetScript.git#egg=package-0.11.34.7'
          ],
      long_description=open('README.rst').read(),
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: System :: Networking",
          "Topic :: Utilities",
          ],)

