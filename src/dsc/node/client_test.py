from dsc.common.blocks import Block, CBTx
from dsc.common.transactions import Tx, TxO
from dsc.common.prettyprint import info, warn, fail, success
import asyncio
import pickle
import ecdsa

HOST = "localhost"
PORT = 8000

async def submit_block(block):
    info("Block submission request initiated.")
    block_data = pickle.dumps(block)
    reader, writer = await asyncio.open_connection(HOST, PORT)
    #Requesting permission with header:
    writer.write(b"[block_addition_request]")
    await writer.drain()
    reply = await reader.read(1024)
    if reply != b"[continue_request]":
        fail(f"Request denied: {reply.decode()}")
        return False
    
    writer.write(block_data+b"[end_request]")
    await writer.drain()

    chunk = b""
    status = b""
    while True:
        chunk = await reader.read(1024)
        if not chunk:
            fail(f"Server closed connection!")
            return False
        status += chunk
        if b"[block_rejected]" in status:
            fail(f"Block was rejected!")
            return False
        if b"[block_accepted]" in status:
            success(f"Block was accepted!")
            return True

async def fetch_utxos(pk):
    info("UTxO fetch request initiated.")
    reader, writer = await asyncio.open_connection(HOST, PORT)
    #Requesting permission with header:
    writer.write(b"[utxos_fetch_request]")
    await writer.drain()
    reply = await reader.read(1024)
    if reply != b"[continue_request]":
        fail(f"Request denied: {reply.decode()}")
        return False
    
    writer.write(pk.encode() + b"[end_request]")
    await writer.drain()

    chunk = b""
    status = b""
    while True:
        chunk = await reader.read(1024)
        if not chunk:
            fail(f"Server closed connection!")
            return False
        status += chunk
        if b"[get_ready]" in status:
            break
    
    writer.write(b"[ready]")

    chunk = b""
    queryb = b""
    while queryb[-13:] != b"[end_request]":
        chunk = await reader.read(1024)
        if not chunk:
            fail(f"Server closed connection!")
            return False
        queryb += chunk
    query = pickle.loads(queryb[:-13])
    return query

async def main():
    rpks = "d353cb6bbcd1ef420a2a21b9df72746e4dc857b2ffc4ba3b3b0de04bed51792662f9d826baa168ed9508f69440b9ad564e2f70d2b947fd06329768eeb86666c7"
    rsks = "73bd55e5fd8c179bfee2f662fcd2cb2663012297a35aa86784d7dcea575130dd"
    rpk =  ecdsa.VerifyingKey.from_string(bytes.fromhex(rpks), curve=ecdsa.SECP256k1)
    rsk =  ecdsa.SigningKey.from_string(bytes.fromhex(rsks), curve=ecdsa.SECP256k1)
    utxos = await fetch_utxos(rpks)
    print(utxos[3][:-1])

asyncio.run(main())