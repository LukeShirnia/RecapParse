#!/usr/local/bin/python env
# Author:       Luke Shirnia

from sys import argv
from optparse import OptionParser
import re
import sys
import os.path
import os


class bcolors:
	'''
	Class used for colour formatting
	'''
	HEADER = '\033[95m'
	RED = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	PURPLE = '\033[35m'
	LIGHTRED = '\033[91m'
	CYAN = '\033[36m'
	UNDERLINE = '\033[4m'


def find_recap_path():
	'''
	Find out if recap logs are on the system by checking directory path
	'''
	RecapLogs = "/var/log/recap"
	if os.path.isdir(RecapLogs):
		return True
	else:
		return False


def check_file_exists(file_to_check):
	'''
	User may enter a file path, we need to check it exists before continuing
	'''
	if os.path.exists(file_to_check):
		return True
	else:
		print "File does not exist, please try again"
		return False


def openfile(filename, normal_file):
	'''
	Check if input file is a compressed or regular file
	'''
	if normal_file:
		return open(filename, "r")
	elif filename.endswith('.gz'):
        	return gzip.open(filename, "r")
	else:
		return open(filename, "r")


def find_rss_column(line): 
	'''
	This check finds the correct column for RSS
	Each distribution and version may log differently, this allows to catch all, for Linux OS compatibility
	'''
	for i, word in enumerate(line):
		if word.lower() == "rss":
			column = int(i+1)
			return column

def find_command_column(line):
	'''
        This check finds the correct column for command column
        Each distribution and version may log differently, this allows to catch all, for Linux OS compatibility
        '''
        for i, word in enumerate(line):
                if word.lower() == "command":
                        column = int(i+1)
                        return column


def save_values(line, rss_column_number, command_column_number):
	'''
	This function processes each line (when record = True) and saves the rss value and process name .eg (51200, apache)
	'''
        value = line.split()[-1:]
        if len(value) == 1:
                cols = line.split()
		if "\_" in line:
			string = cols[rss_column_number-1], line.split("\_ ")[1]
			#print "\_", string
		else:
			service_name = cols[command_column_number-1:]
			service_name = ' '.join(service_name)
	                #string = cols[rss_column_number-1], cols[command_column_number-1:]
	                string = cols[rss_column_number-1], service_name
			#print "no ", string
	return string


def strip_rss(line, rss_column_number):
	'''
	Obtain the RSS value of a service from the line
	'''
	line = line.split()
	value = int(line[rss_column_number-1])
	return value


def strip_line(line):
	'''
	Stripping all non required characters from the line so not to interfere with line.split()
	'''
	for ch in ["[","]","}","{","'", "(",")"]:
		if ch in line:
			line = line.replace(ch,"")
	return line


def find_unique_services(list_of_values):
	'''
	Finding the unique list of killed services (excludes the duplicated, eg apache, apache, apache is just apache)
	'''
        new_list = []
        for i in list_of_values:
                new_list_value = i[1]
                new_list.append(new_list_value)
        new_list = list(set(new_list))
	return new_list


def add_rss_for_processes(unique, list_of_values):
	'''
	Adding the RSS value of each service
	'''
        values_to_add = []
        total_service_usage = []
        del total_service_usage[:]
        for i in unique:
                del values_to_add[:]
                for x in list_of_values:
                        if i == x[1]:
                                number = int(x[0])
                                values_to_add.append(number)
                added_values = ( sum(values_to_add) * 4 ) / 1024 # work out rss in MB
                string = i, added_values
                total_service_usage.append(string)
	return total_service_usage



def option_ps_r(ps_file, counter):
	'''
	Function for option -p, --ps	
	'''
	counter =+ 1
	list_of_values = []
	total_rss_ps = []
	del total_rss_ps[:]
	del list_of_values[:]
	record = False
	if "ps" in ps_file:
		normal_file = (False if ps_file.endswith('.gz') else True)
		inLogFile = openfile(ps_file, normal_file)
		for line in inLogFile:
			line = strip_line(line)
			line = line.strip()
			if "user " in line.lower() and record == False:
				rss_column_number = find_rss_column(line.split()) # find rss column in the file
				command_column_number = find_command_column(line.split())
				record = True
			elif record == True:
				#list_of_values[counter].append(line, rss_column_number)				
				list_of_values.append(save_values(line, rss_column_number, command_column_number))
				rss_value = strip_rss(line, rss_column_number)
				total_rss_ps.append(rss_value)
			else:
				pass
	else:
		print "This does not appear to be a ps log"
	list_of_values = filter(None, list_of_values)
	unique = find_unique_services(list_of_values)
	ps_log_service_rss_total = add_rss_for_processes(unique, list_of_values)
	ps_log_service_rss_total = sorted(ps_log_service_rss_total,key=lambda x: x[1], reverse=True)
	print_ps_output(ps_log_service_rss_total)


def print_ps_output(service_list):
	top_15 = 0
	print 
	for x in service_list:
		service = x[0]
		size = x[1]
		top_15 += 1
		if top_15 <= int(15):
	 		print "{0:<30}  {1} MB ".format(service[:30], size)
	print ""


def main():
	'''
	Usage and help overview
	Option pasring
	'''
	parser = OptionParser(usage='usage: %prog [option]')
	resource = ['--ps']
	parser.add_option("--ps",
			dest="file",
			metavar="FILE",
			help="Summary of specified process log")
	parser.add_option("-p", "--process",
                        dest="file",
                        metavar="FILE",
                        help="Find the size of specified process in ps_ log")
	(options, args) = parser.parse_args()
	if len(sys.argv) > 1:
		selected_option = sys.argv[1:]
		selected_option = selected_option[0]
	if len(sys.argv) == 1: 			# Default options, no added arguments
		parser.print_help()
	elif len(sys.argv) == 3:
		if selected_option in resource and check_file_exists(options.file):
			counter = 0 # this is added in case the script will eventually check a whole hour/date range, counters can increase
			resource_log = options.file
			option_ps_r(resource_log, counter)
	else:
	
		print "Do default"


if __name__ == '__main__':
	try:
		if find_recap_path():
			main()
		else:
			print "Recap Not Installed"
	except(EOFError, KeyboardInterrupt):
		print
		Isys.exit(0)
