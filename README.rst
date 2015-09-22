=============================
Yet Another Coinado.io Client
=============================

What is coinado?
++++++++++++++++
 Coinado is a remote torrenting service.
 We do the torrenting for you, worry about seeding,
 keep your privacy and deliver the file over an encrypted connection.
 After requesting a file, the torrenting happens transparently on our servers
 and a minute later the file starts streaming to you.

And this software is a client of `coinado.io <https://coinado.io>`_.

Dependence
++++++++++
- Requests (http://www.python-requests.org/en/latest/)
- BencodePy (https://github.com/eweast/BencodePy)
- BeautifulSoup4 (http://www.crummy.com/software/BeautifulSoup/)
- PySixel (optional) (https://github.com/saitoha/PySixel)

How to install
++++++++++++++
It is easy.

.. code-block:: bash

   $ git clone https://github.com/pluser/yacoinado.git --depth 1
   $ cd yacoinado.git
   $ pip install -r requirements.txt
   $ pip install PySixel # to display QRcode in your terminal (optional)

Done.

How to use
++++++++++
First of all, you need to set your secret key as environment variable.
The secret key will be found in your genuine coinado.io script file which you have downloaded before.

.. code-block:: bash

   $ export YACOINADO_SECRET=foobarfoooooobaaaaaaa

Now, you can download smoothly.

.. code-block:: bash

   $ python yacoinado.py 743bc6fad39e3a35460d31af5322c131dd196ac2
   $ python yacoinado.py 'http://releases.ubuntu.com/14.04.3/ubuntu-14.04.3-desktop-amd64.iso.torrent'
   $ python yacoinado.py 'magnet:?xt=urn:btih:743bc6fad39e3a35460d31af5322c131dd196ac2&dn=ubuntu-14.04.3-desktop-amd64.iso'
   $ python yacoinado.py ~/Desktop/ubuntu-14.04.3-desktop-amd64.iso.torrent

If you want to download the specific file,

.. code-block:: bash

   $ python yacoinado.py 743bc6fad39e3a35460d31af5322c131dd196ac2 --select filename_or_keyword

Want all files instead of specific file? Yes you can.

.. code-block:: bash

   $ python yacoinado.py 743bc6fad39e3a35460d31af5322c131dd196ac2 --all

To inquire account balance,

.. code-block:: bash

   $ python yacoinado.py --inquire
   ...
   Balance: 6.42 GB
   ...

Advanced usage
++++++++++++++
Basic
-----

.. code-block:: bash

   $ python yacoinado.py --filename 743bc6fad39e3a35460d31af5322c131dd196ac2
   ubuntu-14.04.3-desktop-amd64.iso

.. code-block:: bash

   $ python yacoinado.py --endpoint 743bc6fad39e3a35460d31af5322c131dd196ac2
   https://coinado.io/i/743bc6fad39e3a35460d31af5322c131dd196ac2/auto?u=yoursecretfoobar

.. code-block:: bash

   $ python yacoinado.py --infohash 'http://releases.ubuntu.com/14.04.3/ubuntu-14.04.3-desktop-amd64.iso.torrent'
   743bc6fad39e3a35460d31af5322c131dd196ac2

Using high functioning downloader
---------------------------------

.. code-block:: bash

   $ cat hash-list.txt | python yacoinado.py --endpoint --stdin | xargs curl -O --remote-header-name
   $ cat hash-list.txt | python yacoinado.py --endpoint --stdin | xargs wget --content-disposition

Parallel download (GNU Parallel)
--------------------------------

.. code-block:: bash

   $ cat hash-list.txt | python yacoinado.py --endpoint --stdin | parallel -a - curl -O --remote-header-name

License
+++++++
BSD 3-clause license
