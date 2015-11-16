import socket
import sys
import copy
import urllib
import urlparse
import pickle
from bs4 import BeautifulSoup
import select 
import time
#import logging
#from mod_python import apache

#Stores the results of all links sent to active_nodes
#This variable can be accessed by get_global_map()
global_map={}

global_node_sockets = []

class MyOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15'

# Get the links/urls present in the page of the given url
# Return value - a list containing the links/urls along with depth. example, [[url1, 0]
def get_links(url, depth, atmost_count):
	urldfg = urlparse.urldefrag(url)
	url = urldfg[0]
	urls_list = []
	myopener = MyOpener()
	page = myopener.open(url)
 
	text = page.read()
	page.close()

	soup = BeautifulSoup(text, "html.parser")
 	for tag in soup.findAll('a', href=True):
		if atmost_count == 0:
			break;
		tag['href'] = urlparse.urljoin(url, tag['href'])
		new_url = urlparse.urldefrag(tag['href'])[0]
		if new_url not in urls_list:
			urls_list.append([new_url, depth + 1])
		atmost_count -= 1;
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

# Sends the links_lst on node_sock. links_lst also has depth with each link. example [[url1, 1], [url2, 1]]
# Concatenates the strings in the list using \n as the delimiter.
# Return value - A map of socket to [[start, end]] list as to what was send to each of the nodes
def send_links(active_sockets, links_lst):
	#print "links_str ",links_lst
	no_sockets = len(active_sockets)
	if no_sockets == 0:
		return {}
	print "no sockets", no_sockets;
	no_links_per_node = int(len(links_lst)/no_sockets)
	if (len(links_lst) % no_sockets):
		no_links_per_node += 1
	distribution_map = {}
	i = 0
	end = 0;
	start = 0;
	while end < len(links_lst):
		for node_sock in active_sockets:

			#end = min((i + 1) * no_links_per_node, len(links_lst))#if i < no_sockets -1 else len(links_lst) #DAFUQ does this mean? TODO
			end = min(start + no_links_per_node, len(links_lst))
			print start, end
			node_links = links_lst[start:end]

			links_str = pickle.dumps(node_links)
			length = len(links_str)

			length_str_10 = "0"*(10 - len(str(length))) + str(length)
			start_index_str_10 = "0"*(10 - len(str(start))) + str(start)
			try:
				node_sock.send(length_str_10);
				node_sock.send(start_index_str_10);
				node_sock.send(links_str);

				if node_sock in distribution_map:
					distribution_map[node_sock].append([start, end]);
				else:
					distribution_map[node_sock] = [[start, end]];
			except:
				print "dayum, failed to send"
				i -= 1
				start -= no_links_per_node
			i += 1
			start += no_links_per_node
			if end == len(links_lst):
				break;
	return distribution_map

def recv_data_from_nodes(dist_map, count):
	node_sockets = dist_map.keys()

	total_to_be_read = 0
	for x in dist_map:
		index_lists = dist_map[x]
		total_to_be_read += len(index_lists)
	store_total_to_be_read = total_to_be_read;
	iterations = 0
	while total_to_be_read:
		readable, writable, exceptional = select.select(node_sockets, [], [], max(30, count/2))
		if len(readable) == 0 and len(writable) == 0 and len(exceptional) == 0:
			iterations += 1
			if store_total_to_be_read > total_to_be_read or iterations >= 2:
				print "timed out"
				return []
			else:
				continue
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

def crawl_bfs(crawl_urls, depth, count):
	queue = []
	queue = copy.copy(crawl_urls);
	return_res = []
	url_and_depth_result = {}
	while len(queue) and len(url_and_depth_result) < count:
		print 'res', len(url_and_depth_result), count;
		url_and_depth = queue.pop(0)
		print 'crawling...', url_and_depth[0]
		if url_and_depth[0] not in url_and_depth_result:
			url_and_depth_result[url_and_depth[0]] = url_and_depth[1]
		child_urls_and_depths = get_links(url_and_depth[0], url_and_depth[1], 2*(count - len(url_and_depth_result)))
		print 'got', len(child_urls_and_depths);
		for each in child_urls_and_depths:
			if len(url_and_depth_result) >= count:
				break;
			if each[0] not in url_and_depth_result:
				queue.append(each);
				url_and_depth_result[each[0]] = each[1]
	for each in url_and_depth_result:
		return_res.append([each, url_and_depth_result[each]])
	print return_res
	return return_res;
# This is the function that needs to be called for a given input URL
# Return value - None
def start_processing(crawl_urls, no_crawl_urls, count):
	#crawl_urls and no crawl_urls example: [[url1, 0], [url2, 0]]
	count = int(count);
	init_master()
	remaining_links = []
	global global_node_sockets
	global global_map
	urls_list = []

	urls_list = crawl_bfs(crawl_urls, 0, count);
	urls_list = urls_list + no_crawl_urls
	print "links count =", len(urls_list)
	distribution_map = send_links(global_node_sockets, urls_list)

	print distribution_map
	recv_data_from_nodes(distribution_map, count);
	print global_map
	print len(global_map)
	print distribution_map
	for each in distribution_map:
		for indexes in distribution_map[each]:
			remaining_links = remaining_links + urls_list[indexes[0]:indexes[1]]
	print remaining_links
	ret_map = copy.copy(global_map) 
	global_map = {};
	global_node_sockets = []
	return [ret_map, remaining_links]

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
	global_node_sockets = setup_all_nodes("/tmp/nodes.conf")

#Main function
#A non zero return value indicates unsuccessful run
#Return value - Int
def main():
	start_processing([[sys.argv[1], 0]], [], int(sys.argv[2]))
	return 0


if __name__ == "__main__":
   sys.exit(main()) 
