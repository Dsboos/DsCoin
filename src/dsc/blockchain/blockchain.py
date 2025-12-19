from dsc.utils.prettyprint import warn, fail, success, info
from dsc.blockchain.transactions import TxO, Tx
from dsc.blockchain.blocks import Block, CBTx, verify_block
from datetime import datetime
import sqlite3
import pickle
import ecdsa
import random

#Rule Number One: Always use hashes to reference blocks. Only use objs when details within blocks are required
class BlockChain():
    def __init__(self, root_block, mine_reward=64, Tx_limit = 5, difficulty=3, name="unnamed_blockchain"):
        
        #The Blockchain stores all its blocks and transactions in the blockchain database
        self.conn = sqlite3.Connection("data/blockchain.db")
        self.cursor = self.conn.cursor()
        self.init_db()  #Initialize the blockchain database

        #Chain Details
        self.name = name
        self.height = 0
        self.root = root_block
        self.add_block(self.root)
        self.surface = self.root

        #Block Specifications
        self.difficulty = difficulty
        self.Tx_limit = Tx_limit
        self.mine_reward = mine_reward

        self.save_snapshot()

    def init_db(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS TxOs (
                            o_hash TEXT PRIMARY KEY,
                            tx_hash TEXT,
                            block_hash TEXT,
                            confirmed BOOLEAN,
                            obj BLOB
                            )                           
                            """)
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS UTxOs (
                            o_hash TEXT PRIMARY KEY,
                            tx_hash TEXT,
                            block_hash TEXT,
                            rcvr TEXT,
                            amt REAL,
                            obj BLOB
                            )                           
                            """)
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS blocks (
                            hash TEXT PRIMARY KEY,
                            prevh TEXT,
                            height INTEGER,
                            main_chain BOOLEAN,
                            obj BLOB
                            )                           
                            """)
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS snapshots (
                            name TEXT PRIMARY KEY,
                            height INTEGER,
                            surface TEXT
                            )""")
        self.conn.commit()

    def refresh_db(self):
        if self.conn:
            self.conn.close()
        self.conn = sqlite3.Connection("data/blockchain.db")
        self.cursor = self.conn.cursor()

    def save_snapshot(self):
        nonce = f"{datetime.now().strftime("%H$%M$%S_%d$%m$%y")}_{random.randint(100000, 999999)}"
        snapshot_name = "snapshot_" + nonce
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {snapshot_name} (
                            o_hash TEXT PRIMARY KEY,
                            tx_hash TEXT,
                            block_hash TEXT,
                            rcvr TEXT,
                            amt REAL,
                            obj BLOB
                            )""")
        self.cursor.execute(f"INSERT INTO {snapshot_name} SELECT * FROM UTxOs")
        self.cursor.execute("INSERT INTO snapshots VALUES (?, ?, ?)",
                            (snapshot_name, self.height, self.surface.hash))
        self.conn.commit()


    def process_block(self, block):
        #A) Verifications
        #1.1- Verify Block (everything except UTxO validity)
        if not verify_block(block, self.difficulty, self.mine_reward):
            fail(f"[BlockChain] {block} couldn't be verified!")
            return False
        
        #B) If the block's target is surface
        if block.prevh == self.surface.hash:
            if not self.verify_UTxOs(block):
                fail(f"[BlockChain] {block} contained invalid UTxO(s)!")
                return False
            block.prev = self.surface
            block.height = self.height + 1
            self.height += 1
            self.surface.next.append(block.hash)
            self.cursor.execute("UPDATE blocks SET obj = ? WHERE hash = ?", (pickle.dumps(self.surface),self.surface.hash)) #Update the ex-surface block to reflect new child
            self.surface = block
            self.add_block(block)
            success(f"[BlockChain] {block} added onto {block.prev}!")
            return True

        #C) If the block's target is below surface
        query = self.cursor.execute("SELECT obj FROM blocks WHERE hash = ?", (block.prevh,)).fetchone()
        target = pickle.loads(query[0]) if query else None
        if target:
            if not self.verify_UTxOs(block, main_chain=False):
                fail(f"[BlockChain] Fork: {block} contained invalid UTxO(s)!")
                return False
            block.prev = target 
            block.height = target.height + 1
            target.next.append(block.hash)
            self.cursor.execute("UPDATE blocks SET obj = ? WHERE hash = ?", (pickle.dumps(target),target.hash)) #Update the target block to reflect new child
            self.add_block(block, main_chain=False)
            success(f"[BlockChain] {block} added as fork block on {target} which currently has branches: {[x[-10:] for x in target.next]}")

            #C1) Check if this addition made the fork longer than the main chain
            if block.height > self.height:
                info(f"[BlockChain] {block} from a competing fork has broken surface!")
                self.reorg(block)           #Reorganize the chain if fork defeated main chain
                self.surface = block
            self.conn.commit()
            return True
        else:
            fail(f"[BlockChain] {block} not added: Couldn't attach to anything!")
            return False

    def verify_UTxOs(self, block, main_chain=True):
        if main_chain:                      #Use the main UTxOs table for main chain input verification
            for Tx in block.Tx_list:
                for TxI in Tx.inputs:       #Verify that all inputs provided in Tx do exist in the UTxOs table (for main chain)
                    query = self.cursor.execute("SELECT * FROM UTxOs WHERE o_hash = ?", (TxI.hash,)).fetchone()
                    if not query:
                        warn(f"[UTxO Verification] Input {TxI} in Tx {Tx} doesn't exist in the UTxOs table!")
                        return False
            return True
        else:                               #Use a simulated UTxOs table for fork input verification
            #1.0- Retrieve the closest block to fork's common anscestor (create a path list while at it)
            curr_blockh = block.prevh       #blockh stands for block hash
            query = self.cursor.execute("SELECT prevh, main_chain, obj FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
            while not query[1]:             #Loop over till a block with main_chain = true, i.e a main_chain block, is reached
                curr_blockh = query[0]
                query = self.cursor.execute("SELECT prevh, main_chain, obj FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
            comm_block = pickle.loads(query[2])

            #1.1- Build UTxO table of start block state
            sim_UTxOs = {}                  #The simulated UTxOs table is a dict of hashes, 
            snapshots = self.cursor.execute("SELECT * FROM snapshots WHERE height <= ?", (comm_block.height,)).fetchall()
            latest_snapshot = (None, 0, None)
            for snapshot in snapshots:
                if snapshot[1] >= latest_snapshot[1]:
                    latest_snapshot = snapshot
            snapshot_UTxO = self.cursor.execute(f"SELECT o_hash FROM {latest_snapshot[0]}").fetchall()
            if snapshot_UTxO:
                for UTxO in [x[0] for x in snapshot_UTxO]:
                    sim_UTxOs[UTxO] = True
            snapshot_blockh = latest_snapshot[2]

            #1.2- Create a path from snapshot block (not including) to fork tip (including)
            fork_path = []
            curr_blockh = block.prevh #fork tip
            while curr_blockh != snapshot_blockh:#Loop from fork tip towards snapshot block (not including)
                fork_path.append(curr_blockh)
                query = self.cursor.execute("SELECT prevh FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
                curr_blockh = query[0]

            #1.3- Build UTxO table forwards from snapshot block to fork tip
            for curr_blockh in reversed(fork_path):#Loop from snapshot (not including) block towards fork tip
                query = self.cursor.execute("SELECT obj FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
                curr_block = pickle.loads(query[0])
                for CBTx in curr_block.CBTx_list: #Add CBTx
                    sim_UTxOs[CBTx.hash] = True
                for Tx in curr_block.Tx_list: #Add TxOs and remove TxIs
                    if Tx.Tx_fee:
                        sim_UTxOs[Tx.Tx_fee.hash] = True
                    for TxO in Tx.outputs:
                        sim_UTxOs[TxO.hash] = True
                    for TxI in Tx.inputs:
                        try:
                            sim_UTxOs.pop(TxI.hash)
                        except Exception as e: raise e  
            #2- Now that the UTxO table is built, we begin verifying the new block:
            for Tx in block.Tx_list:
                for TxI in Tx.inputs:       #Verify that all inputs provided in Tx do exist in the simulated UTxOs table
                    if not sim_UTxOs.get(TxI.hash):
                        warn(f"[UTxO Verification] Input {TxI} in Tx {Tx} doesn't exist in the simulated UTxOs table!")
                        return False
            return True

    def add_block(self, block, main_chain=True):
        if main_chain:                      #If block is part of main_chain
            #1.1- Add all CBTx's to the blockchain (TxO table and UTxO table)
            for CBTx in block.CBTx_list:
                self.add_TxO(CBTx, None, block)
                self.add_UTxO(CBTx, None, block)
            #1.2- Add all Tx's to the blockchain
            for Tx in block.Tx_list:
                self.add_Tx(Tx, block)      #Adds all TxO's to TxO table and modifies UTxO table accordingly
            #2- Add the block to the blocks table
            self.cursor.execute("INSERT OR IGNORE INTO blocks VALUES (?, ?, ?, ?, ?)", 
                                (block.hash, block.prevh if block.prevh else "None", block.height, True, pickle.dumps(block)))
        else:
            #a1.1- Add all CBTx's to the blockchain (TxO table only)
            for CBTx in block.CBTx_list:
                self.add_TxO(CBTx, None, block, confirmed=False)
            #a1.2- Add all Tx's to the blockchain
            for Tx in block.Tx_list:
                self.add_Tx(Tx, block, confirmed=False) #Adds all TxO's to only TxO table
            #a2- Add the block to the blocks table
            self.cursor.execute("INSERT OR IGNORE INTO blocks VALUES (?, ?, ?, ?, ?)", 
                                (block.hash, block.prevh, block.height, False, pickle.dumps(block)))
    
    def del_Tx(self, Tx, block):
        #Set all TxOs to unconfirmed
        for TXO in Tx.outputs:
            self.set_TxO(TXO, False)
        if Tx.Tx_fee:
            self.set_TxO(Tx.Tx_fee, False)
        #Remove TxOs (and Tx_fee CBTxOs) from UTxOs table
        self.cursor.execute("DELETE FROM UTxOs WHERE tx_hash = ?", (Tx.hash,))
        #Add all TxIs back to UTxOs table
        for TxI in Tx.inputs:
            self.add_UTxO(TxI, (Tx if isinstance(TxI, TxO) else None), block)

    def add_Tx(self, Tx, block, confirmed=True): #Confirmed is true for main chain additions, false for forks
        #1.1- Add Tx fees (if any) to TxOs table, and to UTxOs table if main chain
        if Tx.Tx_fee:
            self.add_TxO(Tx.Tx_fee, Tx, block, confirmed)
            if confirmed:
                self.add_UTxO(Tx.Tx_fee, Tx, block)
        #1.2- Add TxOs to TxOs and UTxOs table if main chain
        for TxO in Tx.outputs:
            self.add_TxO(TxO, Tx, block, confirmed)
            if confirmed:
                self.add_UTxO(TxO, Tx, block)
        #2- Remove TxIs from UTxOs if main chain
        if confirmed:
            for TxI in Tx.inputs:
                self.cursor.execute("DELETE FROM UTxOs WHERE o_hash = ?", (TxI.hash,))

    def set_TxO(self, TxO, confirmed):
        self.cursor.execute("UPDATE TxOs SET confirmed = ? WHERE o_hash = ?", (confirmed, TxO.hash))

    def add_TxO(self, TxO, Tx, block, confirmed=True):
        self.cursor.execute("INSERT OR IGNORE INTO TxOs VALUES (?, ?, ?, ?, ?)", 
                            (TxO.hash, (Tx.hash if Tx else "None"), block.hash, confirmed, pickle.dumps(TxO)))
        self.set_TxO(TxO, confirmed)    #For good measure (used by winner blocks during chain reorgs)
        
    def add_UTxO(self, TxO, Tx, block):
        self.cursor.execute("INSERT INTO UTxOs VALUES (?, ?, ?, ?, ?, ?)", 
                            (TxO.hash, (Tx.hash if Tx else "None"), block.hash, TxO.rcvr.to_string().hex(), TxO.amt, pickle.dumps(TxO)))
        
    def reorg(self, new_block):
        new_path = []                   #New block to common anscestor (not including)
        old_path = []                   #Surface to common anscestor (not including)

        curr_blockh = new_block.hash    #blockh stands for block hash
        query = self.cursor.execute("SELECT prevh, main_chain, obj FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
        while not query[1]:             #Loop over till a block with main_chain = false, i.e a main_chain block, is reached
            self.cursor.execute("UPDATE blocks SET main_chain = ? WHERE hash = ?", (True, curr_blockh)) #Set fork blocks as main chain
            new_path.append(pickle.loads(query[2])) 
            curr_blockh = query[0]
            query = self.cursor.execute("SELECT prevh, main_chain, obj FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
        comm_blockh = curr_blockh        #The block where main_chain was already true is the common anscestor of both forks

        curr_blockh = self.surface.hash  #Now set current block to surface and travel back to common anscestor
        query = self.cursor.execute("SELECT prevh, obj FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
        while curr_blockh != comm_blockh:#Loop over till common block is reached, set blocks main_chain to false otw
            self.cursor.execute("UPDATE blocks SET main_chain = ? WHERE hash = ?", (False, curr_blockh))
            old_path.append(pickle.loads(query[1]))
            curr_blockh = query[0]
            query = self.cursor.execute("SELECT prevh, obj FROM blocks WHERE hash = ?", (curr_blockh,)).fetchone()
        #Undo the old path blocks (Remove generated UTxOs and re-insert spent ones)
        for orphan in old_path:
            for Tx in orphan.Tx_list:     #Undos the Tx's (and their Tx_fee CBTxOs) (& unconfirm them in TxOs table)
                self.del_Tx(Tx, orphan)
            for CBTx in orphan.CBTx_list: #Remove CBTxOs from UTxOs table (& unconfirm them in TxOs table)
                self.cursor.execute("DELETE FROM UTxOs WHERE o_hash = ?", (CBTx.hash,))
                self.set_TxO(CBTx, False)

        #Process the new path blocks (Add generated UTxOs and remove spent ones)
        for winner in reversed(new_path): #Reversed because we are travelling from common anscestor to fork tip
            self.add_block(winner)        #Adding block again has effect of validating generated UTxOs and nullifying spent ones.
        info(f"[Chain ReOrg] Chain successfully reorganized!")



if __name__ == "__main__":
    sk = ecdsa.SigningKey.generate(ecdsa.curves.SECP256k1)
    pk = sk.get_verifying_key()

    root = Block(None, pk, name="root")
    root.mine()
    txo1 = CBTx(pk, 150, type="addition")
    root.add_CBTx(txo1)

    chain = BlockChain(root)

    #Try adding invalid block 
    b1_invalid = Block(root.hash, pk, name="b1_invalid")
    tx_invalid1 = Tx(pk, name="invalid1")      #Client side verifications are turned off for this test. 
    txi1 = TxO(pk, pk, 50, name="pk_pk_50")    #The blockchain does the verification now.
    tx_invalid1.add_input(txi1)
    tx_invalid1.create_output(pk, 60, name="pk_pk_60")
    tx_invalid1.sign(sk)

    b1_invalid.add_Tx(tx_invalid1)                          #This will be allowed so blockchain can reject b1
    # b1_invalid.mine()                                 
    chain.process_block(b1_invalid)                         #Should be rejected

    #Add valid block b1 now
    b1 = Block(root.hash, pk, name="b1")
    tx1 = Tx(pk, name="tx1")
    tx1.add_input(txo1)
    tx1.create_output(pk, 30, name="pk_pk_30")
    tx1.sign(sk)

    b1.add_Tx(tx1)
    b1.mine()
    chain.process_block(b1)
    
    #Make fork block a1
    a1 = Block(root.hash, pk, name="a1")
    tx2 = Tx(pk, name="tx2")
    tx2.add_input(txo1)
    txo2 = tx2.create_output(pk, 67, name="pk_pk_67")
    tx2.sign(sk)

    a1.add_Tx(tx2)
    a1.mine()
    chain.process_block(a1)

    #Make fork longer than main chain by adding another block a2
    a2 = Block(a1.hash, pk, name="a2")
    tx2 = Tx(pk, name="tx2")
    tx2.add_input(txo2)
    tx2.create_output(pk, 30, name="pk_pk_30")
    tx2.sign(sk)

    a2.add_Tx(tx2)
    a2.mine()
    chain.process_block(a2)

    #Everything below here is AI generated code for bulk testing of the chain's robustness  

    print("\n========== EXTENDED MAIN CHAIN TEST ==========\n")

    # --- Extend main chain to b2, b3, b4 ---
    prev = b1
    spendable = tx1.outputs[0]   # pk_pk_30

    main_blocks = []

    for i in range(2, 5):
        bi = Block(prev.hash, pk, name=f"b{i}")
        tx = Tx(pk, name=f"tx_main_{i}")
        tx.add_input(spendable)
        spendable = tx.create_output(pk, 25 - i, name=f"pk_pk_{25 - i}")
        tx.sign(sk)

        bi.add_Tx(tx)
        bi.mine()
        chain.process_block(bi)

        main_blocks.append(bi)
        prev = bi

    print("\n========== FORK TESTS ==========\n")

    # Fork from b2
    fork_base = main_blocks[0]  # b2

    # --- Fork block f1 (VALID spend) ---
    f1 = Block(fork_base.hash, pk, name="f1_valid")
    txf1 = Tx(pk, name="tx_f1_valid")
    txf1.add_input(main_blocks[0].Tx_list[0].outputs[0])  # spend b2 output
    f1_out = txf1.create_output(pk, 10, name="pk_pk_10")
    txf1.sign(sk)

    f1.add_Tx(txf1)
    f1.mine()
    chain.process_block(f1)

    # --- Fork block f2 (DOUBLE SPEND) ---
    f2 = Block(f1.hash, pk, name="f2_double_spend")
    txf2 = Tx(pk, name="tx_f2_double_spend")
    txf2.add_input(main_blocks[0].Tx_list[0].outputs[0])  # same input again
    txf2.create_output(pk, 5, name="pk_pk_5")
    txf2.sign(sk)

    f2.add_Tx(txf2)
    f2.mine()
    chain.process_block(f2)      # SHOULD FAIL

    # --- Fork block f3 (FAKE INPUT) ---
    f3 = Block(f1.hash, pk, name="f3_fake_utxo")
    txf3 = Tx(pk, name="tx_f3_fake")
    fake_utxo = TxO(pk, pk, 999, name="FAKE_UTXO")
    txf3.add_input(fake_utxo)
    txf3.create_output(pk, 1, name="pk_pk_1")
    txf3.sign(sk)

    f3.add_Tx(txf3)
    f3.mine()
    chain.process_block(f3)      # SHOULD FAIL

    print("\n========== FORK OVERTAKES MAIN CHAIN ==========\n")

    # --- Valid fork extension to trigger reorg ---
    f2_valid = Block(f1.hash, pk, name="f2_valid")
    txf2v = Tx(pk, name="tx_f2_valid")
    txf2v.add_input(f1_out)
    f2v_out = txf2v.create_output(pk, 6, name="pk_pk_6")
    txf2v.sign(sk)

    f2_valid.add_Tx(txf2v)
    f2_valid.mine()
    chain.process_block(f2_valid)

    f3_valid = Block(f2_valid.hash, pk, name="f3_valid")
    txf3v = Tx(pk, name="tx_f3_valid")
    txf3v.add_input(f2v_out)
    txf3v.create_output(pk, 3, name="pk_pk_3")
    txf3v.sign(sk)

    f3_valid.add_Tx(txf3v)
    f3_valid.mine()
    chain.process_block(f3_valid)   # SHOULD TRIGGER REORG

    print("\n========== ADVERSARIAL FEE-ONLY BLOCK TEST ==========\n")

    # Use current surface
    base = chain.surface

# Fetch a live UTxO from the DB
    row = chain.cursor.execute(
        "SELECT obj FROM UTxOs LIMIT 1"
    ).fetchone()

    assert row, "No UTxOs available to test fee-only block!"

    live_utxo = pickle.loads(row[0])
    # Spend a valid UTxO but create NO outputs, only fee
    fee_block = Block(base.hash, pk, name="fee_only_block")

    tx_fee_only = Tx(pk, name="tx_fee_only")
    tx_fee_only.add_input(live_utxo)     # spend last known good UTxO
    tx_fee_only.sign(sk)                 # no outputs => everything becomes fee

    fee_block.add_Tx(tx_fee_only)
    fee_block.mine()
    chain.process_block(fee_block)

    # Try to double-spend the SAME input in another fee-only fork block
    fee_fork = Block(fee_block.hash, pk, name="fee_only_double_spend")

    tx_fee_ds = Tx(pk, name="tx_fee_double_spend")
    tx_fee_ds.add_input(live_utxo)       # same input again
    tx_fee_ds.sign(sk)

    fee_fork.add_Tx(tx_fee_ds)
    fee_fork.mine()
    chain.process_block(fee_fork)        # MUST FAIL

    print("\n========== SNAPSHOT-CROSSING REORG TEST ==========\n")

    # Force a snapshot at current height
    chain.save_snapshot()
    snap_height = chain.height
    print(f"[TEST] Snapshot forced at height {snap_height}")

    # Extend main chain beyond snapshot
    prev = chain.surface
    utxo = spendable

    for i in range(2):
        b = Block(prev.hash, pk, name=f"post_snap_{i}")
        tx = Tx(pk, name=f"tx_post_snap_{i}")
        tx.add_input(utxo)
        utxo = tx.create_output(pk, utxo.amt - 1, name=f"pk_pk_ps_{i}")
        tx.sign(sk)

        b.add_Tx(tx)
        b.mine()
        chain.process_block(b)
        prev = b

    # Create fork that starts BEFORE snapshot
    fork_origin = main_blocks[0]   # well before snapshot

    f1 = Block(fork_origin.hash, pk, name="deep_fork_1")
    txf1 = Tx(pk, name="tx_deep_1")
    txf1.add_input(main_blocks[0].Tx_list[0].outputs[0])
    f1_out = txf1.create_output(pk, 5, name="pk_pk_5")
    txf1.sign(sk)

    f1.add_Tx(txf1)
    f1.mine()
    chain.process_block(f1)

    f2 = Block(f1.hash, pk, name="deep_fork_2")
    txf2 = Tx(pk, name="tx_deep_2")
    txf2.add_input(f1_out)
    txf2.create_output(pk, 3, name="pk_pk_3")
    txf2.sign(sk)

    f2.add_Tx(txf2)
    f2.mine()
    chain.process_block(f2)

    f3 = Block(f2.hash, pk, name="deep_fork_3")
    f3.mine()
    chain.process_block(f3)    # SHOULD TRIGGER REORG ACROSS SNAPSHOT

    print(pk.to_string().hex())
    print(sk.to_string().hex())