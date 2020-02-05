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

If you are using Windows, it will simplify your life as some modules needs a
C compiler and it can be hard sometimes to compile a module by yourself. 

Some examples of complete distributions are Anaconda_ or `Enthought Canopy <https://www.enthought.com/products/canopy/>`_.
As I use Anaconda_, I'll focus on this one but you're free to choose the one
you prefer.

If you are using a RaspberryPi, have a look to miniconda_ or berryconda_. Both can allow a complete installation of modules like bokeh_ and Flask_

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
Open the Anaconda Prompt (a console terminal with Python configured in the path) ::

    pip install BAC0

This simple line will look in Pypi_ (The Python Package Index), download and
install everything you need to start using BAC0

.. _check-that-bac0-works:

Check that BAC0 works
+++++++++++++++++++++
In the terminal again, type :: 

    python

This will open a python terminal. In the terminal type :: 

    >>import BAC0
    >>BAC0.version

This will show you the installed version. You're good to go.   

.. _where-to-download-the-source-code:

Where to download the source code
---------------------------------
https://github.com/ChristianTremblay/BAC0/

There you'll be able to open issues if you find bugs.

.. _dependencies:

Dependencies
------------
* BAC0 is based on BACpypes_ for all BACnet/IP communication.

  Starting at version 0.9.900, BAC0 will not strictly depend on bokeh_ or Flask_ or Pandas_ to work. Having them will allow to use the complete set of features (the web app with live trending features) but if you don't have them installed, you will be able to use the 'lite' version of BAC0 which is sufficient to interact with BACnet devices.

* It uses Bokeh_ for Live trending features 
* It uses Pandas_ for every Series and DataFrame (histories)
* It uses Flask_ to serve the Web app (you will need to pip install flask_bootstrap)

Normally, if you have installed Anaconda_, Flask_, Bokeh_ and Pandas_ will already
be installed. You'll only need to install BACpypes_ ::

    pip install bacpypes
    pip install bokeh (or conda install bokeh if using Anaconda)

You're ready to begin using BAC0 !

.. |build-status| image:: https://travis-ci.org/ChristianTremblay/BAC0.svg?branch=master
   :target: https://travis-ci.org/ChristianTremblay/BAC0
   :alt: Build status
     
.. |docs| image:: https://readthedocs.org/projects/bac0/badge/?version=latest
   :target: http://bac0.readthedocs.org/
   :alt: Documentation
   
.. |coverage| image:: https://coveralls.io/repos/ChristianTremblay/BAC0/badge.svg?branch=master&service=github 
   :target: https://coveralls.io/github/ChristianTremblay/BAC0?branch=master
   :alt: Coverage

.. _bacpypes : https://github.com/JoelBender/bacpypes

.. _bokeh : http://www.bokehplots.com

.. _Flask : http://flask.pocoo.org/

.. _Pandas : http://pandas.pydata.org/

.. _anaconda : https://www.continuum.io/downloads

.. _Pypi : https://pypi.python.org/pypi

.. _miniconda : https://conda.io/miniconda.html

.. _berryconda : https://github.com/jjhelmus/berryconda
