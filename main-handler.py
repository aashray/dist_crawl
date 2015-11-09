import socket
import sys
import urllib
import urlparse
import pickle
from bs4 import BeautifulSoup
import select 
from threading import Thread


#Stores the results of all links sent to active_nodes
#This variable can be accessed by get_global_map()
global_map={}

 
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
def send_links(active_sockets, links_lst):
	#print "links_str ",links_lst
	no_sockets = len(active_sockets)
	no_links = int(len(links_lst)/no_sockets)
	i=0
	for node_sock in active_sockets:
		end=(i+1)*no_links if i<no_sockets-1 else len(links_lst)
		node_links = links_lst[i*no_links:end]
		#links_str = '\n'.join(node_links)
		links_str = pickle.dumps(node_links)
		length = len(links_str)
		length_str_10 = "0"*(10 - len(str(length))) + str(length)
		node_sock.send(length_str_10);
		node_sock.send(links_str);
		i+=1
		#print links_str, length

#Receive results from active nodes.
#Sends back confirmation to the active nodes
# TODO Availability (Actions to be taken if a node goes down)
def recv_results(global_no_active_nodes):
		no_active_nodes = int(global_no_active_nodes)

		input_sockets=[]

		#Create Server socket on port 22000 to listen to uncoming communications
		port = 22000
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.setblocking(0)    
		server_socket.bind(('localhost', port))
    		server_socket.listen(10)
		input_sockets.append(server_socket)
		print "Server started on port ",port

		while len(input_sockets)>0:
			try:
				#Select statement
				read_s,write_s,error_s=select.select(input_sockets,[],[])
				
				for s in read_s:
					if s is server_socket:
						connection, client_address = s.accept()
						connection.setblocking(5)
						read_s.append(connection)
				
					else:
						try:
						    #Read data
						    read_size = s.recv(10)
						    data = s.recv(int(read_size))
						    
						    #Append to global map
					            local_map = pickle.loads(data)
						    global_map.update(local_map)

						    #Confirmation sent to active node.
						    s.send("0000000003")
						    s.send("yes");

						except Exception, msg:
						    print "READ ERROR", msg
						    s.close()
						    read_s.remove(s)

			except Exception, msg:
				print "Error in select.select"
				print msg


			if s in input_sockets:
				read_s.remove(s)


			no_active_nodes-=1
			if no_active_nodes==0:
				print "GLOBAL MAP"
    				for k in global_map:
					print k, global_map[k]
				
				server_socket.close()
				return

#API based function to retrive global_map
#TODO To add logic to convert global map to a format consistent with UI requirement	
def get_global_map():
	return global_map;


# This is the function that needs to be called for a given input URL
# Return value - None
def start_processing(url):
	urls_list = get_links(url)
	return urls_list

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
	return active_node_sockets


#Main function
#A non zero return value indicates an unsuccessful run
def main():
	try:
		active_node_sockets=init_master()
		links = start_processing(sys.argv[1])
		t = Thread(target=recv_results, args=(str(len(active_node_sockets)),))
		t.start()
		send_links(active_node_sockets, links)
    		t.join()
		return 0
	except Exception, msg:
		print msg
		return -1


if __name__ == "__main__":
   sys.exit(main()) 
