Exposing FS objects
===================

The ``fs.expose`` module offers a number of ways of making an FS implementation available over an Internet connection, or to other processes on the system. 


FUSE
----
Makes an FS object available to other applications on the system. See :mod:`fs.expose.fuse`.

Dokan
-----
Makes an FS object available to other applications on the system. See :mod:`fs.expose.dokan`.

Secure FTP
----------
Makes an FS object available via Secure FTP. See :mod:`fs.expose.sftp`.

XMLRPC
------
Makes an FS object available over XMLRPC. See :mod:`fs.expose.xmlrpc`

Import Hook
-----------
Allows importing python modules from the files in an FS object. See :mod:`fs.expose.importhook`

Django Storage
--------------
Connects FS objects to Django. See :mod:`fs.expose.django_storage`
