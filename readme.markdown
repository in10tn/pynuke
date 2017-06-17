## Demo

Demo auto-build every 2 hours with the last commit: [http://demo.pynuke.net](http://demo.pynuke.net)

### Overview ###

Pynuke is an open source CMS, developed in python with web2py framework. 
It's simple, easy to use and has a great potential. It's currently in beta.

## Key Features

* Free and open source software, programmed in python using web2py
* Modules available: 
    * [Announcements](https://bitbucket.org/pynukedev/announcements)
    * [CameraJS](https://bitbucket.org/pynukedev/camerajs)
    * [ChildMenu](https://bitbucket.org/pynukedev/childmenu)
    * [Feedback](https://bitbucket.org/pynukedev/feedback/overview)
    * [HTML](https://bitbucket.org/pynukedev/pynuke/wiki/module_text_html)
    * [Portfolio](https://bitbucket.org/pynukedev/portfolio)
    * [PressBlog](https://bitbucket.org/pynukedev/pressblog)
    * [SQL](https://bitbucket.org/pynukedev/sql)
    * [Testimonials](https://bitbucket.org/pynukedev/testimonials)

* Create pages and add modules into panels, modify content easily.
* Web hierarchical structure in multi-level menus.
* Manage users and roles, assign permissions to pages
* Create your own designs or modules
* Optimized from the start to search engines

## Requirements

* Web2py Framework 
* Python 2.5, 2.6, 2.7.
* Python YAML module

Note: Google appengine is not supported.

### Preparing the installation package from source code

Please download the source code, unzip it and package it into a file w2p


* Download [the last zip file with sources](https://bitbucket.org/pynukedev/pynuke/get/default.tar.gz "Format tar.gz") and unzip to a folder.

    `wget https://bitbucket.org/pynukedev/pynuke/get/default.tar.gz -O ./pynuke.tar.gz`
      
    `gzip -dc pynuke.tar.gz | tar -x`
    

    `#change to folder`
    
    `cd pynukedev-pynuke-commit (change commit for commit id)`




* Compress all files in format "Tar.gz" in a file called pynuke.w2p


    `tar czf ./pynuke.w2p ./ --exclude=*.tar --exclude=*.w2p`



### Installing

* Upload the file pynuke.w2p from web2py administrator using the mechanism of installing new applications and call the application "init", in this way the default boot application will be Pynuke.

* You must move the file "root move_to_root_routes.py" in pynuke folder to root of web2py folder and rename to routes.py

* Access the web site, you should see the home page in pynuke, press the login button

* To enter the first time, username admin and password admin.