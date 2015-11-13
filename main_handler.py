import socket
import sys
import copy
import urllib
import urlparse
import pickle
from bs4 import BeautifulSoup
import select 
import time
from threading import Thread


#Stores the results of all links sent to active_nodes
#This variable can be accessed by get_global_map()
global_map={}

global_node_sockets = []
 
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
# Return value - A map of socket to [[start, end]] list as to what was send to each of the nodes
def send_links(active_sockets, links_lst):
	#print "links_str ",links_lst
	no_sockets = len(active_sockets)
	print "no sockets", no_sockets;
	no_links_per_node = int(len(links_lst)/no_sockets)
	distribution_map = {}
	i = 0
	end = 0;
	while end < len(links_lst) - 1:
		print end, len(links_lst)
		for node_sock in active_sockets:
			end = min((i + 1) * no_links_per_node, len(links_lst) - 1)#if i < no_sockets -1 else len(links_lst) #DAFUQ does this mean? TODO
			node_links = links_lst[i * no_links_per_node:end]

			links_str = pickle.dumps(node_links)
			length = len(links_str)

			length_str_10 = "0"*(10 - len(str(length))) + str(length)
			start_index_str_10 = "0"*(10 - len(str(i * no_links_per_node))) + str(i * no_links_per_node)
			print start_index_str_10, i
			try:
				node_sock.send(length_str_10);
				node_sock.send(start_index_str_10);
				node_sock.send(links_str);

				if node_sock in distribution_map:
					distribution_map[node_sock].append([i * no_links_per_node, end]);
				else:
					distribution_map[node_sock] = [[i * no_links_per_node, end]];
			except:
				print "dayum, failed to send"
				i -= 1
			i += 1
	return distribution_map

#Create Server socket on port 22000 to listen to incoming communications
#Return value - socket
def get_server_socket():
	port = 22000
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setblocking(0)    
	server_socket.bind(('localhost', port))
    	server_socket.listen(10)
	print "Server started on port ",port
	return server_socket


def recv_data_from_nodes(dist_map):
	node_sockets = dist_map.keys()

	total_to_be_read = 0
	for x in dist_map:
		index_lists = dist_map[x]
		total_to_be_read += len(index_lists)

	while total_to_be_read:
		print "looping here.."
		readable, writable, exceptional = select.select(node_sockets, [], [], 30)
		if len(readable) == 0 and len(writable) == 0 and len(exceptional) == 0:
			print "timed out!"
			return
		for socket in readable:
			recv_size = socket.recv(10)
			if len(recv_size) == 0:
				print "node closed connection", socket
				node_sockets.remove(socket)
				continue;
			try:
				recv_size = int(recv_size)
			except:
				print "Recv size is not int"
				return []
			recv_start_index = socket.recv(10)
			if len(recv_start_index) == 0:
				print "node closed connection", socket
				node_sockets.remove(socket)
				continue;
			try:
				recv_start_index = int(recv_start_index)
			except:
				print "Recv start index is not int"
				return []
			print "Receiving size", recv_size
			print "Receiving start index", recv_start_index

			recv_data = socket.recv(recv_size)
			if len(recv_data) == 0:
				print "node closed connection", socket
				node_sockets.remove(socket)
				continue;

			local_map = pickle.loads(recv_data)
			global_map.update(local_map)

			total_to_be_read -= 1

			index_lists = dist_map[socket]
			copy_index_lists = copy.copy(index_lists)
			for il in index_lists:
				if il[0] == recv_start_index:
					copy_index_lists.remove(il)
			dist_map[socket] = copy_index_lists
	return []

#API based function to retrive global_map
#TODO To add logic to convert global map to a format consistent with UI requirement
#Return Value - global_map (Map)	
def get_global_map():
	return global_map;


# This is the function that needs to be called for a given input URL
# Return value - None
def start_processing(url):
	global global_node_sockets

	if type(url) == str:
		urls_list = get_links(url)
	else:
		urls_list = url
	time.sleep(5);
	print "links count =", len(urls_list)
	distribution_map = send_links(global_node_sockets, urls_list)

	print distribution_map
	recv_data_from_nodes(distribution_map);
	print global_map
	print distribution_map
	return global_map

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
	global global_node_sockets
	global_node_sockets = setup_all_nodes("./nodes.conf")

#Main function
#A non zero return value indicates unsuccessful run
#Return value - Int
def main():
	init_master()
	start_processing(sys.argv[1])
	return 0


if __name__ == "__main__":
   sys.exit(main()) 