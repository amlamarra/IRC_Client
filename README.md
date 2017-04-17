# IRC Client
This is an IRC client I'm writing in Python.

------------------------------------------------------------                                                                                                                               
List of commands (not case sensitive):                                                                                                                                                     
        /SERVER (add|delete|list) [<name> <ip> <port>]                                                                                                                                     
                Name, IP, and port are required if the add option is used                                                                                                                  
                Name is required if the delete option is used                                                                                                                              
        /SET <server name>.(nick|username|realname) <value>                                                                                                                                
                You must have a nick and username set before connecting                                                                                                                    
                Example: /set freenode.nick testuser                                                                                                                                       
        /CONNECT <name> | Connect to the saved server                                                                                                                                      
        /DISCONNECT | Disconnect from the current server                                                                                                                                   
        /JOIN #<channel name> | Join a channel                                                                                                                                             
        /NICK <new nick> | Changes your nick                                                                                                                                               
                Note: In order to change your username, you'll need to log out,                                                                                                            
                use the /SET command, and log back in                                                                                                                                      
        /NAMES [#<channel name>]                                                                                                                                                           
                List all visible channels & users if no arguments are given                                                                                                                
                If channel name is given, list all visible names in that channel                                                                                                           
        /QUIT [:<message>] | Closes the connection & exits the program                                                                                                                     
        /EXIT [:<message>] | Same as /QUIT                                                                                                                                                 
        /HELP | Display this help dialog                                                                                                                                                   
------------------------------------------------------------                                                                                                                               
While in a channel:                                                                                                                                                                        
        /NAMES | List all visible nicknames in the current channel                                                                                                                         
        /PART [<part message>] | Leaves the current channel                                                                                                                                
        /PRIVMSG <nick> :<message> | Send a private message to a user                                                                                                                      
------------------------------------------------------------