import tkinter as tk
import sys
import socket
import threading


class Client:
    def __init__(self, master, username, server_port):
        self.master = master
        self.username = username
        self.serverport = int(server_port)
        master.title("Internet Relay Chat")
        master.geometry("1000x600")
        master.configure(bg="black")
        self.current_frame = None
        self.create_chat_frame()
        self.connect_to_server()

    def create_chat_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        MainFrame = tk.Frame(self.master)
        MainFrame.configure(bg="black")

        # Create and configure the Text widget for displaying messages
        self.text_widget = tk.Text(
            MainFrame, bg="white", state=tk.DISABLED, width=120, height=30)
        self.text_widget.pack(pady=10)

        # Create and configure the Entry widget for user input
        self.entry = tk.Entry(MainFrame, bg="white", width=120)
        self.entry.pack(padx=10, pady=10)

        self.master.bind('<Return>', self.send_message)

        MainFrame.pack(expand=True)

    def send_message(self, event):
        message = self.entry.get()
        if message:
            self.text_widget.configure(state=tk.NORMAL)
            self.text_widget.insert(tk.END, f"{self.username} : {message}\n")
            self.client_socket.send(message.encode('utf-8'))
            self.text_widget.configure(state=tk.DISABLED)
            self.text_widget.see("end")
            self.entry.delete(0, tk.END)

    def receive_message(self):
        try:
            while True:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.text_widget.configure(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, f"{message}\n")
                    self.text_widget.configure(state=tk.DISABLED)
                    self.text_widget.see("end")
                    self.entry.delete(0, tk.END)
        # le serveur est fermé
        except Exception as e:
            print(e)

        self.client_socket.close()

    def connect_to_server(self):
        host = '127.0.0.1'  # Adresse IP du serveur
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, self.serverport))
        self.client_socket.send(f"{self.username}".encode('utf-8'))
        t = threading.Thread(target=self.receive_message)
        t.start()


def main():
    if len(sys.argv) != 3:
        print("Need username and server port")
        return
    root = tk.Tk()
    Client(root, sys.argv[1], sys.argv[2])
    root.mainloop()


if __name__ == "__main__":
    main()
