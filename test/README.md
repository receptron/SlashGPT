# autotest configuration file

This directory contains autotest configuration files.
This is the file used by the /autotest command.


When running with `/autotest`, default.json is used.
If you run `/autotest foo` with the argument, foo.json will be used.

If manifests is specified in the json file, /switch {manifests} is run to switch the manifests directory.
