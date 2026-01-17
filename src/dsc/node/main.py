from dsc.node.blockchain import BlockChain
from dsc.node.mempool import Mempool
from dsc.common.blocks import Block, CBTx
from dsc.common.transactions import Tx, TxO, verify_Tx
from dsc.common.prettyprint import info, warn2, fail, success, info2, warn2
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import pickle, ecdsa, base64, uvicorn

bc: BlockChain = None
mp: Mempool = None

class QueryPayload(BaseModel):
    data: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bc, mp

    bc = BlockChain()
    # if bc.blank_chain:
    #     sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    #     pk = sk.get_verifying_key()
    #     name = input("Chain Name: ")
    #     difficulty = int(input("Difficulty: "))
    #     Tx_limit = int(input("Tx Limit: "))
    #     mine_reward = int(input("Mining Reward: "))
    #     password = input("Chain Password (TESTING): ")
        
    #     bc.name = name
    #     bc.difficulty = difficulty
    #     bc.Tx_limit = Tx_limit
    #     bc.mine_reward = mine_reward
    #     bc.chain_password = password

    #     root = Block(None, pk, bc.mine_reward, bc.Tx_limit, bc.difficulty, "root")
    #     root.mine()
    #     bc.add_block(root, main_chain=True) # type: ignore (idk why this dumbass retard error keeps coming up.)
    #     bc.root = root
    #     bc.surface = bc.root
    #     bc.save_state()
    mp = Mempool()
    yield

app = FastAPI(lifespan=lifespan)

#GET Request Handling
@app.get("/utxos")
def serve_utxos(pks: str | None = None):
    if pks:
        query = bc.fetch_UTxOs_from_pks(pks)
        queryb = pickle.dumps(query)
        encoded_data = base64.b64encode(queryb)

        return {"data": encoded_data}
    
    query = bc.fetch_UTxOs()
    queryb = pickle.dumps(query)
    encoded_data = base64.b64encode(queryb)

    return {"data": encoded_data}

@app.get("/mempool")
def serve_mempool(): 
    query = mp.get_pending()
    queryb = pickle.dumps(query)
    encoded_data = base64.b64encode(queryb)

    return {"data": encoded_data}

@app.get("/blocks")
def serve_blocks(hash: str | None = None): 
    if hash:
        query = bc.fetch_block_from_hash(blockh=hash)
        if not query:
            raise HTTPException(status_code=404, detail="Block not found!")
        queryb = pickle.dumps(query)
        encoded_data = base64.b64encode(queryb)

        return {"data": encoded_data}
    
    query = bc.fetch_blocks()
    queryb = pickle.dumps(query)
    encoded_data = base64.b64encode(queryb)

    return {"data": encoded_data}

@app.get("/chainstate")
def serve_chainstate(): 
    query = bc.fetch_chainstate()
    queryb = pickle.dumps(query)
    encoded_data = base64.b64encode(queryb)

    return {"data": encoded_data}

#Submission Handling
@app.post("/submit-block")
def handle_block_submission(payload: QueryPayload):
    try:
        blockb = base64.b64decode(payload.data)
        block = pickle.loads(blockb)
        status = bc.process_block(block)
        if not status:
            raise HTTPException(status_code=400, detail=f"Block Rejected!")
        for tx in block.Tx_list: #Delete all associated tx from mempool
            mp.del_tx(tx)
        return {"status": "Block Accepted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Block could not be added: {e}!")

@app.post("/submit-tx")
def handle_tx_submission(payload: QueryPayload):
    try:
        txb = base64.b64decode(payload.data)
        tx = pickle.loads(txb)
        if not verify_Tx(tx, blockless=True):
            raise HTTPException(status_code=400, detail=f"Couldn't Verify Tx!")
        mp.add_tx(tx)
        return {"status": "Tx Accepted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tx could not be accepted: {e}!")


