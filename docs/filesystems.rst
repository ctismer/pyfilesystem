Filesystems
===========

This page lists the builtin filesystems.


FTP (File Transfer Protocol)
----------------------------
An interface to FTP servers. See :class:`fs.ftpfs.FTPFS`

Memory
------
A filesystem that exists entirely in memory. See :mod:`fs.memoryfs`


Mount
-----
A filesystem that can map directories in to other filesystems (like a symlink). See :mod:`fs.mountfs`


Multi
-----
A filesystem that overlays other filesystems. See :mod:`fs.multifs`


OS
--
An interface to the OS Filesystem. See :mod:`fs.osfs`


RPCFS (Remote Procedure Call)
-----------------------------
An interface to a file-system served over XML RPC, See :mod:`fs.rpcfs` and :mod:`fs.expose.xmlrpc` 


SFTP (Secure FTP)
-----------------------
A secure FTP filesystem. See :mod:`fs.sftpfs`


S3
--
A filesystem to access an Amazon S3 service. See :mod:`fs.s3fs`


Temporary
---------
Creates a temporary filesystem in an OS provided location. See :mod:`fs.tempfs`


Wrap
----
A collection of wrappers that add new behavior / features to existing FS instances. See :mod:`fs.wrapfs`


Zip
---
An interface to zip files. See :mod:`fs.zipfs`


