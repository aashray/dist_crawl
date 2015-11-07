#/usr/local/bin/python

import thread
import socket
import httplib
import urlparse
import re
import sys
import urllib
from bs4 import BeautifulSoup
import math
from collections import Counter
 
class MyOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15'

# Calculates the entropy of a given string
#
# Return value - the entropy of the string
def entropy(s):
    p, lns = Counter(s), float(len(s))
    return -sum(count/lns * math.log(count/lns, 2) for count in p.values())

# Finds out whether a given url uses nonce
# to help prevent login csrf attack
#
# Return value - True or False
def get_nonce(link):
    myopener = MyOpener()
    page = myopener.open(link)
 
    text = page.read()
    page.close()
 
    soup = BeautifulSoup(text, "lxml")

    forms = soup.find_all('form')

    isNonce = False

    for form in forms:
        password = form.find('input', type="password")
        if password is None:
            continue
            #print "Not a login form!"
        #else:
            #print "Login form found!"

        inputs = form.find_all('input', type="hidden")

        for ip in inputs:
            value = ip.get('value')
            if value and entropy(value) >= 3.5:
                #print "Value:", value, "Entropy:", entropy(value), "NONCE!"
                isNonce = True
            #else:
                #print "Not a nonce!"

    return isNonce

# Gets all the links embedded in the given link (url)
#
# Return value - A list of urls in the given link
def get_links(link):
    myopener = MyOpener()
    #page = urllib.urlopen(url)
    page = myopener.open(link)
 
    text = page.read()
    page.close()
 
    soup = BeautifulSoup(text)
 
    for tag in soup.findAll('a', href=True):
        tag['href'] = urlparse.urljoin(link, tag['href'])
        print tag['href']

# Finds out if a given link contains the following 5
# security properties:
# Http only     :
# Secure cookie :
# Sts           :
# Xframe        :
# Nonce         :
#
# Return value - A list of True / False for the properties
def get_security_properties(link):
    httponly = False
    securecookie = False
    sts = False
    xframe = False
    redirect_max = 3

    while (redirect_max):	
        url_parsed = urlparse.urlparse(link)

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
    # TODO (@anyone): check if per cookie or overall
    cookieinfo = resp.getheader("set-cookie");
    if cookieinfo and "HTTPOnly" in cookieinfo:
        httponly = True
    if cookieinfo and "secure" in cookieinfo:
        securecookie = True

    nonce = get_nonce(link)

    return [sts, xframe, httponly, securecookie, nonce]

# Read the links from master to process
#
# Return value - list of links to be processed
def read_links(client_socket):
	client_socket.setblocking(1)

	read_size = client_socket.recv(10);
	try:
		read_size = int(read_size)
	except:
		print "got non int in read size"
		return []
	
	links_str = ""
	while read_size > 0:
		links_str = links_str + client_socket.recv(read_size)
		read_size -= len(links_str)

	links_lst = links_str.split("\n");

	return links_lst;	

# Handles the job of getting security properties in
# the given link. Also finds all embedded urls in it.
#
# Return value - None
def thread_handler(client_socket):
	links_list = read_links(client_socket);

	for link in links_list:
		if link == "":
			continue
		print get_security_properties(link)
		print get_links(link) # print all links of page.
	print "exiting thread"

# Setup server side socket functionality and listens
# for a connection.
#
# Return value - None
def setup_server_socket():
	serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serversock.bind(("", 21413))
	serversock.listen(10);
	return serversock

def main():
	srv_sock = setup_server_socket();
	while True:
		(client_socket, address) = srv_sock.accept()
    		thread.start_new_thread(thread_handler, (client_socket, ))
	return 0

if __name__ == "__main__":
    sys.exit(main())

