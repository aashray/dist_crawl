import socket
import sys
import urllib
import urlparse
from bs4 import BeautifulSoup
 
class MyOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15'

# Get the links/urls present in the page of the given url
# Return value - a list containing the links/urls
def get_links(url):
	urls_list = []	
	myopener = MyOpener()
	#page = urllib.urlopen(url)
	page = myopener.open(url)
 
	text = page.read()
	page.close()
 	
	soup = BeautifulSoup(text, "html.parser")
 	for tag in soup.findAll('a', href=True):
		tag['href'] = urlparse.urljoin(url, tag['href'])
		#print tag['href']
		if tag['href'] not in urls_list:
			urls_list.append(tag['href'])
	return urls_list

# Sets up connection with the given ip, port.
# Return value - the socket for the connection
def setup_connection_node(ip, port):
	node_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		node_sock.settimeout(1); # will block for _ no.of seconds to connect
		node_sock.connect((ip, port));
	except:
		print "Couldn't connect to ", ip, ":", port
		return None

	return node_sock;

# Sends the links_lst on node_sock.
# Concatenates the strings in the list using \n as the delimiter.
# Return value - None
def send_links(node_sock, links_lst):

	links_str = '\n'.join(links_lst)
	length = len(links_str);
	
	length_str_10 = "0"*(10 - len(str(length))) + str(length)

	node_sock.send(length_str_10);

	node_sock.send(links_str);
	#print links_str, length

# This is the function that needs to be called for a given input URL
# Return value - None
def start_processing(url):
	urls_list = get_links(url)
	print urls_list

# Reads the config file path for slave nodes'
# connection information.
# Return value - list of ip:port for the slave nodes
def read_nodes_info(conf_file_path):
	fd = open(conf_file_path, "r");
	if fd == None:
		return None

	conf_file_content = fd.read()
	nodes = conf_file_content.split("\n");
	ips_and_ports = []
	
	for node in nodes:
		ip_port = node.split(":");
		if (len(ip_port) == 2):
			ips_and_ports.append(ip_port)
	return ips_and_ports;


# Reads nodes information from nodes_conf_file_path and
# sets up the sockets on the active nodes.
# Return value - a list of active sockets created
def setup_all_nodes(nodes_conf_file_path):
	ips_and_ports = read_nodes_info(nodes_conf_file_path)
	active_node_sockets = []

	for each in ips_and_ports:
		ip = each[0]
		port = int(each[1])
		node_sock = setup_connection_node(ip, port);
		if node_sock == None:
			continue;
		active_node_sockets.append(node_sock)

	print "activ nodes :", len(active_node_sockets)
	if len(active_node_sockets) == 0:
		return []

	return active_node_sockets
	
# First thing that should run after master is started
# Return value - None
def init_master():

	active_node_sockets = setup_all_nodes("./nodes.conf")

init_master()

print len(sys.argv)
start_processing(sys.argv[1])
