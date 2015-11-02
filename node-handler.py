#/usr/local/bin/python

import thread
import socket
import httplib
from urlparse import urlparse

def get_security_properties(link):
	httponly = False
	securecookie = False
	sts = False
	xframe = False
	
	redirect_max = 3

	while (redirect_max):	
		url_parsed = urlparse(link)

		if url_parsed == None:
			return []
		#print url_parsed
		if url_parsed.scheme == "https":
			conn = httplib.HTTPSConnection(url_parsed.netloc)
		else:
			conn = httplib.HTTPConnection(url_parsed.netloc)
	
		if conn == None:
			return []
		conn.request("GET", url_parsed.path)

		resp = conn.getresponse()

		if (resp.status != 200):
			if (resp.status == 302) or (resp.status == 301):
				link = resp.getheader("location")
				redirect_max -= 1
			else:
				print link, " not ok, status ", resp.status, 
				return []
		else:
			break;
	print link, 	
	temp = resp.getheader("strict-transport-security")
	if temp:
		sts = True
	temp = resp.getheader("x-frame-options")
	if temp:
		xframe = True

	cookieinfo = resp.getheader("set-cookie");
	if cookieinfo and "HTTPOnly" in cookieinfo:
		httponly = True
	if cookieinfo and "secure" in cookieinfo:
		securecookie = True

	return [sts, xframe, httponly, securecookie]

def read_links(client_socket):

	client_socket.setblocking(1)

	read_size = client_socket.recv(10);
	try:
		read_size = int(read_size)
	except:
		print "got non int in read size"
		return []
	
	while read_size > 0:
		links_str = client_socket.recv(read_size)
		read_size -= len(links_str)

	links_lst = links_str.split("\n");

	return links_lst;	

def thread_handler(client_socket):
	links_list = read_links(client_socket);

	for link in links_list:
		if link == "":
			continue
		print get_security_properties(link)
	print "exiting thread"

def setup_server_socket():
	serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversock.bind(("", 21413))
	serversock.listen(10);
	return serversock


srv_sock = setup_server_socket();

while True:
	(client_socket, address) = srv_sock.accept()
	thread.start_new_thread(thread_handler, (client_socket, ))
