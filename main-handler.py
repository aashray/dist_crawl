import socket

def setup_connection_node(ip, port):
	node_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		node_sock.settimeout(1);
		node_sock.connect((ip, port));
	except:
		print "Couldn't connect to ", ip, ":", port
		return None

	return node_sock;

def send_links(node_sock, links_lst):

	links_str = '\n'.join(links_lst)
	length = len(links_str);
	
	length_str_10 = "0"*(10 - len(str(length))) + str(length)

	node_sock.send(length_str_10);

	node_sock.send(links_str);
	#print links_str, length

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

def read_all_links(links_path):
	
	fd = open(links_path, "r");
	if fd == None:
		return []
	all_links = fd.read().split("\n");
	all_links.remove("");
	return all_links

def main():
	ips_and_ports = read_nodes_info("./nodes.conf")
	all_links = read_all_links("./links.txt");

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
		return

	print "total number of links:", len(all_links)

	links_per_node = len(all_links)/len(active_node_sockets)
	if (len(all_links) % len(active_node_sockets) != 0):
		links_per_node += 1
	
	print "links per node: atmost", links_per_node
	start = 0;
	for i in xrange(len(active_node_sockets)):
		print "sent ", start, "to ", min(start + links_per_node, len(all_links)) - 1, "to", active_node_sockets[i].getpeername()
		send_links(active_node_sockets[i], all_links[start: min(start + links_per_node, len(all_links))]);
		start = start + links_per_node;

main()

