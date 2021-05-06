#!/usr/bin/env python3
import subprocess
import time
import threading
import socket
import os

SERVERS_DIR = "Servers/"
SERVER_TESTED = "ChatamuCentral"
CLIENTS_DIR = "Clients/"
DEFAULT_PORT = 12345

def run_command( command , file_to_stdin=""):
    """ Runs a command on the shell.
	Returns the process that is doing it """
    return subprocess.run( command, stdout=subprocess.PIPE)

def get_text_from_file( filename ):
	with open( filename , 'r') as f:
		lines = f.read()
	return lines	

############## Server ############################################
def launchChatamuServer():
	""" Return the PID of the process running the server. """
	server_path= SERVERS_DIR + SERVER_TESTED +"/" + SERVER_TESTED
	server_cmd=["./pm_daemonize.sh", "java", server_path, str(DEFAULT_PORT)]
	daemonOutput = run_command(server_cmd)
	server_pid = daemonOutput.stdout.decode()[:-1]
	return server_pid

def killChatamuServer( server_pid ):
	run_command(["kill", str(server_pid)])

############### Clients ############################################
def testWithSimpleClient():
	time.sleep(3) # <- Used so that jak joins in the middle when Nc client talks
	# Get client text for test files:
	lines = get_text_from_file( '../../Tests/txt_sources/SimpleClient.txt' )
	#Connect the client:
	client_cmd = ["./client.sh", "SimpleClient"]
	client = subprocess.Popen( client_cmd,stdout= subprocess.PIPE,
	               stderr = subprocess.PIPE, stdin = subprocess.PIPE)
	#Send the text of the client:
	client_output = client.communicate( lines.encode() )
	client.kill()

def testWithNc():
	time.sleep(1)
	# Get client text for test files:
	lines = get_text_from_file( '../../Tests/txt_sources/nc.txt' )
	# Uses python socket's but can be assimilated to an NC client
	# this is done so that i can control the rate at which I send data.
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(("localhost", DEFAULT_PORT))
	# Send a line every seconds and close wrinting channel after:
	for line in lines.split('\n'):
		s.send( (line+'\n').encode() )
		time.sleep(1)
	s.shutdown(socket.SHUT_WR)
	## Get nc stdout:
	printBanner( "Nc client stdout",
		         " [Expected]: We see JAK's activity:  \n"+ \
		         "    1) JAK joins the chat \n"+ \
		         "    2) JAK speaks, then immediatly quit.\n"+ \
		         "    3) We see that JAK left.\n"+ \
		         "    4) Our last message is an error (\"MESSAGE\" protocol not respected) the server signal it to us." )
	while True:
		data = s.recv(4096)
		if not data:
			break
		print( data.decode())
	#Close the socket
	s.close()

def launchClientsWithThreads():
	""" Launch SimpleClient and Nc client with threads,
	so that they can see each other as they talk in the same time
	on the server """
	simple_client_T = threading.Thread( target=testWithSimpleClient )
	nc_client_T = threading.Thread( target= testWithNc )
	simple_client_T.start()
	nc_client_T.start()
	simple_client_T.join()
	nc_client_T.join()


############### Main ############################################
def main():
	try:
	# Go to src/ directory
		os.chdir("../src/")
	# Launch Chatamu server
		server_pid = launchChatamuServer()
	##Get server stderr first:
		printBanner("SERVER stderr" , 
			        " [Expected]: ZERO \"Error [MESSAGE]\".\n"+ \
			        "  The server should not encounter any error!" )
		print("    [This part of the test takes some time, please wait ...]")
    #Launch Clients:
		os.chdir("Clients/")
		launchClientsWithThreads()
		os.chdir("../")
	## Get server stdout:
		printBanner("Server stdout",
			" [Expected]: The discussion between the two clients: it's the Server's STDOUT.\n"+
		    "     This output is saved in \"server.log\":\n"+\
		    "     This file was generated by a script that you gave us: \"pm_daemonize.sh\" .")
		show_server_log()
	finally:
	# Tests done: close the server (kill it's pid)
		killChatamuServer( server_pid )

############## Print data ##########################################
def PWD():
	pwd = run_command( "pwd" )
	print(pwd.stdout.decode())

def printBanner( banner_title, banner_content ):
	time.sleep(1) #<- used to separate the time where output is printed. (can be removed if you want)
	print("\n"+"#"*20+" "+banner_title+" "+"#"*23+"\n"+\
		  banner_content +\
		  "\n"+"#"*60)
	time.sleep(1) #<- used to separate the time where output is printed. (can be removed if you want)

def show_server_log():
	server_log = run_command( ['cat','server.log'] )
	print( server_log.stdout.decode() )

if __name__ == '__main__':
	main()
