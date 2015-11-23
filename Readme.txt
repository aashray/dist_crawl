# dist_crawl

System security Fall 2015 Project.

To install beautiful soup:
	pip install beautifulsoup4

To install mod python and apache:
	sudo apt-get install apache2 apache2.2-common apache2-mpm-prefork apache2-utils libexpat1 ssl-cert
  	sudo apt-get install libapache2-mod-python

Add the following lines to /etc/apache2/apache2.conf
	<Directory /var/www/html/syssec/>
	        AddHandler mod_python .py
	        PythonHandler mod_python.publisher
	        PythonDebug On
	</Directory>
	

Start the apache server
	sudo /etc/init.d/apache2 restart

Ensure that your html page is present under /var/www/html/.

Start the WebUI by going to your html page. Eg: localhost/syssec/myWebPage.html

Add the helper nodes by creating a /tmp/nodes.conf file.
nodes.conf: contains <ip>:<port> of each node where node-handler.py is running.

Start the node_handler.py at each node with the specified port number in each node.

Provide the domain URL and the number of links to crawl in the WebUI and submit. 

The results are displayed on the Web UI after the processing is complete. 
