BAC0 |build-status| |coverage| |docs|
=====================================
BAC0 is a Python 3 (3.4 and over) scripting application that uses bacpypes_ to process bacnet messages on a IP network. 
This library brings out simple commands to browse a bacnet network, read properties from bacnet devices or write to them.

Python is a simple language to learn and a very powerful tool for data processing. Coupled to bacnet, it becomes a great 
tool to test devices an interact with controllers.

Test driven development (TDD) for DDC controls
==============================================
BAC0 allows users to simply test an application even if sensors are not connected to the controller. Using the out_of_service
property, it's easy to write a value to the input so the controller will think an input is conencted. 

Without a program like BAC0, you can rely on your DDC programming tool... but it is often slow and
every test must be done manually.

Now you can write your test and run them as often as you want.

Better start-up with data acquisition
=====================================
As you will discover, when you define a controller in BAC0, you will get access to historical data of
every variables in the controllers. Every points are trended every 10 seconds by default. Which means 
that you can do data analysis on everything while you're doing your startup. It allows to see performances and
trouble really fast.


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
