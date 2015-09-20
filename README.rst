=============================
Yet Another Coinado.io client
=============================

How to install
--------------
It is easy.
.. code-block:: bash
   git clone hogehoge --depth 1
   pip install -r requirements.txt
Done.

How to use
----------
First of all, you must set your secret key as environment variable.
Secret key will be found in your genuin coinado script file which you have downloaded before.
.. code-block:: bash
   export COINADO_SECRET=foobarfoooooobaaaaaaa

Now, you can download smoothly.
.. code-block:: bash
   python yacoinado.py 743bc6fad39e3a35460d31af5322c131dd196ac2
   python yacoinado.py 'http://releases.ubuntu.com/14.04.3/ubuntu-14.04.3-desktop-amd64.iso.torrent'
   python yacoinado.py 'magnet:?xt=urn:btih:743bc6fad39e3a35460d31af5322c131dd196ac2&dn=ubuntu-14.04.3-desktop-amd64.iso'
   python yacoinado.py ~/Desktop/ubuntu-14.04.3-desktop-amd64.iso.torrent

License
-------
BSD 3-clause license
