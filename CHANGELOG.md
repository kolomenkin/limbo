CHANGELOG
=========

future release
------

v1.6 [2020-06-xx]
------

- fix backend: return code 403 in case uploaded file already exists in the storage
- show error message box in case of error during file adding (file already exists & etc)
- Front: improve code formatting

v1.5 [2020-05-31]
------

- Dockerfile: update Python from `3.7.6-alpine` to `3.10.4-alpine3.16`
- remove unused Travis CI support
- update all Python package dependencies to latest versions
- `cherrypy` was split into two projects. Now we are using `cheroot`
- refactor code: use f-strings more
- refactor code: use Path object from `pathlib` instead of `os.path` library

v1.4.4 [2022-05-30]
------

- add GitHub Action CI integration
- CI: automatically build Docker image and upload to Dockerhub registry
- upgrade vulnerable dependencies: `twisted` and `waitress`
- remove broken Python 3.6 support after upgrading `twisted` package
- update all Python package dependencies to modern versions
- fix flaky (unstable) tests
- improve code formatting
- update documentation

v1.4.3 [2020-02-15]
------

- upgrade python packages found vulnerable
- CI fixes and improvements
- drop Python 3.4 support (3.5, 3.6, 3.7 are supported)

v1.4.2 [2018-06-18]
------

- improve CI stability
- CI: add support testing externally started Limbo web server

v1.4.1 [2018-06-15]
------

- fix bug with wrong directory credentials (partly existed from 1.0, became blocking in 1.4)
- refactor lib_file_storage.py to catch and ignore exceptions in retention thread
- force redownload of updated recently main.css
- add Travis CI script for automated build

v1.4 [2018-06-13]
------

- process request body by chunks. Don't need to save big uploaded files to disk twice any more.
- only one web server is found to work fine now: `cherrypy` (later it was renamed to `cheroot`)
- added speed test script for web server speed compare
- atomic files upload: file is never stored partially if upload was not complete
- web page redesign: make corners round
- fix bug in cancel file upload javascript code. Now half-uploaded file is automatically
  removed from server by javascript
- raised max upload file limit from 10 GB to 30 GB in javascript

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

- special release with `Duplo` rebranding. This is a honorable release dedicated
  to original idea of the similar service called `Дупло`
  (pronounced as `dupl'o`, this is translated from Russian as hollow).

v1.1 [2018-05-14]
------

- first implementation
- small amount of code
- single python file
