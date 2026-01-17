from dsc.common.prettyprint import warn, fail, info, success, info2, warn2
from pydantic import BaseModel
import pickle, requests, asyncio, base64


class QueryPayload(BaseModel):
    data: str

class BlockPayload(BaseModel):
    data: str

class NodeClient():
    def __init__(self, HOST, PORT):
        self.host = HOST
        self.port = PORT

    #Fetching Methods
    async def fetch_utxos(self, pks):
        info2("[Node Client] utxos fetch request initiated...")
        response = requests.get(url=f"{self.host}:{self.port}/utxos", params={"pks": pks})
        query_payload = response.json()
        queryb = base64.b64decode(query_payload["data"])
        query = pickle.loads(queryb)
        return query, response.status_code
    
    async def fetch_mempool(self):
        info2("[Node Client] mempool fetch request initiated...")
        response = requests.get(url=f"{self.host}:{self.port}/mempool")
        query_payload = response.json()
        queryb = base64.b64decode(query_payload["data"])
        query = pickle.loads(queryb)
        return query, response.status_code
    
    async def fetch_blocks(self):
        info2("[Node Client] blocks fetch request initiated...")
        response = requests.get(url=f"{self.host}:{self.port}/blocks")
        query_payload = response.json()
        queryb = base64.b64decode(query_payload["data"])
        query = pickle.loads(queryb)
        return query, response.status_code
    
    async def fetch_chainstate(self):
        info2("[Node Client] chainstate fetch request initiated...")
        response = requests.get(url=f"{self.host}:{self.port}/chainstate")
        query_payload = response.json()
        queryb = base64.b64decode(query_payload["data"])
        query = pickle.loads(queryb)
        return query, response.status_code
    
    #Submission Methods
    async def submit_block(self, block):
        info2("[Node Client] Block submission request initiated...")
        blockb = pickle.dumps(block)
        encoded_data = base64.b64encode(blockb).decode("utf-8")
        payload = {"data": encoded_data}
        response = requests.post(url=f"{self.host}:{self.port}/submit-block", json=payload)
        return response.status_code, response.reason
    
    async def submit_tx(self, tx):
        info2("[Node Client] Tx submission request initiated...")
        txb = pickle.dumps(tx)
        encoded_data = base64.b64encode(txb).decode("utf-8")
        payload = {"data": encoded_data}
        response = requests.post(url=f"{self.host}:{self.port}/submit-tx", json=payload)
        return response.status_code, response.reason