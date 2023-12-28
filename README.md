# irc_chat

Simple local chat between multiple terminal using the socket package

## First version

to launch a server :

python .\1_version\server.py 123

To launch a client :

python .\1_version\irc.py username 123

## Second version

to launch a first server :

python .\2_version\server.py 123

to launch a second server :

python .\2_version\server.py 456 [123]

to launch multiple clients :

python .\2_version\irc.py username_1 123

python .\2_version\irc.py username_2 456
