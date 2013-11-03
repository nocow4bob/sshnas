
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


def do_commands(host,commands_file,account):
	global error_count
	global success_count
	error = 0
	try:
		commands=open(commands_file)
	except:
		print "[!] %s - Error opening commands file" %host.rstrip()
		outfile.write("[!] %s - Error opening commands file" %host.rstrip())
		return
	try:
		#print "[*] %s - Connecting" % host.rstrip()
        	outfile.write("[*] %s - Connecting\n" % host.rstrip())
        	conn = SSH2(timeout=10)
        	conn.connect(host.rstrip())
        	conn.login(account)
	except:
        	#print "[!] %s - Error connecting" %host.rstrip()
                outfile.write("[!] %s - Error connecting\n" %host.rstrip())
		error_count = error_count + 1
		return

    	#print " [-] %s - Starting commands" % host.rstrip()
	outfile.write(" [-] %s - Starting commands\n" %host.rstrip())
	for command in commands:
		try:
			conn.execute(command)              
        		#print conn.response
		except:
			#print "[!] %s - Error: did not finish command %s" % (host.rstrip(),command.rstrip())
               		outfile.write("[!] %s - Error: did not finish command %s\n" % (host.rstrip(), command.rstrip()))
			error = 1
		outfile.write(" [-] %s - %s complete\n" % (host.rstrip(),command.rstrip()))
	if error == 1:
		error_count = error_count + 1
	else:
		 success_count = success_count + 1
	conn.send('exit\r')
	#print "[**] %s - Commands complete" % host.rstrip()
        outfile.write("[**] %s - Commands complete\n" % host.rstrip()) 

# Worker function for threads
def worker(queue, commands_file, account, thread_count):
	global count
	global host_count
	global error_count
	global success_count
	queue_full = True
	while queue_full:
		try:
			host = queue.get(False)
			do_commands(host,commands_file,account)
			count = count + 1
			if count == 1:
                		print "[*] Progress (%s\%s)" % (count,host_count)
			elif count % thread_count == 0:
				print "[*] Progress (%s\%s)" % (count,host_count)
				print "\tSuccessful (%s\%s)" % (success_count,host_count)
				print "\tFailed (%s\%s)" % (error_count,host_count)
		except Queue.Empty:
            		queue_full = False

# Main function
def main(thread_count,logfile,hosts_file,commands_file,username,password):
	global outfile
	global count
	global host_count
	global error_count
	global success_count
	
	count = 0
	host_count = 0
	error_count = 0	
	success_count = 0
	hosts = open(hosts_file) 
	outfile = open(logfile,'w')
	commands = open(commands_file)
	account = Account(username, password)
	
	print "[*] Starting sshNAS..."
	outfile.write("Starting sshNAS...\n")
	q = Queue.Queue()
	for host in hosts:
		q.put(host)
		host_count = host_count + 1
	
	threads = []
	for i in range(thread_count):
    		t = threading.Thread(target=worker, args=(q,commands_file,account,thread_count,))
    		threads.append(t)
	
	# Start all threads
	[x.start() for x in threads]
	# Wait for all threads to finish before moving on
	[x.join() for x in threads]
	
	print "[*] Completed (%s\%s)\n\tSuccessful (%s\%s)\n\tFailed (%s\%s)" % (count,host_count, success_count,host_count,error_count,host_count)
	print "[*] sshNAS complete!"

# Start	here
if __name__ == "__main__":		
	parser = argparse.ArgumentParser(version="%prog 1.0",description="A multi-threaded SSH network automation script")
        parser.add_argument('hosts', help='Hosts file (one host per line)', metavar='HOSTS_FILE')
	parser.add_argument('commands', help='Commands file (one command per line)', metavar='COMMANDS_FILE')
        parser.add_argument("-l", "--log-file", dest='logfile', help="logfile name", metavar="LOGFILE", default="sshnas.log")
	parser.add_argument("-t", "--threads", dest='threads', help="number of threads (1-100)", type=int, metavar='THREADS', default=10)
	parser.add_argument("-u", "--username", dest='username', help='Username for SSH login', metavar='USERNAME', default='admin')
	parser.add_argument("-p", "--password", dest='password', help='Password for SSH login', metavar='PASSWORD', default='admin')
	args = parser.parse_args()
	main(args.threads,args.logfile,args.hosts,args.commands,args.username,args.password)
