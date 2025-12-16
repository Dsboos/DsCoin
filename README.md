# Naming Convention:

Transaction: Tx\
Transaction Input: TxI\
Transaction Output: TxO\
Unspent Transaction: UTxO\
Coin Base Transaction: CBTx (sometimes CBTxO)

# 1. Transactions

## 1.1- TxO(sender, reciever, amount)

Fundamental unit of a Tx. Automatically created in Tx by .create_output() method.

### Methods: None

## 1.2- Tx(sender)

The Tx itself that holds all the Inputs and Outputs (+ a Tx fee)

### Methods:

.add_input(TxO)\
.create_output(reciever, amount)\
.sign(private_key)

# To-do list:

1- Add CoinBase maturity: miner rewards can only be used after 10 blocks or more are appended to that block

2- Add auto snapshot at every n blocks feature

3- Create user client, integrate transaction creation into UI, and implement client UTxO fetching

4- Create a miner client with block mining UI, and implement local mempool

5- Display copy of blockchain through a visual GUI in clients

6- Create node client with mempool and blockchain copy.

7- Connect user clients, miner clients with nodes: node mempool updates local miner mempools, node blockchain updates clients' copies

8- Create a chain verification tool that scans and verifies entire specified segment of chain.
