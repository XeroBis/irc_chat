import sys
import socket
import threading


class Server:
    def __init__(self, port, ports):
        self.port = int(port)
        self.host = '127.0.0.1'
        self.servers = []
        self.clients = {}
        self.clients_others = {}
        self.canaux = {}
        self.away = {}
        self.connect_to_serv(ports)
        self.start_server()

    def connect_to_serv(self, ports):
        for port in eval(ports):
            try:
                serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.servers.append(serv_socket)
                serv_socket.connect((self.host, port))
                serv_socket.send("$serveur".encode('utf-8'))
                t = threading.Thread(
                    target=self.handle_server, args=(serv_socket,))
                t.start()
            except Exception as e:
                print(e)

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        print(f"Attente de connexion sur {self.host}:{self.port}...")
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()

                username = client_socket.recv(1024).decode('utf-8')
                if "$serveur" in username:
                    print(f"Connexion établie avec serveur d'adresse {client_address}")
                    self.servers.append(client_socket)
                    t = threading.Thread(
                        target=self.handle_server, args=(client_socket,))
                    t.start()
                else:
                    print(f"Connexion établie avec {
                          username} d'adresse : {client_address}")
                    self.clients[username] = client_socket
                    t = threading.Thread(
                        target=self.handle_client, args=(client_socket, username))
                    t.start()

        except Exception as e:
            print(f"Erreur: {e}")

        finally:
            print("Serveur fermé")
            self.server_socket.close()

    def handle_server(self, socket):
        print("serveur :", socket)
        try:
            while True:
                message = socket.recv(1024).decode('utf-8')
                username = message.split(":")[0]
                msg = message[len(username) + 2:]

                print("message serveur recu : ", message)
                print("username deciphered:", username, ".")
                print("msg deciphered:", msg, ".")
                if username not in self.clients_others:
                    self.clients_others[username] = socket
                self.handle_server_message(username, msg)

        except Exception as e:
            print(e)

        return 0

    def handle_server_message(self, username, message):
        """
        """
        print("HANDLE SERVER MESSAGE")
        print("msg = ",message,". FIN MSG")
        print("TAILLE MSG :", len(message))
        if message[0] == "/":
            parts = message.split(" ")
            command = parts[0][1:].lower()
            if command == "away":
                if username not in self.away:
                    self.away[username] = message[6:]
                else:
                    del self.away[username]
            elif command == "help":
                # pas de réaction a un message help recu d'un serveur
                pass
            elif command == "invite":
                nick = parts[1]
                msg = f"User {username} invite you to join canal {
                    self.get_canal_of_user(username)}"
                if nick in self.clients:
                    self.send_message(self.clients[nick], msg)
                pass
            elif command == "join":
                canal = parts[1]
                print(f"User {username} of other server joined canal {canal}")
                self.join_canal_server(username, canal)
                pass
            elif command == "list":
                # pas de réaction a un message list recu d'un serveur
                pass
            elif command == "msg":
                target = parts[1]
                message_content = f"{username} : " + " ".join(parts[2:])
                print("TARGET : ", target)
                print("CONTENT : ", message_content)
                if username not in self.away and target in self.clients:
                    if target in self.away:
                        self.send_message(
                            self.clients_others[username], f"SYSTEM : /msg {username} {target} n'est pas joignable en ce moment, message de sa part : {self.away[target]}")
                    else:
                        self.send_message(self.clients[target], "MP de "+message_content)
                elif target in self.canaux:
                    self.send_message_canal(username, target, message_content)
            elif command == "names":
                # pas de réaction a un message names recu d'un serveur
                pass
        else:
            canal = self.get_canal_of_user(username)
            if canal != None:
                self.send_message_canal_server(
                    canal, f"canal {canal} : {username} : {message}")
        return 0
    
    def handle_client(self, socket, username):
        try:
            while True:
                message = socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.handle_message(username, message)
                for sc in self.servers:
                    self.send_message(sc, f"{username} : {message}")

        # la connection est fermé
        except Exception as e:
            print(e)

        del self.clients[username]

        # Si le client était dans un canal, le retirer du canal
        for canal_name, canal_members in self.canaux.items():
            if username in canal_members:
                canal_members.remove(username)
                self.send_message_canal(
                    None, f"{username} a quitté le canal.", canal_name)

        socket.close()
        return

    def handle_message(self, username, message):
        if message[0] == "/":
            parts = message.split(" ")
            command = parts[0][1:].lower()
            if command == "away":
                if username not in self.away:
                    self.away[username] = message[6:]
                else:
                    del self.away[username]
            elif command == "help":
                response = """Liste des commandes : \n
                /away [message] \n
                /help \n
                /join <canal> [clé] \n
                /list \n
                /msg [canal|nick] message \n
                /names [channel]"""
                self.send_message(self.clients[username], response)
            elif command == "invite":
                nick = parts[1]
                canal = self.get_canal_of_user(username)
                msg = f"User {username} invite you to join canal {canal}"
                if canal is not None:
                    if nick in self.clients:
                        self.send_message(self.clients[nick], msg)
                    elif nick in self.clients_others:
                        self.send_message(self.clients_others[nick])
                else:
                    self.send_message(self.clients[username], "You are in no canal")
            elif command == "join":
                
                canal = parts[1]
                print(f"User {username} of my server joined canal {canal}")
                self.join_canal(username, canal)
                pass
            elif command == "list":
                response = f"""Liste des canaux : \n
                {self.canaux.keys()}"""
                self.send_message(self.clients[username], response)
                pass
            elif command == "msg":
                target = parts[1]
                message_content = f"{username} :" + " ".join(parts[2:])
                if target in self.clients:
                    if target in self.away:
                        self.send_message(
                            self.clients[username], f"{target} n'est pas joignable en ce moment, message de sa part : {self.away[target]}")
                    else:
                        self.send_message(
                            self.clients[target], "MP de " + message_content)
                elif target in self.canaux:
                    self.send_message_canal(username, target, f"{message_content}")
                elif target in self.clients_others:
                    self.send_message(self.clients_others[target], f"{username} : /msg {target} {" ".join(parts[2:])}")
                pass
            elif command == "names":
                if len(parts) == 1:  # il n'y a que /names
                    # on affiche donc tout
                    response = "Liste des utilisateurs : \n"
                    for canal in self.canaux:
                        response += f"   canal {canal} : \n"
                        for user in self.canaux[canal]:
                            response += f"      {user} \n"
                else:
                    canal = parts[1]
                    response = f"Liste des utilisateurs du canal {canal} : \n"
                    for user in self.canaux[canal]:
                        response += f"{user} \n"
                
                self.send_message(self.clients[username], response)
                pass
        else:
            canal = self.get_canal_of_user(username)
            if canal != None:
                self.send_message_canal(
                    username, canal, f"{username}: {message}")
            else:
                print("ici")
                self.send_message(self.clients[username], "You are in no canal.")

    def get_canal_of_user(self, username):
        for canal in self.canaux:
            if username in self.canaux[canal]:
                return canal

        return None

    def join_canal_server(self, username, canal):
        """
        Fonction pour qu'un user rejoigne un canal quand on recoit le message d'un autre serveur
        la différence est qu'on ne renvoit pas de message à l'utilisateur et qu'on notifie seulement les utilisateurs 
        du serveur courant
        """
        canal_of_user = self.get_canal_of_user(username)
        if canal_of_user == canal:
            return
        if canal_of_user != None:
            self.canaux[canal_of_user].remove(username)

        if canal not in self.canaux:
            self.canaux[canal] = [username]
        else:
            self.canaux[canal].append(username)

        self.send_message_canal_server(canal, f"{username} a rejoint le canal.")
        return 0

    def join_canal(self, username, canal):
        """
        Fonction pour rejoindre un canal quand l'user vient du serveur courant
        """
        canal_of_user = self.get_canal_of_user(username)
        if canal_of_user == canal:
            self.send_message(self.clients[username], f'You already are in canal {canal}')
            return
        if canal_of_user != None:
            self.canaux[canal_of_user].remove(username)

        if canal not in self.canaux:
            self.canaux[canal] = [username]
            self.send_message(
                self.clients[username], f"Vous avez crée et rejoint le canal {canal}.")
        else:
            self.canaux[canal].append(username)
            self.send_message(
                self.clients[username], f"Vous avez rejoint le canal {canal}.")

        self.send_message_canal(username, canal, f"{username} a rejoint le canal.")
        return 0
    
    def send_message_canal_server(self, canal, message):
        """
        Fonction pour envoyer un message sur un canal seulement au user du serveur courant
        """
        for user in self.canaux[canal]:
            if user in self.clients:
                self.send_message(self.clients[user], message)
        return 0

    def notify_join_canal(self, username, canal):
        for user in self.clients_others:
            self.send_message(self.clients_others[user], f"{username}: /join {canal}")

    def send_message_canal(self, username, canal, message):
        """
        Fonction pour envoyer un message à tous les user sur tout les serveurs sur un canal
        """
        for user in self.canaux[canal]:
            if user != username: # on n'envoit pas le message a l'utilisateur qui vient de rejoindre
                if user in self.clients:
                    self.send_message(self.clients[user], message)
        return 0

    def send_message(self, socket, message):
        """
        Fonction qui envoie le message au socket
        """
        try:
            socket.send(message.encode('utf-8'))
        except Exception as e:
            print("Exception envoie de message :", e)

def main():
    if len(sys.argv) < 2:
        print("Need server port")
        return

    port = sys.argv[1]
    if len(sys.argv) == 3:
        Server(port, sys.argv[2])
    else:
        Server(port, "[]")


if __name__ == "__main__":
    main()
