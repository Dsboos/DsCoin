#Custom imports
from dsc.common.prettyprint import warn, fail, success, info
from dsc.common.transactions import TxO, Tx
from dsc.common.blocks import Block, CBTx
from dsc.client.wallet_handler import WalletHandler
from dsc.client.chain_handler import ChainHandler
from dsc.client.node_client import NodeClient
from dsc.client.login import DsCoinLogin
from dsc.client.ui.ui import DsCoinUI, CreateBlockUI, SwitchNodeUI
#PySide6 imports
from PySide6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem, QDialog, QTreeWidgetItem
from PySide6.QtCore import QTimer, Qt
from qasync import QEventLoop
import qdarktheme
#Other imports
from pathlib import Path
import random, sys, pickle, ecdsa, asyncio


class DsCoinClient(DsCoinUI):
    def __init__(self, wh: WalletHandler, ch: ChainHandler, nc: NodeClient):
        super().__init__()

        #Button Cooldowns
        #Submit cooldown
        self.submission_cooldown = QTimer(self)
        self.submission_cooldown.setSingleShot(True) # Timer runs only once
        self.submission_cooldown.timeout.connect(lambda: self.sign_btn.setEnabled(True))
        self.submission_cooldown.timeout.connect(lambda: self.submit_btn.setEnabled(True))
        self.submission_cooldown_dur = 3000 # 3 second cooldown
        
        #Connections
        self.change_wallet_btn.clicked.connect(self.change_wallet)
        self.switch_node_btn.clicked.connect(self.switch_node)
        #Wallet Tab
        self.add_btn.clicked.connect(self.add_output)
        self.remainder_btn.clicked.connect(self.add_remainder)
        self.del_tx_btn.clicked.connect(self.del_tx)
        self.clear_btn.clicked.connect(self.clear_output_form)
        self.refresh_btn.clicked.connect(self.update_inputs)
        self.select_all_btn.clicked.connect(self.select_all_inputs)
        self.input_tx_list.itemChanged.connect(self.update_tx_data)
        self.sign_btn.clicked.connect(self.compile_tx)
        #Mine Tab
        self.refresh_mempool_btn.clicked.connect(self.mempool_viewer_refresh)
        self.create_block_btn.clicked.connect(self.create_block)
        self.del_block_btn.clicked.connect(self.del_block)
        self.mine_btn.clicked.connect(self.mine_block)
        self.mine_preset_menu.currentIndexChanged.connect(self.update_preset)
        self.mempool_list.itemChanged.connect(self.insert_tx)
        self.select_limit_btn.clicked.connect(self.select_limit)
        self.add_cb_btn.clicked.connect(self.create_cbtx)
        self.submit_btn.clicked.connect(self.compile_block)

        #Application variables
        self.output_total = 0
        self.input_total = 0
        self.select_all_toggle = False
        self.active_block = None
        self.batch_size = 1000

        #Handlers
        self.wh = wh
        self.ch = ch
        self.nc = nc

        #initial function calls
        self.update_qotd()
        self.load_output_list()
        self.update_inputs
        self.display_error()

        self.update_preview()
        self.update_preset()
        self.display_error_m()

    #Update Functions
    def update_inputs(self):
        asyncio.create_task(self.inputs_fetcher())
  
    async def inputs_fetcher(self):
        self.setDisabled(True)
        status, msg = await self.wh.update_inputs()
        if not status and not msg:
            self.display_error("You don't have any UTxOs!")
        elif not status:
            self.display_error(f"Couldn't fetch inputs: {msg}")
        else:
            self.display_error()
            info("[Client] Updated Inputs!")
        self.load_input_list()
        self.setDisabled(False)
    
    def update_mempool(self):
        asyncio.create_task(self.mempool_fetcher())

    async def mempool_fetcher(self):
        self.setDisabled(True)
        query, msg = await self.nc.fetch_mempool()
        if query:
            self.ch.load_pending(query)
            info(f"Updated Mempool")
            self.display_error_m()
        elif not msg:
            self.display_error_m(f"Mempool is currently all empty :)")
            self.ch.load_pending([])
        else:
            self.display_error_m(f"Couldn't fetch mempool: {msg}")
        self.load_mempool()
        self.setDisabled(False)

    def update_chainstate(self):
        asyncio.create_task(self.chainstate_fetcher())

    async def chainstate_fetcher(self):
        self.setDisabled(True)
        query, msg = await self.nc.fetch_chainstate()
        if query:
            self.ch.load_chainstate(query)
            info(f"Updated Chainstate")
            self.display_error_m()
        elif not msg:
            self.display_error_m(f"Chainstate is blank :O")
        else:
            self.display_error_m(f"Couldn't fetch chainstate: {msg}")
        self.load_details()
        self.setDisabled(False)

    def update_tx_data(self):
        self.output_total = 0
        self.input_total = 0
        for row in range(self.output_tx_list.rowCount()):
            self.output_total += float(self.output_tx_list.item(row, 3).text())
        self.output_amt_label.setText(f"{self.output_total:.4f}")
        for row in range(self.input_tx_list.rowCount()):
            if self.input_tx_list.item(row, 2).checkState() != Qt.CheckState.Checked:
                continue
            self.input_total += float(self.input_tx_list.item(row, 1).text())
        self.input_amt_label.setText(f"{self.input_total:.4f}")
        remainder = self.input_total - self.output_total
        self.remainder_label.setText(f"{remainder:.4f}")
        if remainder < 0:
            self.remainder_label.setStyleSheet("color: crimson; font-weight: bold;")
        else:
            self.remainder_label.setStyleSheet("font-weight: bold;")

    def update_qotd(self):
        qotds = ["My wallet is like an onion—opening it makes me cry.",
                "I tried to follow a budget, but it unfollowed me back.",
                "How do you make a small fortune in finance? Start with a large one and invest wisely.",
                "A bank is a place that will lend you money if you can prove that you don't need it.",
                "If you think no one cares about you, try missing a couple of payments.",
                "The easiest way for your children to learn about money is for you not to have any.",
                "The trick is to stop thinking of it as 'your' money. \033[3m—IRS auditor\033[0m",
                "Always borrow money from a pessimist. They'll never expect it back.",
                "They say money talks, but mine just waves goodbye.",
                "The safest way to double your money is to fold it over and put it in your pocket.",
                "Money is the best deodorant.",
                "What's the use of happiness? It can't buy you money.",]
        idx = random.randint(0,len(qotds)-1)
        self.qotd.setText(qotds[idx])
   
    def update_preview(self, btns=True):
        if not self.active_block:
            self.add_cb_btn.setDisabled(True)
            self.mempool_list.setDisabled(True)
            self.select_limit_btn.setDisabled(True)

            self.block_nonce.setText("---")
            self.block_name.setText("---")
            self.block_diff.setText("---")
            self.block_limit.setText("---")
            self.block_prev.setText("---")
            self.block_reward.setText("---")
            self.block_mine_status.setText("No Block")
            self.block_mine_status.setStyleSheet("font-weight: bold;")

            self.block_tx_list.setPlainText("Create Block First")
            self.block_cbtx_list.setPlainText("Create Block First")
            self.hash_field.setText("")
            self.seq_field.setText("")

            if btns:
                self.create_block_btn.setDisabled(False)
                self.del_block_btn.setDisabled(True)
                self.mine_btn.setDisabled(True)
                self.submit_btn.setDisabled(True)
            return
        
        self.add_cb_btn.setDisabled(False)
        self.mempool_list.setDisabled(False)
        self.select_limit_btn.setDisabled(False)

        b = self.active_block
        self.block_nonce.setText(b.nonce)
        self.block_name.setText(b.name)
        self.block_diff.setText(str(b.difficulty))
        self.block_limit.setText(str(b.Tx_limit))
        self.block_prev.setText(b.prevh)
        self.block_reward.setText(str(b.mine_reward))
        self.block_mine_status.setText("Mined" if b.isMined() else "Not Mined")
        self.block_mine_status.setStyleSheet("font-weight: bold; color: lime;" if b.isMined() else "font-weight: bold; color: orange;")

        cbtx_block = ""
        tx_block = ""
        for tx in b.Tx_list:
            tx_block += f"{tx.hash[:30]}... \tIn Amt: {tx.inputs_amt} \tOut Amt: {tx.outputs_amt}\n"
            if tx.Tx_fee:
                cbtx_block += f"{tx.Tx_fee.hash[:30]}... \tType: {tx.Tx_fee.type} \tAmt: {tx.Tx_fee.amt}\n"
        for cbtx in b.CBTx_list:
            cbtx_block += f"{cbtx.hash[:30]}... \tType: {cbtx.type} \tAmt: {cbtx.amt}\n"

        self.block_tx_list.setPlainText(tx_block)
        self.block_cbtx_list.setPlainText(cbtx_block)
        self.hash_field.setText(b.hash_block())
        self.seq_field.setText(str(b.mine_seq))

        if btns:
            self.create_block_btn.setDisabled(True)
            self.del_block_btn.setDisabled(False)
            self.mine_btn.setDisabled(False)

        if self.active_block.isMined():
            self.submit_btn.setDisabled(False)
        else:
            self.submit_btn.setDisabled(True)
        
    def update_preset(self):
        preset = self.mine_preset_menu.currentIndex()
        preset_mapping = {0: 1000, 1:8000, 2:20000, 3:50000, 4:100000}
        self.batch_size = preset_mapping[preset]

    async def update_chain_viewer(self):
        self.setDisabled(True)

    #Addition/Creation Functions
    def add_output(self):
        name = self.tx_name_field.text().strip()
        pk2 = self.pk2_field.toPlainText().strip().replace("\n", "")
        amt = self.amt_field.value()
        res, msg = self.wh.add_output(pk2, amt, name)
        if not res:
            self.display_error(msg)
            return
        self.load_output_list()
    
    def add_remainder(self):
        remainder = self.input_total - self.output_total
        if remainder > 0:
            self.tx_name_field.setText("Remainder Amount")
            self.pk2_field.setPlainText(self.wh.active_pks)
            self.amt_field.setValue(remainder)
        else:
            self.display_error("Remainder is less than or equal to Zero!")

    def create_block(self):
        dialog = CreateBlockDialog(self.ch)
        self.update_chainstate()    #Update chainstate before block creation to get latest details when loading button is clicked
        dialog.show()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        name = dialog.block_name_field.text()
        diff = dialog.diff_field.value()
        limit = dialog.limit_field.value()
        reward = dialog.reward_field.value()
        prev = dialog.prev_field.text()
        if not prev:
            self.display_error_m("Block not created: Need Previous Block's address!")
            return
        self.active_block = Block(prev, self.wh.active_pk, reward, limit, diff)
        self.active_block.add_CBTx(CBTx(self.active_block.miner, self.active_block.mine_reward, type="reward")) #Add the miner's reward
        if name:
            self.active_block.name = name
        self.update_preview()
        
    def insert_tx(self):
        if not self.active_block:
            self.display_error_m("How'd you even do that? You need a block first!")
            return
        self.active_block.Tx_list = []  #Start from a blank slate
        for row in range(self.mempool_list.rowCount()):
            if self.mempool_list.item(row, 2).checkState() != Qt.CheckState.Checked:
                continue
            txh = self.mempool_list.item(row, 0).text()
            query = self.ch.get_tx_from_hash(txh)
            if not query:
                self.display_error_m("Couldn't find this Tx. Please refresh your mempool.")
            tx = pickle.loads(query[0])
            if not self.active_block.add_Tx(tx):
                self.display_error_m("One or more Tx were not added: Tx Limit reached!")
                return
        self.update_preview(btns=False)
        self.display_error_m()

    def create_cbtx(self):
        if not self.active_block:
            self.display_error_m("Create a block first dawg ;o;")
            return
        name = self.cb_name_field.text()
        pks = self.cb_pk_field.toPlainText().strip().replace("\n", "")
        amt = self.cb_amt_field.value()
        password = self.cb_password_field.text().strip()
        if not pks:
            self.display_error_m("Please enter the recipient key honeypie ;-;")
            return
        if not amt:
            self.display_error_m("Enter an amount for coinbase, my cutie patootie")
            return
        try:
            pk = ecdsa.VerifyingKey.from_string(bytes.fromhex(pks), curve=ecdsa.SECP256k1)
        except:
            self.display_error_m("Invalid key -_-")
            return
        cbtx = CBTx(pk, amt, "addition", password=password)
        if name:
            cbtx.name = name
        self.active_block.add_CBTx(cbtx)
        self.display_error_m()
        self.update_preview(btns=False)

    #Deletion Functions
    def del_tx(self):
        selected_rows =  { index.row() for index in self.output_tx_list.selectedIndexes() }
        for row in selected_rows:
            o_hash = self.output_tx_list.model().index(row, 2).data()
            self.wh.del_output(o_hash)
        self.load_output_list()

    def clear_output_form(self):
        self.tx_name_field.clear()
        self.pk2_field.clear()
        self.amt_field.setValue(0)
        self.display_error()    
    
    def del_block(self):
        reply = QMessageBox.question(self, "Delete Block", 
                                     "Are you sure you want to delete this block?", 
                                     defaultButton=QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        self.active_block = None
        self.update_preview()

    #Loading and Updating Functions
    def load_output_list(self):
        self.output_tx_list.clearContents()
        self.output_tx_list.setRowCount(0)
        outputs = self.wh.get_outputs()
        row = 0
        for output in outputs:
            self.output_tx_list.insertRow(row)
            self.output_tx_list.setItem(row, 0, QTableWidgetItem(output[1]))
            self.output_tx_list.setItem(row, 1, QTableWidgetItem(output[2]))
            self.output_tx_list.setItem(row, 2, QTableWidgetItem(output[3]))
            self.output_tx_list.setItem(row, 3, QTableWidgetItem(str(output[4])))   
            row += 1 
        self.update_tx_data()
    
    def load_input_list(self):
        self.input_tx_list.blockSignals(True)
        self.input_tx_list.clearContents()
        self.input_tx_list.setRowCount(0)
        inputs = self.wh.get_inputs()
        row = 0
        for input in inputs:
            self.input_tx_list.insertRow(row)
            self.input_tx_list.setItem(row, 0, QTableWidgetItem(input[1]))
            self.input_tx_list.setItem(row, 1, QTableWidgetItem(str(input[3])))
            checkbox_itm = QTableWidgetItem()
            checkbox_itm.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_itm.setCheckState(Qt.CheckState.Unchecked)
            self.input_tx_list.setItem(row, 2, checkbox_itm)     
            row += 1 
        self.input_tx_list.blockSignals(False)
        self.update_tx_data()

    def load_mempool(self):
        self.mempool_list.blockSignals(True)
        self.mempool_list.clearContents()
        self.mempool_list.setRowCount(0)
        row = 0
        query = self.ch.get_pending()
        for tx in query:
            self.mempool_list.insertRow(row)
            self.mempool_list.setItem(row, 0, QTableWidgetItem(tx[1]))
            self.mempool_list.setItem(row, 1, QTableWidgetItem(str(tx[2])))
            checkbox_itm = QTableWidgetItem()
            checkbox_itm.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_itm.setCheckState(Qt.CheckState.Unchecked)
            self.mempool_list.setItem(row, 2, checkbox_itm)     
            row += 1 
        self.mempool_list.blockSignals(False)          

    def load_details(self):#DEPRECATED FUNC, DIALOG HANDLES THIS NOW
        query = self.ch.get_chainstate()
        if not query:
            return
        surface = pickle.loads(query[4])
        surfaceh = surface.hash
        diff = query[5]
        limit = query[6]
        reward = query[7]

    def load_blocks(self):
        pass

    #Submission Functions
    def compile_tx(self):
        self.sign_btn.setEnabled(False)
        #Check if remainder is greater or equal to zero
        if (self.input_total - self.output_total) < 0:
            self.display_error("Cannot submit Tx with negative remainder!")
            self.sign_btn.setEnabled(True)
            return
        tx = Tx(self.wh.active_pk)
        #Add all selected inputs to Tx
        for row in range(self.input_tx_list.rowCount()):
            if self.input_tx_list.item(row, 2).checkState() != Qt.CheckState.Checked:
                continue
            txih = self.input_tx_list.item(row, 0).text()
            txib = self.wh.get_input_from_hash(txih)[4]
            tx.add_input(pickle.loads(txib))
        #Add all outputs to Tx
        for row in range(self.output_tx_list.rowCount()):
            txoh = self.output_tx_list.item(row, 2).text()
            txob = self.wh.get_output_from_hash(txoh)[5]
            tx.add_output(pickle.loads(txob))
        if self.output_tx_list.rowCount() == 0:
            reply = QMessageBox.warning(self, "No Outputs", 
                                     "You have no outputs added. Any selected inputs will go towards transaction fees.\nDo you want to still continue?", 
                                     defaultButton=QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                self.sign_btn.setEnabled(True)
                return
        tx.sign(self.wh.active_sk)
        asyncio.create_task(self.submit_tx(tx))
        self.submission_cooldown.start(self.submission_cooldown_dur)

    async def submit_tx(self, tx):
        self.setDisabled(True)
        status, msg = await self.nc.submit_tx(tx)
        if not status:
            self.display_error(f"Error submitting Tx: {msg}")
        else:
            self.display_error()
        self.wh.del_all_outputs()
        self.load_output_list()
        self.setDisabled(False)
    
    def compile_block(self):
        self.submit_btn.setEnabled(False)
        asyncio.create_task(self.submit_block(self.active_block))
        self.submission_cooldown.start(self.submission_cooldown_dur)

    async def submit_block(self, block):
        self.setDisabled(True)
        status, msg = await self.nc.submit_block(block)
        if not status:
            self.display_error_m(f"Error submitting block: {msg}")
        else:
            self.display_error_m()
            self.active_block = None
            self.update_preview()
            self.mempool_viewer_refresh()
        self.setDisabled(False)

    #Utility Functions
    def change_wallet(self):
        self.setDisabled(True)
        login = DsCoinLogin(self.wh)     
        if login.exec() != QDialog.DialogCode.Accepted:
            self.setDisabled(False)
            return
        self.clear_output_form()
        self.load_input_list()
        self.load_output_list()
        self.update_qotd()
        self.update_inputs()

        self.active_block = None
        self.update_preview()
        self.mempool_viewer_refresh()
        self.setDisabled(False)

    def switch_node(self):
        dialog = SwitchNodeUI()
        dialog.addr_field.setText("localhost")
        dialog.port_field.setValue(8000)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.nc.host = dialog.addr_field.text()
        self.nc.port = dialog.port_field.value()
        self.update_inputs()
        self.update_mempool()

    def select_all_inputs(self):
        if not self.select_all_toggle:
            for row in range(self.input_tx_list.rowCount()):
                self.input_tx_list.item(row, 2).setCheckState(Qt.CheckState.Checked)
        else:
            for row in range(self.input_tx_list.rowCount()):
                self.input_tx_list.item(row, 2).setCheckState(Qt.CheckState.Unchecked)
        self.select_all_toggle = not self.select_all_toggle

    def select_limit(self):
        if not self.active_block:
            self.display_error_m("Wha. Make a block first my guy!")
            return
        for row in range(self.mempool_list.rowCount()):
            if row >= self.active_block.Tx_limit:
                return
            self.mempool_list.item(row, 2).setCheckState(Qt.CheckState.Checked)

    async def mine_block_task(self):
        self.del_block_btn.setDisabled(True)
        self.mine_btn.setDisabled(True)
        self.cancel_btn.show()

        self.mining_cancelled = False
        
        self.cancel_btn.clicked.connect(self.cancel_mining)
        batch_size = self.batch_size

        b = self.active_block
        try:
            while not b.isMined() and not self.mining_cancelled:
                for i in range(batch_size):
                    if b.isMined() or self.mining_cancelled:
                        break
                    b.mine_seq += 1
                await asyncio.sleep(0)
                self.update_preview(btns=False)
        finally:
            self.update_preview(btns=False)
            self.mine_btn.setDisabled(False)
            self.cancel_btn.hide()
            self.del_block_btn.setDisabled(False)

    def cancel_mining(self):
        self.mining_cancelled = True    

    def mine_block(self):
        asyncio.create_task(self.mine_block_task())

    def mempool_viewer_refresh(self):
        self.update_mempool()
        self.load_mempool()

    def display_error(self, msg=None):
        if not msg:
            self.error_label.setText("")
            return
        self.error_label.setText(msg)

    def display_error_m(self, msg=None):
        if not msg:
            self.mine_error_label.setText("")
            return
        self.mine_error_label.setText(msg)

class CreateBlockDialog(CreateBlockUI):
    def __init__(self, mh):
        super().__init__()
        self.ch = mh
        self.load_details_btn.clicked.connect(self.load_details)

    def load_details(self):
        query = self.ch.get_chainstate()
        if not query:
            return
        surface = pickle.loads(query[4])
        surfaceh = surface.hash
        diff = query[5]
        limit = query[6]
        reward = query[7]

        self.prev_field.setText(surfaceh)
        self.diff_field.setValue(diff)
        self.limit_field.setValue(limit)
        self.reward_field.setValue(reward)
    
def createKeypair():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    pk = sk.get_verifying_key()
    success(f"[Public Key]  {pk.to_string().hex()}")
    success(f"[Private Key] {sk.to_string().hex()}")

def main():
    createKeypair()

    #Bootstrap Node
    HOST, PORT =  ("nodeabrar.ddns.net", 8000)

    app = QApplication()
    qdarktheme.setup_theme("dark", "sharp")

    nc = NodeClient(HOST, PORT)
    wh = WalletHandler(nc)
    ch = ChainHandler()
    login = DsCoinLogin(wh)
    if login.exec() != QDialog.DialogCode.Accepted:
        exit(1)
        
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    win = DsCoinClient(wh, ch, nc)
    win.show()
    with loop:
        QTimer.singleShot(0, win.update_chainstate) #Initial fetch and updates from Node
        QTimer.singleShot(0, win.update_inputs)
        QTimer.singleShot(0, win.update_mempool)
        loop.run_forever()

if __name__ == "__main__":
    main() 