# coding: utf-8

#_____________________________________________________________________________
# use the undocumented django function to add the "lucidTag" to the tag library.
# 
from django.template import add_to_builtins
add_to_builtins('extrahead.defaulttags')
