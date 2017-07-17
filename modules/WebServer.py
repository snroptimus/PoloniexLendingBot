# coding=utf-8
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import curdir, sep
from sys import version as python_version
from cgi import parse_header, parse_multipart

if python_version.startswith('3'):
    from urllib.parse import parse_qs
    from http.server import BaseHTTPRequestHandler
else:
    from urlparse import parse_qs
    from BaseHTTPServer import BaseHTTPRequestHandler

import modules.Lending as Lending

server = None
web_server_ip = "0.0.0.0"
web_server_port = "8080"


def initialize_web_server(config):
    import threading
    global web_server_ip, web_server_port

    if config.has_option('BOT', 'customWebServerAddress'):
        custom_web_server_address = (config.get('BOT', 'customWebServerAddress').split(':'))
        if len(custom_web_server_address) == 1:
            custom_web_server_address.append("8000")
            print "WARNING: Please specify a port for the webserver in the form IP:PORT, default port 8000 used."
    else:
        custom_web_server_address = ['0.0.0.0', '8000']

    web_server_ip = custom_web_server_address[0]
    web_server_port = custom_web_server_address[1]

    thread = threading.Thread(target=start_web_server)
    thread.deamon = True
    thread.start()

def start_web_server():

    try:
        port = int(web_server_port)
        host = web_server_ip
        class myHandler(BaseHTTPRequestHandler):
            #Handler for the GET requests
            def do_GET(self):
                try:
                    if ( self.path.endswith(".html") or
                        self.path.endswith(".json") or
                        self.path.endswith(".png") ):
#                        print curdir + "/www" + self.path
                        f = open(curdir + "/www" + self.path) #self.path has /test.html
                        #note that this potentially makes every file on your computer readable by the internet
                        
                        self.send_response(200)
                        self.send_header('Content-type',    'text/html')
                        self.end_headers()
                        self.wfile.write(f.read())
                        f.close()
                        return
                    elif self.path.endswith(".js"):
                        f = open(curdir + "/www" + self.path) #self.path has /test.html
                        #note that this potentially makes every file on your computer readable by the internet
                        
                        self.send_response(200)
                        self.send_header('Content-type',    'text/javascript')
                        self.end_headers()
                        self.wfile.write(f.read())
                        f.close()
                        return
                    elif self.path.endswith(".css") :
                        f = open(curdir + "/www" + self.path) #self.path has /test.html
                        #note that this potentially makes every file on your computer readable by the internet
                        
                        self.send_response(200)
                        self.send_header('Content-type',    'text/css')
                        self.end_headers()
                        self.wfile.write(f.read())
                        f.close()
                        return
                    else:
                        # Send the html message
                        self.wfile.write("Hello World !")
                        return

                except IOError:
                    self.send_error(404,'File Not Found: %s' % self.path)
            #Handler for the GET requests

            def parse_POST(self):
                ctype, pdict = parse_header(self.headers['content-type'])
                if ctype == 'multipart/form-data':
                    postvars = parse_multipart(self.rfile, pdict)
                elif ctype == 'application/x-www-form-urlencoded':
                    length = int(self.headers['content-length'])
                    postvars = parse_qs(self.rfile.read(length), keep_blank_values=1)
                else:
                    postvars = {}
                return postvars
                
            def do_POST(self):
                if ( self.path == "/setParam" ):
                    
                    postvars = self.parse_POST()
                    print postvars
                    Lending.setParam(float(postvars['minRate'][0]), float(postvars['minRateLonger'][0]), float(postvars['duration'][0]))
                    print postvars['minRate'][0]
                    print postvars['minRateLonger'][0]
                    print postvars['duration'][0]

                    self.send_response(200)
                    self.send_header('Content-type','text/html')
                    self.end_headers()
                    # Send the html message
                    self.wfile.write("Hello World !")
                elif self.path == "/login":

                    postvars = self.parse_POST()
                    print postvars
                    
                    print postvars['username'][0]
                    print postvars['password'][0]

                    if ( postvars['username'][0] == "polobot@mail.com" and 
                        postvars['password'][0] == "polobot" ):
                        self.send_response(200)
                        self.send_header('Content-type','text/html')
                        self.end_headers()
                        # Send the html message
                        self.wfile.write("Succeed!")
                    else:
                        self.send_response(200)
                        self.send_header('Content-type','text/html')
                        self.end_headers()
                        # Send the html message
                        self.wfile.write("Failed!")
                return

        global server

        server = HTTPServer((host, port), myHandler)
        print 'Started httpserver on port ' , port
            
        server.serve_forever()
    except Exception as ex:
        ex.message = ex.message if ex.message else str(ex)
        print('Failed to start WebServer: {0}'.format(ex.message))

def stop_web_server():
    try:
        print "Stopping WebServer"
        threading.Thread(target = server.shutdown).start()
    except Exception as ex:
        ex.message = ex.message if ex.message else str(ex)
        print("Failed to stop WebServer: {0}".format(ex.message))
