
import os
import time
from mod_python import apache
directory = os.path.dirname(__file__) 
dist_crawl = apache.import_module('main_handler', path=[directory])
#import dist_crawl.main_handler
def do_more_stuff(req, links_str):
	links_with_depth = links_str.split("|||");
	links = []
	for each in links_with_depth:
		if each != "":
			each_link_and_depth = each.split("||")
			apache.log_error(str(each_link_and_depth))
			links.append(each_link_and_depth);
	apache.log_error(links_str);
	#apache.log_error(str(len(links_str)));
	#apache.log_error(str(links))
	result = dist_crawl.start_processing([], links, 0);
	map_res = result[0]
	result.pop(0);
	map_to_arr = []
	for each in map_res:
		map_to_arr.append([each] + map_res[each])
	result.insert(0, map_to_arr);
	more_results = result[0]
	ret_html = ""
	for res in more_results:
		ret_html = ret_html + "<tr>"
		for col in res:
			ret_html = ret_html + "<td>" + str(col) + "</td>"
		ret_html = ret_html + "</tr>"

	return ret_html

def html_out_of_result(result):
	html_table = "<table id='results_table' width='90%'>"
	actual_results = result[0]
	need_to_process = result[1]
	# [sts, xframe, httponly, securecookie, nonce]

	html_table = html_table + "<tr><td>URL</td><td>HTTP STP</td><td>X-Frame Options</td><td>HTTPOnly</td><td>Secure-Cookie</td><td>CSP</td><td>Nonce in webform</td><td>Depth</td></tr>"
	for res in actual_results:
		html_table = html_table + "<tr>"
		for col in res:
			html_table = html_table + "<td>" + str(col) + "</td>"
		html_table = html_table + "</tr>"
	html_table = html_table + "</table>"
	
	html_div = "<div id='remaining_links' style='visibility: hidden'>"
	for x in need_to_process:
		html_div = html_div + str(x[0]) + "||" + str(x[1]) + "|||"
	html_div = html_div + "</div>"
	return html_table + html_div;

def do_stuff(req, link, number):
	result = dist_crawl.start_processing([[link, 0]], [], int(number));
	map_res = result[0]
	if len(map_res) == 0:
		return ""
	result.pop(0);
	map_to_arr = []
	for each in map_res:
		map_to_arr.append([each] + map_res[each])
	result.insert(0, map_to_arr);
	return html_out_of_result(result)
