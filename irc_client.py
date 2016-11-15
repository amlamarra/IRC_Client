#!/usr/bin/python3
import socket
import threading
import curses
import pickle
import os.path
from string import printable

# Defining constants and globals
PRINTABLE = [ord(x) for x in printable]
BUFF_SIZE = 10 # Command buffer size
sockets = []
servers = {}
lines = []
txt = []

class ServerInfo():
	"Used to store server and user info"
	
	def __init__(self, name, ip, port):
		self.name = name
		self.ip = ip
		self.port = port
		self.addr = (ip, port)
		self.nick = ""
		self.username = ""
		self.realname = ""
		

# Display whatever string is passed to it
def output(stdscr, msg):
	Y, X = stdscr.getyx()
	max_lines = stdscr.getmaxyx()[0] - 3
	
	# Scrolling (if necessary)
	if len(lines) > max_lines:
		del lines[0]
		stdscr.clear()
		for i, line in enumerate(lines):
			stdscr.addstr(i, 0, line)
		# Redraw the input line
		stdscr.addstr(Y, 2, "".join(txt))
		stdscr.move(Y, X)

	stdscr.addstr(len(lines), 0, msg)
	lines.append(msg)
	stdscr.move(Y, X) # Move the cursor back to the start position
	stdscr.refresh()

# Displays the help listing
def help(stdscr):
	output(stdscr, "------------------------------------------------------------")
	output(stdscr, "List of commands (not case sensitive):")
	output(stdscr, "\t/SERVER (add|delete|list) [<name> <ip> <port>]")
	output(stdscr, "\t\tName, IP, and port are required if the add option is used")
	output(stdscr, "\t\tName is required if the delete option is used")
	output(stdscr, "\t/SET <server name>.(nick|username|realname) <value>")
	output(stdscr, "\t\tYou must have a nick and username set before connecting")
	output(stdscr, "\t\tExample: /set freenode.nick testuser")
	output(stdscr, "\t/CONNECT <name> | Connect to the saved server")
	output(stdscr, "\t/DISCONNECT | Disconnect from the current server")
	output(stdscr, "\t/JOIN #<channel name> | Join a channel")
	output(stdscr, "\t/NICK <new nick> | Changes your nick")
	output(stdscr, "\t\tNote: In order to change your username, you'll need to log out,")
	output(stdscr, "\t\tuse the /SET command, and log back in")
	output(stdscr, "\t/NAMES [#<channel name>]")
	output(stdscr, "\t\tList all visible channels & users if no arguments are given")
	output(stdscr, "\t\tIf channel name is given, list all visible names in that channel")
	output(stdscr, "\t/QUIT | Closes the connection & exits the program")
	output(stdscr, "\t/EXIT | Same as /QUIT")
	output(stdscr, "\t/HELP | Display this help dialog")
	output(stdscr, "------------------------------------------------------------")
	output(stdscr, "While in a channel:")
	output(stdscr, "\t/NAMES | List all visible nicknames in the current channel")
	output(stdscr, "\t/PART [<part message>] | Leaves the current channel")
	output(stdscr, "\t/PRIVMSG <nick> :<message> | Send a private message to a user")
	output(stdscr, "------------------------------------------------------------")

# Listens for messages from the server
def listen(stdscr):
	while True:
		messages = sockets[0].recv(4096).decode().split("\r\n")
		for message in messages:
			if message != "": # Dismiss empty lines
				# Trim the fat
				message = message.split(" ")
				if message[0] != "PING" and message[1][0].isdigit():
					message = " ".join(message[2:])
				elif message[0] != "PING":
					message = " ".join(message[1:])
				else:
					message = " ".join(message)
				output(stdscr, message)
				
				# Automatically reply to PING messages to prevent being disconnected
				if message.split(" ")[0] == "PING":
					pong = "PONG" + message[4:]
					sockets[0].sendall(pong.encode())
					output(stdscr, pong)

# Connects to the server
def connect(stdscr, srv_name):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(10)
	try:
		sock.connect(servers[srv_name].addr)
	except socket.error as exc:
		output(stdscr, "Connection error: {}".format(exc))
		return False
	sock.settimeout(None)
	sockets.append(sock)
	sockets[0].sendall("NICK {}\r\n".format(servers[srv_name].nick).encode())
	sockets[0].sendall("USER {} 0 * :{}\r\n".format(servers[srv_name].username,
	                   servers[srv_name].realname).encode())
	t = threading.Thread(target=listen,args=(stdscr,))
	t.daemon = True
	t.start()
	
	return True

