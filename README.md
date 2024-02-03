# IRC Chat

This project consists of a simple Internet Relay Chat (IRC) application implemented in Python. The application includes a server (server.py) and a client (irc.py) using the tkinter library for the graphical user interface.

## Features

- Supports multiple chat channels.
- Private messaging between users.
- Away status for users.
- Joining and creating channels with optional passwords.
- Invite functionality to invite users to a channel.

## Known bugs
- When server is launched later, the user connecting to that server does not see what others users have done on the network.

## Single Server

to launch a server :

python server.py 123

To launch a client :

python irc.py username 123

## Multi Server

to launch a first server :

python server.py 123

to launch a second server :

python \server.py 456 [123]

to launch multiple clients :

python irc.py username_1 123

python irc.py username_2 456
