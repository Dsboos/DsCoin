import sqlite3
import random
import dsc.blockchain.blockchain

#This module handles the client's wallets and their functionalities

class WalletHandler():
    def __init__(self, first_active_user):

        self.active_user = first_active_user
        self.wallet_ids = {}                    # A dict of all wallets currently logged into client

        # Connections initialization
        self.init_db()
        self.connect_blockchain_db()

    def connect_blockchain_db(self):
        if self.bc_conn:
            self.bc_conn.close()
        self.bc_conn = sqlite3.connect("file:data/blockchain.db?mode=ro", uri=True) # Open a connection to the blockchain database in read-only mode
        self.bc_cursor = self.bc_conn.cursor()

    def init_db(self):
        self.conn = sqlite3.connect("data/client.db")
        self.cursor = self.conn.cursor()
    
    def add_wallet(self, user_pk):
        user_id = self.create_user_id(user_pk)
        self.wallet_ids[user_id] = user_pk
        self.cursor.execute(f"""CREATE TABLE {user_id}""")

    def create_user_id(self, pk):
        #The protocol for generating a short unique id for the supplied user
        #It joins a six digit random number with first six characters of the user pk
        return f"{random.randint(100000, 999999)}{pk}"