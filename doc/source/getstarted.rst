.. _getting-started:

Getting started
===============

.. _i-know-nothing-about-python:

I know nothing about Python
---------------------------
First, welcome to the Python community. If you're new to Python programming, 
it can be hard to know where to start.

I highly recommend to start with a complete distribution. That will help you a 
lot as the majority of important modules will be installed for you.

If you are using Windows, it will simplify your life as some modules need a
C compiler and it can be hard sometimes to compile a module by yourself. 

Some examples of complete distributions are Anaconda_ or `Enthought Canopy <https://www.enthought.com/products/canopy/>`_.
As I use Anaconda_, I'll focus on this one but you're free to choose the one
you prefer.

If you are using a Raspberry Pi, have a look at miniconda_ or berryconda_.
For berryconda, once it's done, run `conda install pandas` to install pandas without compiling.

.. _installing-a-complete-distribution:

Installing a complete distribution
++++++++++++++++++++++++++++++++++
Begin by downloading Anaconda_. Install it. Once it's done, you'll get access
to a variety of tools like : 

    * Spyder (and IDE to write the code)
    * Anaconda Prompt (a console configured for Python)
    * Jupyter Notebook (Python in your browser)
    * pip (a script allowing you to install modules)
    * conda (a package manager used by Anaconda_)

.. _start-using-pip:

Start using pip
+++++++++++++++
Open a terminal (e.g., Anaconda Prompt on Windows) ::

    pip install BAC0

This simple line will look in Pypi_ (The Python Package Index), download and
install everything you need to start using BAC0

.. _check-that-bac0-works:

Check that BAC0 works
+++++++++++++++++++++
In the terminal again, start the asyncio REPL and create a session :: 

    python -m asyncio

This will open a python terminal. In the terminal type :: 

    >>> import BAC0
    >>> async with BAC0.start() as bacnet:
    ...     # connected, ready to use
    ...     pass

This will show you the installed version. You're good to go.   

You can also assign directly and manage cleanup yourself ::

    >>> import BAC0, asyncio
    >>> async def demo():
    ...     bacnet = BAC0.start()  # or BAC0.connect(), BAC0.lite()
    ...     try:
    ...         # use bacnet
    ...         await bacnet._discover(global_broadcast=True)
    ...     finally:
    ...         await bacnet._disconnect()  # or: await bacnet.disconnect()
    ...
    >>> asyncio.run(demo())

Note: the context manager waits for full initialization before entering. Without it, most operations work immediately, but a few conveniences may need a brief moment to become ready.

.. _where-to-download-the-source-code:

Where to download the source code
---------------------------------
https://github.com/ChristianTremblay/BAC0/

There you'll be able to open issues if you find bugs.

.. _dependencies:

Dependencies
------------
* BAC0 is based on BACpypes3_ for BACnet/IP communication.

Optional:
* Pandas_ for convenient history handling
* rich for nicer console output
* python-dotenv to load a .env

You're ready to begin using BAC0!

.. |build-status| image:: https://travis-ci.org/ChristianTremblay/BAC0.svg?branch=master
   :target: https://travis-ci.org/ChristianTremblay/BAC0
   :alt: Build status
     
.. |docs| image:: https://readthedocs.org/projects/bac0/badge/?version=latest
   :target: http://bac0.readthedocs.org/
   :alt: Documentation
   
.. |coverage| image:: https://coveralls.io/repos/ChristianTremblay/BAC0/badge.svg?branch=master&service=github 
   :target: https://coveralls.io/github/ChristianTremblay/BAC0?branch=master
   :alt: Coverage

.. _bacpypes3 : https://github.com/JoelBender/BACpypes3

.. _Pandas : http://pandas.pydata.org/

.. _anaconda : https://www.continuum.io/downloads

.. _Pypi : https://pypi.python.org/pypi

.. _miniconda : https://conda.io/miniconda.html

.. _berryconda : https://github.com/jjhelmus/berryconda
