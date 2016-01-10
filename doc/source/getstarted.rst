Getting started
===============

Where to download
-----------------
https://github.com/ChristianTremblay/BAC0/
Project will soon be published on PyPi to be able to pip install BAC0

How to install dependencies
---------------------------
BAC0 is based on BACpypes found here::

    pip install bacpypes
    pip install bokeh (or conda install bokeh if using Anaconda)

Bacpypes is now available for python 2.5, 2.7 and 3.4. You can also download it using Pypy.

You will also need Pandas as data processing is so easier with this !

If running Python on Windows, I recommend the use of complete distributions like Anaconda or Enthought Canopy.

How to install BAC0
-------------------
Once the repo has been cloned, use::

    python setup.py install


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
