CHANGELOG
=========

future release
------


v1.3 [2018-06-12]
------

- full support for utf-8 file names
- unit tests for storage class 
- auto tests for whole `Limbo` service. Tested a number of web servers with `Limbo`.
- quick server stop

v1.2 [2018-06-10]
------

- improved security (file name cleaning)
- changed default WSGI server in docker (previous did not support utf-8 in URLs)
- fixed bug with missing url encoding for uploaded files
- fixed bug with potentially too much cleaning of file name
- now code passes `flake8` checks
- refactoring into few separate modules

v1.1 [2018-05-30] "Duplo"
------

- special release with `Duplo` rebranding. This is a honorable release dedicated to original idea of the similar service called `Дупло` (pronounced as "dupl`o", translated from Russian as hollow).

v1.1 [2018-05-14]
------

- first implementation
- small amount of code
- single python file
