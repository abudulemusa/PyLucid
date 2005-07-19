#!/usr/bin/python
# -*- coding: UTF-8 -*-

# by jensdiemer.de (steht unter GPL-License)

"""
Ist f�r die Darstellung der Seiten zust�ndig
"""

__author__ = "Jens Diemer (www.jensdiemer.de)"

__version__="0.0.3"

__history__="""
v0.0.3
    - main_menu, sub_menu und back_links mit Modul-Manager
v0.0.2
    - tinyTextile eingebaut
v0.0.1
    - erste Version
"""


import config


# Python-Basis Module einbinden
import os, sys, re





# Für Debug-print-Ausgaben
#~ print "Content-type: text/html\n\n<pre>%s</pre>" % __file__
#~ print "<pre>"


class pagerender:
    def __init__( self, PyLucid ):
        self.PyLucid = PyLucid
        self.session        = PyLucid["session"]
        self.CGIdata        = PyLucid["CGIdata"]
        self.db             = PyLucid["db"]
        self.config         = PyLucid["config"]
        self.module_manager = PyLucid["module_manager"]
        self.tools          = PyLucid["tools"]
        self.page_msg       = PyLucid["page_msg"]

    def admin_menu( self ):
        """Baut das Front-Menü zusammen"""
        menu = '<p class="adminmenu">[ '
        menu += self.lucidTag_script_login()

        # Front-Menü Daten vom Module-Manager holen
        menu_data = self.module_manager.get_menu_data( "front menu" )
        for order,data in menu_data.iteritems():
            if data.has_key("get_page_id") and data["get_page_id"] == True:
                # Aktuelles Modul benötigt den page_id Parameter
                post_parameter = "&page_id=%s" % self.CGIdata["page_id"]
            else:
                post_parameter = ""

            menu += ' | <a href="%(url)s?command=%(order)s%(post)s" title="%(title)s">%(txt)s</a>' % {
                "url"   : self.config.system.real_self_url,
                "order" : order,
                "post"  : post_parameter,
                "title" : data['txt_long'],
                "txt" : data['txt_menu'],
            }

        menu += " ]</p>"
        return menu


    #____________________________________________________________________________
    # lucid-Tags

    def replace_lucidTags( self, content, side_data ):
        if type( content ) != str:
            return "pagerender.replace_lucidTags - Error: content invalid:" + str( content )
            return "pagerender.replace_lucidTags - Error: content invalid!"

        #~ print "Content-type: text/html\n"
        #~ print content
        #~ print "<pre>"
        #~ import cgi
        #~ for k,v in side_data.iteritems(): print k,"-",cgi.escape(str(v))
        #~ print "</pre>"

        if side_data["description"]==None:
            side_data["description"] = ""

        # Fest eingebaute Regeln
        rules = [
            ( "<lucidTag:page_style_link/>",    self.lucidTag_page_style_link       ),
            ( "<lucidTag:script_login/>",       self.lucidTag_script_login          ),
            ( "<lucidTag:page_name/>",          side_data["name"]                   ),
            ( "<lucidTag:page_title/>",         side_data["title"]                  ),
            ( "<lucidTag:page_keywords/>",      side_data["keywords"]               ),
            ( "<lucidTag:page_description/>",   side_data["description"]            ),
            ( "<lucidTag:powered_by/>",         __info__                            ),
            (
                "<lucidTag:page_last_modified/>",
                self.tools.convert_date_from_sql( side_data["lastupdatetime"] )
            ),
        ]

        # Regeln mit dynamischen Modulerweiterungen ergänzen
        lucidTags_modules_data = self.module_manager.get_lucidTags()
        for tag_module, data in lucidTags_modules_data.iteritems():
            tag = "<lucidTag:%s/>" % data["lucidTag"]
            rules.append(
                ( tag, self.module_manager.start_module(data) )
            )

        if self.session.ID != False:
            # User ist eingeloggt, nur dann werden folgende Tags ersetzt:
            rules.append(
                ( "<lucidTag:admin_sub_menu_list/>",self.lucidTag_admin_sub_menu_list() )
            )

        for rule in rules:
            if content.find(rule[0]) != -1: # Ersatz für "rule[0] in content"
                if rule[1] == None:
                    # None Objekte enstehen, wenn es in der DB ein NULL Wert hat
                    continue

                if type( rule[1] ) == str:
                    # Ist ein normaler String
                    content = content.replace( rule[0], rule[1] )
                else:
                    # Ist eine Funktion
                    content = content.replace( rule[0], rule[1]() )

        rules = [
            ( "<lucidFunction:IncludeRemote>(.*?)</lucidFunction>(?uism)", self.lucidFunction_IncludeRemote ),
        ]
        for rule in rules:
            try:
                content = re.sub( rule[0], rule[1], content )
            except Exception, e:
                return "pagerender.replace_lucidTags - Error: '%s' Tag:'%s'" % ( e, rule[0] )

        return content

    def lucidTag_page_style_link( self ):
        CSS_content = self.db.side_style_by_id( self.CGIdata["page_id"] )
        return "<style>%s</style>" % CSS_content

    def lucidTag_script_login( self ):
        if self.session.has_key("user"):
            return '<a href="%s?page_id=%s&command=logout">logout [%s]</a>' % (
                self.config.system.real_self_url, self.CGIdata["page_id"], self.session["user"]
            )
        else:
            return '<a href="%s?page_id=%s&command=login">login</a>' % (
                self.config.system.real_self_url, self.CGIdata["page_id"]
            )

    #~ def lucidTag_lastupdatetime( self ):
        #~ return self.tools.convert_date_from_sql( side_data["lastupdatetime"] )

    #____________________________________________________________________________
    # lucid-Tags für eingeloggte User

    def lucidTag_admin_sub_menu_list( self ):
        """ Erstellt das admin-sub-Menü """
        menu = ""
        menu_data = self.module_manager.get_menu_data( "admin sub menu" )
        menu = '<ul class="admin_sub_menu">'
        for order,data in menu_data.iteritems():
            menu += '<li><a href="?command=%s" title="%s">%s</a></li>' % (
                order, data['txt_long'], data['txt_menu']
            )
        menu += "</ul>"
        return menu

    #____________________________________________________________________________
    # lucid-Function

    def lucidFunction_IncludeRemote( self, matchobj ):
        """
        Unterscheidet zwischen Lokalen PyLucid-Skripten und echten URL-Abfragen
        """

        #~ return "TEST"

        import urllib2
        URL = matchobj.group(1)

        try:
            f = urllib2.urlopen( URL )
            sidecontent = f.read()
            f.close()
        except Exception, e:
            return "<p>IncludeRemote error! Can't get '%s'<br /> \
                error:'%s'</p>" % ( URL, e )

        try:
            return re.findall("<body.*?>(.*?)</body>(?uism)", sidecontent)[0]
        except:
            return sidecontent


    #____________________________________________________________________________
    # Render Page

    def lucidTag_page_body( self, side_data ):
        """Parsen des SeitenInhalt, der Aufgerufenen Seite"""

        #~ page_data = self.db.get_page_data_by_id( self.CGIdata["page_id"] )

        #~ main_content = page_data["content"]

        # Das Markup anwenden
        side_data["content"] = self.apply_markup( side_data["content"], side_data["markup"] )

        side_data["content"] = self.replace_lucidTags( side_data["content"], side_data )

        return side_data["content"]

    def apply_markup( self, content, markup ):
        "Wendet das passende Markup an"

        if markup == "textile":
            try:
                return self.parse_textile_page( content )
            except Exception, e:
                return "[Can't use textile-Markup (%s)]\n%s" % ( e, content )
        elif markup == "none":
            return content
        else:
            return "[Markup '%s' not supported yet :(]\n%s" % ( markup, content )

    def parse_textile_page( self, content ):
        "textile Markup anwenden"
        import tinyTextile
        fileobj = fileobj_save()
        #~ tinyTextile.parser( sys.stdout ).parse( txt )
        tinyTextile.parser( fileobj ).parse( content )
        return fileobj.get()

        #~ from textile import textile
        #~ return textile.textile( content )



class fileobj_save:
    def __init__( self ):
        self.data = ""
    def write( self, txt ):
        self.data += txt
    def get( self ):
        return self.data













