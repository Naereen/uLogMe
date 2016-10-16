#!/usr/bin/env python2
# -*- coding: utf8 -*-
# ulogme_serve.py for https://github.com/Naereen/uLogMe/
# MIT Licensed, https://lbesson.mit-license.org/
#
from __future__ import print_function  # Python 2 compatibility

import sys
import os
import SocketServer
import SimpleHTTPServer
import cgi
import subprocess
import socket

from export_events import updateEvents
from rewind7am import rewindTime
from notify import notify


# Convenience functions

def writenote(note, time_=None):
    """ From https://github.com/karpathy/ulogme/issues/48"""
    cmd = ["../scripts/note.sh"]
    if time_ is not None:
        cmd.append(str(time_))
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    process.communicate(input=note)
    process.wait()
    notify("uLogMe created a note, with content '{}' and time '{!s}'.".format(note, time_), "note")  # DEBUG


# Custom handler
class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        # default behavior
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers["Content-Type"]
            }
        )
        result = "NOT_UNDERSTOOD"

        if self.path == "/refresh":
            notify("Refreshing the view of uLogMe ...")  # DEBUG
            # recompute jsons. We have to pop out to root from render directory
            # temporarily. It's a little ugly
            refresh_time = form.getvalue("time")
            os.chdir(rootdir)  # pop out
            updateEvents()  # defined in export_events.py
            os.chdir(os.path.join("..", "render"))  # pop back to render directory
            result = "OK"

        if self.path == "/addnote":
            notify("Adding a note in uLogMe ...", icon="note")  # DEBUG
            # add note at specified time and refresh
            note = form.getvalue("note")
            note_time = form.getvalue("time")
            os.chdir(rootdir)  # pop out
            # os.system("echo %s | ../scripts/note.sh %s" % (note, note_time))  # FIXED security threat!
            writenote(note, note_time)
            updateEvents()  # defined in export_events.py
            os.chdir(os.path.join("..", "render"))  # go back to render
            result = "OK"

        if self.path == "/blog":
            notify("Adding a blog post in uLogMe ...", icon="note")  # DEBUG
            # add note at specified time and refresh
            post = form.getvalue("post")
            if post is None:
                post = ""
            post_time = int(form.getvalue("time"))
            os.chdir(rootdir)  # pop out
            trev = rewindTime(post_time)
            with open(os.path.join("..", "logs", "blog_%d.txt" % (post_time, )), "w") as f:
                f.write(post)
            updateEvents()  # defined in export_events.py
            os.chdir(os.path.join("..", "render"))  # go back to render
            result = "OK"

        # This part has to be done manually
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(result)


if __name__ == "__main__":
    IP = "127.0.0.1"  # Instead of "", thanks to https://github.com/karpathy/ulogme/issues/48

    # Port settings
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
        assert PORT > 2024, "Error, you should not ask to use a PORT reserved by the system (<= 2024)"
    else:
        PORT = 8124

    # serve render/ folder, not current folder
    rootdir = os.getcwd()
    os.chdir(os.path.join("..", "render"))

    try:
        httpd = SocketServer.ThreadingTCPServer((IP, PORT), CustomHandler)
        print("Serving ulogme on a HTTP server, see it on 'http://localhost:{}' ...".format(PORT))
        notify("Serving ulogme on a HTTP server, see it on 'http://localhost:{}' ...".format(PORT), icon="terminal")  # DEBUG
        httpd.serve_forever()
    except socket.error as e:
        if e.errno == 98:
            print("\nThe port {} was already used...".format(PORT))
            print("Try again in some time (about 1 minute on Ubuntu), or launch the script again with another port: '$ ulogme_serve.py {}' ...".format(PORT + 1))
        else:
            print("\nError, ulogme_serve.py was interrupted, giving:")
            print("Exception: e =", e)
            # print("Exception: dir(e) =", dir(e))  # DEBUG
    finally:
        print("\nClosing HTTP server...")
        httpd.server_close()