# Handles commands specified by the user
def commands(stdscr, message, connected, inchannel, send):
	param = ""
	text = ""
	msg = message[1:]
	params = len(msg.split(" ")) - 1

	if len(msg.split(":")) > 1:
		text = " :" + msg.split(":")[1]

	if params > 0:
		param = msg.split(" ")[1].lower()

	command = msg.split(" ")[0].upper()

	if command == "SERVER" and params:
		if param == "list":
			for server in servers:
				output(stdscr, "Server Name: {}  |  Address: {}"
					   .format(server, servers[server].addr))
				output(stdscr, "       Nick: {}".format(servers[server].nick))
				output(stdscr, "   Username: {}".format(servers[server].username))
				output(stdscr, "   Realname: {}".format(servers[server].realname))
				output(stdscr, "")
		elif param == "add" and params >= 4:
			name = msg.split(" ")[2]
			if name in servers:
				output(stdscr, "That server name already exists.")
			else:
				ip = msg.split(" ")[3]
				port = int(msg.split(" ")[4])
				server = ServerInfo(name, ip, port)
				servers[name] = server
				with open("servers.db", "wb") as f: # Save to file
					pickle.dump(servers, f)
		elif param == "add" and params < 4:
			output(stdscr, "Adding a server requires 3 parameters:")
			output(stdscr, "\t/SERVER add <server name> <ip> <port>")
		elif param == "delete" and params > 1:
			name = msg.split(" ")[2]
			if name in servers:
				del servers[name]
				with open("servers.db", "wb") as f:
					pickle.dump(servers, f)
				output(stdscr, "Server '{}' has been deleted.".format(name))
			else:
				output(stdscr, "Server name does not exist.")
		elif param == "delete" and params < 2:
			output(stdscr, "Specify the server name to delete it.")

	elif command == "SET":
		# I'd really like to clean this place up...
		if params < 2 or "." not in msg.split(" ")[1]:
			output(stdscr, "Command usage: /SET <server name>."
			               "(nick|username|realname) <value>")
		else:
			name = msg.split(" ")[1].split(".")[0].lower()
			if name not in servers:
				output(stdscr, "You must specify one of your saved servers")
				output(stdscr, "Use '/SERVER list' to see all saved servers")
			else:
				attr = msg.split(" ")[1].split(".")[1].lower()
				value = " ".join(msg.split(" ")[2:])
				if attr == "nick" or attr == "username" or attr == "realname":
					if attr != "realname":
						value = value.split(" ")[0]
					setattr(servers[name], attr, value)
					with open("servers.db", "wb") as f:
						pickle.dump(servers, f)
				else:
					output(stdscr, "You must specify one of the following attributes:"
								   " (nick|username|realname)")
			 
	elif command == "CONNECT":
		if params and param in servers and not connected:
			if servers[param].nick and servers[param].username and servers[param].realname:
				connected = connect(stdscr, param)
				output(stdscr, "Socket info: {}".format(sockets[0].getpeername()))
				if not connected:
					output(stdscr, "Unable to connect to the server")
			else:
				output(stdscr, "You must set a nick and username for the server:")
				output(stdscr, "\t/SET <server name>.(nick|username|realname) <value>")
		elif param not in servers and not connected:
			output(stdscr, "You must specify the name of a saved server")
		elif connected:
			output(stdscr, "You must first disconnect from the current server.")

	elif command == "JOIN" and params:
		if connected and param[0] == "#":
			channel = param
			msg = "JOIN {}".format(channel)
			inchannel = True
			send = True
		elif connected:
			output(stdscr, "Improper channel name")
		else:
			output(stdscr, "You must be connected to a server.")

	elif command == "NICK" and params:
		if connected:
			msg = "NICK {}".format(param)
			send = True
		NICK = param

	elif command == "PART":
		if connected and inchannel:
			msg = "PART {}{}".format(channel, text)
			send = True
		elif connected and not inchannel:
			output(stdscr, "You must be in a channel to leave one.")
		inchannel = False

	elif command == "NAMES":
		# To do: Allow user to specify multiple channels
		if connected and not params:
			msg = "NAMES"
			send = True
		elif connected and params and param[0] == "#":
			msg = "NAMES {}".format(param)
			send = True
		elif connected and params and param[0] != "#":
			output(stdscr, "Invalid channel name.")
		else:
			output(stdscr, "You must first connect to a server.")

	elif command == "HELP":
		help(stdscr)

	elif command == "QUIT" or command == "EXIT":
		msg = "QUIT"
		output(stdscr, "You tried to quit, but HAHA, you can't!")
		if connected:
			send = True

	elif command == "PRIVMSG" and params > 1:
		if connected:
			msg = "PRIVMSG {}{}".format(param, text)
			send = True
		else:
			output(stdscr, "You must first connect to a server.")
			
	else:
		output(stdscr, "Invalid command or parameter...")
	
	return msg, connected, inchannel, send


def clear_prompt(stdscr, string=""):
	Ymax, Xmax = stdscr.getmaxyx()
	stdscr.move(Ymax-1, 0)
	stdscr.clrtoeol()
	# Put the nick before the prompt if connected to a server
	stdscr.addstr("> {}".format(string))


