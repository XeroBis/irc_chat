import sys
import socket
import threading
import logging


class Server:
    def __init__(self, port):
        self.port = int(port)
        logging.basicConfig(filename=f'server_{
                            port}.log', encoding='utf-8', level=logging.INFO)
        self.host = '127.0.0.1'
        self.clients = {}
        self.canaux = {}
        self.canaux_password = {}
        self.away = {}
        logging.debug('Server launched')
        self.start_server()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        logging.info(f"Attente de connexion sur {self.host}:{self.port}...")
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                logging.info(f"Connexion établie avec {client_address}")
                username = client_socket.recv(1024).decode('utf-8')
                self.clients[username] = client_socket
                t = threading.Thread(
                    target=self.handle_client, args=(client_socket, username))
                t.start()

        except Exception as e:
            logging.info(f"Erreur start server : {e}")

        finally:
            logging.info("Serveur fermé")
            server_socket.close()

    def handle_client(self, socket, username):
        logging.info(f"Handle client start for username : {username}, and socket : {socket} ")
        try:
            while True:
                message = socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.handle_message(socket, username, message)

        # la connection est fermé
        except Exception as e:
            logging.info(f"Handle client stop for username : {
                         username}, and socket : {socket} ")

        del self.clients[username]

        # Si le client était dans un canal, le retirer du canal
        for canal_name, canal_members in self.canaux.items():
            if username in canal_members:
                canal_members.remove(username)
                self.send_message_canal(
                    None, canal_name, f"{username} a quitté le canal.", )

        socket.close()
        return

    def handle_message(self, socket, username, message):
        if message[0] == "/":
            parts = message.split(" ")
            command = parts[0][1:].lower()
            if command == "away":
                if username not in self.away:
                    self.away[username] = message[6:]
                    logging.info(
                        f"user {username} is now away with the message : {message[6:]}")
                else:
                    del self.away[username]
                    logging.info(f"user {username} is no longer away")
            elif command == "help":
                response = """Liste des commandes : \n
                /away [message] \n
                /help \n
                /join <canal> [clé] \n
                /list \n
                /msg [canal|nick] message \n
                /names [channel]"""
                self.send_message(socket, response)
                logging.info(f"user {username} asked for help")
            elif command == "invite":
                nick = parts[1]
                canal = self.get_canal_of_user(username)
                msg = f"User {username} invite you to join canal {canal}"
                self.send_message(self.clients[nick], msg)
                logging.info(f"user {username} invited user {
                             nick} on canal {canal}")
            elif command == "join":
                canal = parts[1]
                if len(parts) > 2:
                    password = parts[2][1:len(
                        parts[2])-1] if parts[2][0] == "[" and parts[2][len(parts[2])-1] == "]" else ""
                else:
                    password = ""
                self.join_canal(socket, username, canal, password)
            elif command == "list":
                response = f"""Liste des canaux : \n"""
                for key in list(self.canaux.keys()):
                    response += f"   {key} \n"
                self.send_message(socket, response)
            elif command == "msg":
                target = parts[1]
                message_content = f"{username} : " + " ".join(parts[2:])
                if target in self.clients:
                    if target in self.away:
                        self.send_message(
                            socket, f"{target} n'est pas joignable en ce moment, message de sa part : {self.away[target]}")
                        logging.info(f"user {username} tried to contact {
                                     target} but {target} was away")
                    else:
                        self.send_message(
                            self.clients[target], "MP de " + message_content)
                        logging.info(
                            f"user {username} send a message to {target}")
                elif target in self.canaux:
                    self.send_message_canal(username, target, message_content)
                    logging.info(
                        f"user {username} send a message to canal {canal}")
                else:

                    response = "No user of canal where found for :" + target
                    self.send_message(socket, response)
                    logging.info(
                        f"user {username} send a message to an incorect canal/user")
            elif command == "names":
                if len(parts) == 1:  # il n'y a que /names
                    # on affiche donc tout
                    response = "Liste des utilisateurs : \n"
                    for canal in self.canaux:
                        response += f"   canal {canal} : \n"
                        for user in self.canaux[canal]:
                            response += f"      {user} \n"
                    logging.info(
                        f"user {username} sent a request for all users.")
                else:
                    canal = parts[1]
                    response = f"Liste des utilisateurs du canal {canal} : \n"
                    for user in self.canaux[canal]:
                        response += f"{user} \n"
                    logging.info(
                        f"user {username} sent a request for all users of canal {canal}.")

                self.send_message(socket, response)
        else:
            canal = self.get_canal_of_user(username)
            if canal != None:
                self.send_message_canal(
                    username, canal, f"{username} : {message}")
                logging.info(
                    f"user {username} sent a message to canal {canal}")
            else:
                self.send_message(socket, "You are in no canal.")
                logging.info(
                    f"user {username} tried to send a message but he was in no canal {canal}")

    def get_canal_of_user(self, username):
        for canal in self.canaux:
            if username in self.canaux[canal]:
                return canal

        return None

    def join_canal(self, socket, username, canal_name, password):
        """
        Rejoint un canal ou le crée s'il n'existe pas.
        """
        canal_of_user = self.get_canal_of_user(username)
        if canal_of_user != None:
            self.canaux[canal_of_user].remove(username)
            self.send_message_canal(username, canal_of_user,
                                    f"{username} a quitté le canal.")

        if canal_name not in self.canaux:
            self.canaux[canal_name] = [username]
            if password != "":
                self.canaux_password[canal_name] = password
            self.send_message(
                socket, f"Vous avez crée et rejoint le canal {canal_name}.")
        else:
            if canal_name in self.canaux_password:
                if password == self.canaux_password[canal_name]:
                    self.canaux[canal_name].append(username)
                    self.send_message(
                        socket, f"Vous avez rejoint le canal {canal_name}.")
                else:
                    self.send_message(
                        socket, f"Mauvais mot de passe. Vous n'avez pas rejoint le canal {canal_name}.")
                    logging.info(
                        f"user {username} did not join the canal {canal_name}")
                    return
            else:
                self.canaux[canal_name].append(username)
                self.send_message(
                    socket, f"Vous avez rejoint le canal {canal_name}.")

        self.send_message_canal(username, canal_name,
                                f"{username} a rejoint le canal.")
        logging.info(f"user {username} joined canal {canal_name}")
        return

    def send_message_canal(self, username, canal, message):
        try:
            for user in self.canaux[canal]:
                if user != username:
                    self.send_message(
                        self.clients[user], f"canal {canal} : {message}")
        except Exception as e:
            logging.error(f"Erreur envoi message canal : {e}")

    def send_message(self, socket, message):
        try:
            socket.send(message.encode('utf-8'))
        except Exception as e:
            logging.error(f"Erreur envoi message : {e}")


def main():
    if len(sys.argv) < 2:
        print("Need server port")
        return

    port = sys.argv[1]
    Server(port)


if __name__ == "__main__":
    main()
