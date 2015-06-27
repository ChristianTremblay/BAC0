.. BAC0 documentation master file

BAC0 is a Python 3 scripting application that uses BACpypes to process bacnet messages on a IP network. 
This library brings out simple commands to browse a bacnet network, read properties from bacnet devices or write to them.

Python is a simple language to learn and a very powerful tool for data processing. Coupled to bacnet, it becomes a great 
tool to test devices an interact with controllers.

Where to download
-----------------
http://christiantremblay.github.io/BAC0/

What you need
-------------
BAC0 is based on BACpypes-python3 found here::

    git clone https://github.com/ChristianTremblay/bacpypes-python3

This is a port of the official BACpypes module found here::
    
    svn checkout svn://svn.code.sf.net/p/bacpypes/code/trunk bacpypes-code

Except that it works with Python 3... Yeah, that's why it's called bacpypes-python3... :0)

How to install
--------------
Once the repo has been cloned, use::

    python setup.py install

Demo in a Jupyter Notebook
--------------------------
When installed, module can be used to script communication with bacnet device.
Jupyter Notebooks are an excellent way to test it

https://github.com/ChristianTremblay/BAC0/blob/master/Jupyter/BAC0.ipynb