def user_input(stdscr):
	global NICK
	send = False
	inchannel = False
	connected = False
	channel = ""
	Ymax, Xmax = stdscr.getmaxyx()
	buff = [""]

	while True:
		clear_prompt(stdscr)
		Y, X = stdscr.getyx()
		eol = X
		txt = []
		bindex = 0 # Buffer Index
		
		while True:
			y, x = stdscr.getyx()
			c = stdscr.getch()
			
			if c == 10: # Pressing Enter (\r)
				bindex = 0
				buff[0] = ""
				break
			elif c == curses.KEY_BACKSPACE:
				if x > X:
					eol -= 1
					del txt[x-X-1]
					stdscr.move(y, x-1)
					stdscr.clrtoeol()
					stdscr.insstr("".join(txt[x-X-1:]))
			elif c == curses.KEY_LEFT:
				if x > X:
					stdscr.move(y, x-1)
			elif c == curses.KEY_RIGHT:
				if x < eol:
					stdscr.move(y, x+1)
			elif c == curses.KEY_UP:
				if bindex < len(buff) - 1:
					bindex += 1
					clear_prompt(stdscr, buff[bindex])
					txt = list(buff[bindex])
					Y, X = stdscr.getyx()
					eol = X
				
			#elif c == curses.KEY_DOWN:
			#	if bindex > 0:
			#		bindex -= 1
				
			elif c == curses.KEY_END:
				stdscr.move(y, eol)
			elif c == curses.KEY_HOME:
				stdscr.move(y, X)
			elif c == curses.KEY_DC: # Delete key
				if x < eol:
					eol -= 1
					del txt[x-X]
					stdscr.clrtoeol()
					stdscr.insstr("".join(txt[x-X:]))
			# Each line cannot exceed 512 characters in length, including \r\n
			elif c in PRINTABLE and len(txt) < 510:
				eol += 1
				if x < eol:
					txt.insert(x-X, chr(c))
					stdscr.insch(c)
				else:
					txt.append(chr(c))
					stdscr.addch(c)
				stdscr.move(y, (x+1))
				buff[0] = "".join(txt)
				
		message = "".join(txt)
		output(stdscr, ">>> {}".format(message))
		
		# Add to the command buffer. Remove if limit is reached.
		buff.insert(1, message)
		if len(buff) > BUFF_SIZE:
			buff.pop()
		#output(stdscr, "Buffer = {}".format(buff))
		
		if message and message[0] == "/" and len(message) > 1:
			###############################################################
			# Commands function because the indents were getting rediculous
			msg, connected, inchannel, send = commands(
				stdscr, message, connected, inchannel, send)
			###############################################################
		elif message and message[0] == "/" and len(message) == 1:
			output(stdscr, "Invalid command")
		elif message and inchannel:
			msg = "PRIVMSG {} :{}".format(channel, message)
		elif message and not inchannel:
			output(stdscr, "You need to be in a channel to send a message")
			
		if send and message and connected:
			msg += "\r\n"
			sockets[0].sendall(msg.encode())
		
		if (message.split(" ")[0].upper() == "/QUIT" or 
			message.split(" ")[0].upper() == "/EXIT"):
			break
			
		send = False # Reset the send flag
		
def main(stdscr):
	global servers
	help(stdscr) # Display the help dialog first
	
	if os.path.isfile("servers.db"):
		with open("servers.db", "rb") as f:
			servers = pickle.load(f)
			
	user_input(stdscr)
	
	if sockets:
		sockets[0].shutdown(socket.SHUT_RDWR)
		sockets[0].close()
	stdscr.erase()
	stdscr.refresh()
	del stdscr

if __name__ == "__main__":
	curses.wrapper(main)

'''
Notes on IRC:
	Initiating a connection:
		NICK <nickname>
		USER <username> <mode> :<realname>
		Examples:
			NICK elusive
			USER amlamarra 0 * :Andrew L
			USER eb 0 * :Elusive Bear
			USER elusive 8 * :Elusive Bear	# Join as invisible
	Each line from the client cannot be more than 512 characters in length
		Including CR-LF
	Channel Names:
		Strings (beginning with &, #, + or !) of length up to 50 characters (No spaces)
	Channel Messages:
		JOIN #foo
		PART #foo
		NAMES #foo (if no channel is given, all channels & nicks will be listed)
		MODE #foo *( ( "-" / "+" ) *<modes> *<modeparams> )
		TOPIC #foo :This is the topic
		LIST #foo (List channels & their topics. List all if no channel is given)
		INVITE (to be implement later)
		KICK (to be implement later)
	Sending a message
		PRIVMSG #foo :Hello there! (Sends a message to everyone in the channel)
		PRIVMSG user1 :Hello (Sends a message to the nick 'user1' in the current channel)
	Leaving:
		PART #foo :message
		QUIT :message
	Server queries and commands: (to be implemented later)
		MOTD
		LUSERS
		VERSION
		STATS
		LINKS
		TIME
		TRACE
		INFO (returns server version, when it was compiled, patchlevel, when it started, and any other misc info)
	User queries: (to be implemented later)
		WHO
		WHOIS
		WHOWAS
	Optional features:
		AWAY
		USERS
		ISON
		
Features to add:
	- Color! (colorama module?)
	- Menus & such (maybe)
	- List users in the channel on the right
	- Command buffer
Known bugs:
	- Sometimes the prompt ">" disappears
		- It happens when the buffer scrolls without the user pressing Enter
'''