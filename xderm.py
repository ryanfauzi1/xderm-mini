#!/usr/bin/python
import re
import ssl
import time
import json
import random
import select
import datetime
import socket
import threading
import os
import sys

class server_tunnel(threading.Thread):
    def __init__(self, socket_accept, force_tunnel_type=None, external=False, quiet=False):
        super(server_tunnel, self).__init__()

        self.socket_client, (self.client_host, self.client_port) = socket_accept
        self.force_tunnel_type = force_tunnel_type
        self.external = external
        self.quiet = quiet

        self.server_name_indication = 'explor.zoom.us'
        self.tunnel_type = ''
        self.proxies = []
        self.payload = ''
        self.config = {}

        self.do_handshake_on_connect = True
        self.buffer_size = 65535
        self.timeout = 3
        self.daemon = True

    def extract_client_request(self):
        self.client_request = self.socket_client.recv(self.buffer_size).decode('charmap')
        result = re.findall(r'(([a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+):([0-9]+))', self.client_request)
        result = result[0] if len(result) else ''
        self.host, self.port = result[1], int(result[3])
        return True

    def handler(self):
        sockets = [self.socket_tunnel, self.socket_client]
        timeout = 0
        self.socket_client.sendall(b'HTTP/1.0 200 Connection established\r\n\r\n')
        while True:
            timeout += 1
            socket_io, _, errors = select.select(sockets, [], sockets, 3)
            if errors: break
            if socket_io:
                for socket in socket_io:
                    try:
                        data = socket.recv(self.buffer_size)
                        if not data: break
                        if socket is self.socket_tunnel:
                            self.socket_client.sendall(data)
                        elif socket is self.socket_client:
                            self.socket_tunnel.sendall(data)
                        timeout = 0
                    except: break
            if timeout == 30: break

    def konek(self):
        try:
            print('Soket disentuh oleh ' +self.host)
            self.socket_tunnel.connect((self.host, int(self.port)))
            self.socket_tunnel = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2).wrap_socket(self.socket_tunnel, server_hostname=self.server_name_indication, do_handshake_on_connect=self.do_handshake_on_connect)
            self.handler()
        except OSError:
            print('Error: Connection closed.')
        finally:
            self.socket_tunnel.close()
            self.socket_client.close()

    def run(self):
        self.socket_tunnel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_tunnel.settimeout(self.timeout)

        if not self.extract_client_request():
            self.socket_tunnel.close()
            self.socket_client.close()
            return
        self.konek()

class server(threading.Thread):
    def __init__(self, inject_host_port, force_tunnel_type=None, external=False, quiet=False):
        super(server, self).__init__()
        self.inject_host, self.inject_port = self.inject_host_port = inject_host_port
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.force_tunnel_type = force_tunnel_type
        self.external = external
        self.quiet = quiet
        self.daemon = True

    def run(self):
        try:
            self.socket_server.bind(self.inject_host_port)
            self.socket_server.listen(True)
            while True:
                try:
                    server_tunnel(self.socket_server.accept(), self.force_tunnel_type, self.external, self.quiet).start()
                except KeyboardInterrupt: pass
        except OSError:
            print('Inject not running!')

def main():
 print('Inject Started on 8789.')
 server(('127.0.0.1', 8789), external=True, quiet=False).run()

if __name__ == '__main__':
    main()
