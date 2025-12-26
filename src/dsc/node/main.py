from dsc.node.blockchain import BlockChain
from dsc.node.mempool import Mempool
from dsc.common.blocks import Block, CBTx
from dsc.common.transactions import Tx, TxO, verify_Tx
from dsc.common.prettyprint import info, warn2, fail, success, info2, warn2
import asyncio
import pickle

HOST = "localhost"
PORT = 8000
db_lock = asyncio.Lock()

class Node():
    def __init__(self):
        pass
    
    async def server_loop(self):
        server = await asyncio.start_server(self.request_handler, HOST, PORT)
        while True:
            async with server:
                info2(f"[Network] Started listening for connections...")
                await server.serve_forever()

    async def request_handler(self, reader, writer):
        data = await reader.read(1024)
        header = data.decode()
        peer = writer.get_extra_info("peername")
        client_addr, client_port = peer[:2]
        info2(f"[Network] New request from: {client_addr}:{client_port} | {header}")
        if header == "[block_submission_request]":
            block_data = await self.get_block_data(reader, writer)
            if not block_data:
                writer.write(b"[invalid_request]")
                await writer.drain()
                warn2(f"[Network] {client_addr}:{client_port}'s request was closed: Invalid block data!")
                return 
            wasAdded = await self.add_block(block_data)
            if wasAdded:
                writer.write(b"[block_accepted]")
                await writer.drain()
                #Delete all txs associated with this block from mempool
                for tx in pickle.loads(block_data).Tx_list:
                    mp.del_tx(tx)
                info2(f"[Network] {client_addr}:{client_port}'s block submission was accepted!")
            else:
                writer.write(b"[block_rejected]")
                await writer.drain()
                warn2(f"[Network] {client_addr}:{client_port}'s block submission was rejected!")
        elif header == "[utxos_fetch_request]":
            pks = await self.get_client_pks(reader, writer)
            if not pks:
                warn2(f"[Network] {client_addr}:{client_port}'s request was closed: Invalid Public Key!")
                writer.close()
                return
            await self.serve_utxos(pks, reader, writer)
            info2(f"[Network] {client_addr}:{client_port} was served UTxOs as per request!")
        elif header == "[tx_submission_request]":
            txb = await self.get_tx(reader, writer)
            if not txb:
                warn2(f"[Network] {client_addr}:{client_port}'s request was closed: couldn't get tx!")
                writer.write(b"[tx_rejected]")
                await writer.drain()
                writer.close()
                return
            if not verify_Tx(pickle.loads(txb), blockless=True):
                warn2(f"[Network] {client_addr}:{client_port}'s request was closed: couldn't verify tx!")
                writer.write(b"[tx_rejected]")
                await writer.drain()
                writer.close()
                return
            writer.write(b"[tx_accepted]")
            await writer.drain()
            writer.close()
            mp.add_tx(pickle.loads(txb))
            info2(f"[Network] {client_addr}:{client_port}'s tx submission was added to mempool!")
        else:
            warn2(f"[Network] {client_addr}:{client_port}'s request was denied: Invalid request!")
            writer.write(b"[invalid_request]")
            await writer.drain()

    #UTXO fetch request handling
    async def serve_utxos(self, pks, reader, writer):
        query = bc.fetch_UTxOs(pks)
        queryb = pickle.dumps(query)
        writer.write(b"[get_ready]")
        await writer.drain()
        await reader.read(1024)         #Get ready for client to recieve the query
        writer.write(queryb + b"[end_request]")
        await writer.drain()
        
    async def get_client_pks(self, reader, writer):
        pks = b""
        writer.write(b"[continue_request]")
        await writer.drain()
        while pks[-13:] != b"[end_request]":
            chunk = await reader.read(1024)
            if not chunk:               #If client closed connection
                warn2(f"[Network] Failed to get client's pk: Client closed connection!")
                return False
            pks += chunk
            if len(pks) > 102400:       #Check if request is getting too long (more than 100kb)
                writer.write(b"[request_denied]")
                await writer.drain()
                warn2(f"[Network] Failed to get client's pk: Request size limit exhausted!")
                return False
        return pks[:-13].decode()

    #Block submission request handling
    async def get_block_data(self, reader, writer):
        block_data = b""
        writer.write(b"[continue_request]")
        await writer.drain()
        while block_data[-13:] != b"[end_request]":
            chunk = await reader.read(1024)
            if not chunk:                   #If client closed connection  
                warn2(f"[Network] Failed to get block data: Client closed connection!")
                return False
            block_data += chunk
            if len(block_data) > 102400:    #Check if request is getting too long (more than 100kb)
                writer.write(b"[request_denied]")
                await writer.drain()
                warn2(f"[Network] Failed to get block data: Request size limit exhausted!")
                return False
        block_data = block_data[:-13]       #Remove the footer
        return block_data

    async def add_block(self, block_data):
        try:
            async with db_lock:
                block = pickle.loads(block_data)
                status = bc.process_block(block)
            return status
        except Exception as e:
            warn2(f"[Network] Submitted block was rejected by chain!")
            return False

    #Tx submission request handling
    async def get_tx(self, reader,writer):
        txb = b""
        writer.write(b"[continue_request]")
        await writer.drain()
        while txb[-13:] != b"[end_request]":
            chunk = await reader.read(1024)
            if not chunk:               #If client closed connection
                warn2(f"[Network] Failed to get tx: Client closed connection!")
                return False
            txb += chunk
            if len(txb) > 102400:       #Check if request is getting too long (more than 100kb)
                writer.write(b"[request_denied]")
                await writer.drain()
                warn2(f"[Network] Failed to get tx: Request size limit exhausted!")
                return False
        return txb[:-13]

if __name__ == "__main__":
    bc = BlockChain()
    mp = Mempool()
    node = Node()
    asyncio.run(node.server_loop())
