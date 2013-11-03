
import sys
import Exscript
import threading
import Queue
import argparse

from Exscript.util.start import start
from Exscript.util.interact import read_login
from Exscript.protocols import SSH2
from Exscript import Host, Account
from Exscript.util.file  import get_hosts_from_file
from Exscript.util.start import quickstart
from optparse import OptionParser


def do_commands(host,commands_file,account):
	try:
		commands=open(commands_file)
	except:
		print "[!] %s - Error opening commands file" %host.rstrip()
		outfile.write("[!] %s - Error opening commands file" %host.rstrip())

	try:
		print "[*] %s - Connecting" % host.rstrip()
        	outfile.write("[*] %s - Connecting\n" % host.rstrip())
        	conn = SSH2(timeout=10)
        	conn.connect(host.rstrip())
        	conn.login(account)
	except:
        	print "[!] %s - Error connecting for migration" %host.rstrip()
                outfile.write("[!] %s - Error connecting for migration\n" %host.rstrip())
		return

    	print " [-] %s - Starting commands" % host.rstrip()
	outfile.write(" [-] %s - Starting commands\n" %host.rstrip())
	for command in commands:
		print "[D] - %s" % command
		try:
			conn.execute(command)              
        	except:
			print "[!] %s - Error: did not finish command %s" % (host.rstrip(),command)
               		outfile.write("[!] %s - Error: did not finish command %s\n" % (host.rstrip(), command))
		outfile.write(" [-] %s - %s complete\n" % (host.rstrip(),command))
	print "[**] %s - Commands complete" % host.rstrip()
        outfile.write("[**] %s - Commands complete\n" % host.rstrip()) 
	conn.close()

# Worker function for threads
def worker(queue, commands_file, account):
	queue_full = True
	while queue_full:
		try:
			host = queue.get(False)
			do_commands(host,commands_file,account)
		except Queue.Empty:
            		queue_full = False

# Main function
def main(thread_count,logfile,hosts_file,commands_file,username,password):
	global outfile
	hosts = open(hosts_file) 
	outfile = open(logfile,'w')
	commands = open(commands_file)
	account = Account(username, password)
	
	#option = raw_input("migrate (m) or cancel reloads (c): ") 
	print "\nStarting sshNAS..."
	outfile.write("\nStarting sshNAS...\n")
	q = Queue.Queue()
	for host in hosts:
		q.put(host)
	
	threads = []
	for i in range(thread_count):
    		t = threading.Thread(target=worker, args=(q,commands_file,account,))
    		threads.append(t)
	# Start all threads
	[x.start() for x in threads]
	# Wait for all threads to finish before moving on
	[x.join() for x in threads]
	
	print "\nsshNAS complete!"

# Start	here
if __name__ == "__main__":		
	parser = argparse.ArgumentParser(version="%prog 1.0",description="A multi-threaded SSH network automation script")
        parser.add_argument('hosts', help='Hosts file', metavar='HOSTS_FILE')
	parser.add_argument('commands', help='Commands file', metavar='COMMANDS_FILE')
        parser.add_argument("-l", "--log-file", dest='logfile', help="logfile name", metavar="LOGFILE", default="sshnas.log")
	parser.add_argument("-t", "--threads", dest='threads', help="number of threads (1-100)", type=int, metavar='THREADS', default=10)
	parser.add_argument("-u", "--username", dest='username', help='Username for SSH login', metavar='USERNAME', default='admin')
	parser.add_argument("-p", "--password", dest='password', help='Password for SSH login', metavar='PASSWORD', default='admin')
	args = parser.parse_args()
	main(args.threads,args.logfile,args.hosts,args.commands,args.username,args.password)
