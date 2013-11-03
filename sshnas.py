
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


def do_migration(host):
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

    	print " [-] %s - Starting migration" % host.rstrip()
	outfile.write(" [-] %s - Starting migration\n" %host.rstrip())
	try:
		conn.execute('wri')              
        	outfile.write(" [-] %s - Wri complete\n" % host.rstrip())
		conn.execute('wri')
		conn.execute('reload in 15 \r')
		outfile.write(" [-] %s - Reload-in command complete\n" % host.rstrip())
        	conn.execute('conf t')
        	conn.execute('int tun 0')
        	conn.execute('shut')
		outfile.write(" [-] %s - Tunnel Shut complete\n" % host.rstrip())
		#print conn.response
        	conn.send('exit\r')
		print "[**] %s - Migration complete" % host.rstrip()
        	outfile.write("[**] %s - Migration complete\n" % host.rstrip()) 
	except:
		print "[!] %s - Error: did not finish migration" % host.rstrip()
		outfile.write("[!] %s - Error: did not finish migration\n" % host.rstrip())

def do_cancel(host):
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

	print " [-] %s - Cancelling reload" % host.rstrip()
	outfile.write(" [-] %s - Cancelling reload\n" % host.rstrip())
	try:
		conn.execute('reload cancel')
		outfile.write("[**] %s - Reload cancelled\n" % host.rstrip())
		print "[**] %s - Reload cancelled" % host.rstrip()
		conn.send('exit\r')
	except:
		print "[!] %s - Error: reload cancel did not finish" % host.rstrip()
		outfile.write("[!] %s - Error: reload cancel did not finish\n" % host.rstrip())

def worker(queue, option):
	queue_full = True
	while queue_full:
		try:
			host = queue.get(False)
			if option == 'm':
				do_migration(host)
			elif option == 'c':
				do_cancel(host)
			else:
				print "[X] Invalid option for thread worker"
				outfile.write("[X] Invalid option for thread worker")
		except Queue.Empty:
            		queue_full = False
# Main function
def main(threads,logfile,hosts_file,commands,username,password):
	global outfile
	hosts = open(hosts_file) 
	outfile = open(logfile,'w')
	account = Account(username, password)
	option = raw_input("migrate (m) or cancel reloads (c): ")
 
	if option == 'm':
		print "\nStarting migrations..."
		outfile.write("\nStarting migrations...\n")
		q = Queue.Queue()
		for host in hosts:
			q.put(host)
	
		threads = []
		thread_count = 10
		for i in range(thread_count):
    			t = threading.Thread(target=worker, args = (q,option,))
    			threads.append(t)
		# Start all threads
		[x.start() for x in threads]
		# Wait for all threads to finish before moving on
		[x.join() for x in threads]
	
	
		print ""
		cancel = raw_input("Would you like to cancel the reloads? ")
		if cancel == 'y':
			hosts = open(sys.argv[1])
			print "\nCancelling reloads..."
			outfile.write("\nCancelling reloads...\n")
			q = Queue.Queue()
			for host in hosts:
				q.put(host)
			threads = []
			thread_count = 10
			for i in range(thread_count):
                		t = threading.Thread(target=worker, args = (q,'c',))
        			threads.append(t)        	

			# Start all threads
        		[x.start() for x in threads]
        		# Wait for all threads to finish before moving on
        		[x.join() for x in threads]
	
		else:
			print "Migration complete"

	elif option == 'c':
		hosts = open(sys.argv[1])
        	print "\nCancelling reloads..."
		outfile.write("\nCancelling reloads...\n")
        	q = Queue.Queue()
		for host in hosts:
			q.put(host)
        	
		threads = []
		thread_count = 10
		for i in range(thread_count):
        		t = threading.Thread(target=worker, args = (q,option,))
                	threads.append(t)

		# Start all threads
        	[x.start() for x in threads]
        	# Wait for all threads to finish before moving on
        	[x.join() for x in threads]	
	else:
		print "[!] Not a valid option"

	print ""


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
