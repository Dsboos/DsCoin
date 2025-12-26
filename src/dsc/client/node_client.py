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
            return False

        #Requesting permission with header:
        writer.write(b"[utxos_fetch_request]")
        await writer.drain()
        reply = await reader.read(1024)
        if reply != b"[continue_request]":
            warn2(f"[Node Client] Couldn't fetch utxos: Request denied: {reply.decode()}")
            return False
        
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
                return False
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
                return False
            queryb += chunk
        query = pickle.loads(queryb[:-13])
        return query