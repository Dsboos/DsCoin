from dsc.common.prettyprint import warn, fail, info, success, info2, warn2
import asyncio, pickle


class NodeClient():
    def __init__(self, HOST, PORT):
        self.host = HOST
        self.port = PORT

    async def fetch_utxos(self, pks):
        info2("[Node Client] utxo fetch request initiated...")
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
        except:
            warn2(f"[Node Client] Couldn't fetch utxos: couldn't connect to node!")
            return False, "Couldn't connect to node."

        #Requesting permission with header:
        writer.write(b"[utxos_fetch_request]")
        await writer.drain()
        reply = await reader.read(1024)
        if reply != b"[continue_request]":
            warn2(f"[Node Client] Couldn't fetch utxos: Request denied: {reply.decode()}")
            return False, "Request was denied."
        
        #Send the pks
        writer.write(pks.encode() + b"[end_request]")
        await writer.drain()

        #Wait for signal from node to get ready for data stream
        chunk = b""
        status = b""
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                warn2(f"[Node Client] Couldn't fetch utxos: Server closed connection!")
                return False, "Server closed connection."
            status += chunk
            if b"[get_ready]" in status:
                break
        
        #Accept the data stream
        writer.write(b"[ready]")

        #Record the data stream
        chunk = b""
        queryb = b""
        while queryb[-13:] != b"[end_request]":
            chunk = await reader.read(1024)
            if not chunk:
                warn2(f"[Node Client] Couldn't fetch utxos: Server closed connection!")
                return False, "Server closed connection."
            queryb += chunk
        query = pickle.loads(queryb[:-13])
        return query, None
    
    async def submit_block(self, block):
        info2("[Node Client] Block submission request initiated...")
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
        except:
            warn2(f"[Node Client] Couldn't submit block: couldn't connect to node!")
            return False, "Server closed connection."

        #Requesting permission with header:
        writer.write(b"[block_submission_request]")
        await writer.drain()
        reply = await reader.read(1024)
        if reply != b"[continue_request]":
            warn2(f"[Node Client] Couldn't submit block: Request denied: {reply.decode()}")
            return False, "Request was denied."
        
        #Send the block data
        writer.write(pickle.dumps(block) + b"[end_request]")
        await writer.drain()

        #Check for status from node on the block submission
        chunk = b""
        status = b""
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                warn2(f"[Node Client] Couldn't confirm block submission: Server closed connection!")
                return False, "Server closed connection."
            status += chunk
            if b"[block_accepted]" in status:
                return True, None
            if b"[block_rejected]" in status:
                return False, "Block was rejected by node." 
    
    async def submit_tx(self, tx):
        info2("[Node Client] Tx submission request initiated...")
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
        except:
            warn2(f"[Node Client] Couldn't submit tx: couldn't connect to node!")
            return False, "Server closed connection."

        #Requesting permission with header:
        writer.write(b"[tx_submission_request]")
        await writer.drain()
        reply = await reader.read(1024)
        if reply != b"[continue_request]":
            warn2(f"[Node Client] Couldn't submit tx: Request denied: {reply.decode()}")
            return False, "Request was denied."
        
        #Send the tx data
        writer.write(pickle.dumps(tx) + b"[end_request]")
        await writer.drain()

        #Check for status from node on the tx submission
        chunk = b""
        status = b""
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                warn2(f"[Node Client] Couldn't confirm tx submission: Server closed connection!")
                return False, "Server closed connection."
            status += chunk
            if b"[tx_accepted]" in status:
                return True, None
            if b"[tx_rejected]" in status:
                return False, "Tx was rejected by node." 