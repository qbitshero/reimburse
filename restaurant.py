#!/usr/bin/python

from flask import Flask, render_template, request, redirect, session, url_for
import hashlib, subprocess
import os, requests, json, time, logging

app = Flask(__name__)

SERVICE1_ID = 1
SERVICE1_UNIT = 10

exe_cmd_prefix = 'snarkos developer execute '
aleo_program = 'token_receipt.aleo '
query = ''' --query https://vm.aleo.org/api '''
broadcast = '''--broadcast https://vm.aleo.org/api/testnet3/transaction/broadcast '''
fee_prefix = '''--fee 30000 --record '''

consumer_address = ""
view_key = ""
private_key = ""
fee_record_list = []

token_list = []

selected_category = ''
selected_department = ''

def load_config():
    global consumer_address, view_key, private_key, fee_record_list, token_list

    fd = open("restaurant.conf", "r+")
    consumer_address = fd.readline().strip()
    private_key = fd.readline().strip()
    view_key = fd.readline().strip()

    records = fd.read().strip()
    end = records.find('\"', 1)
    fee_record = records[:end+1].strip()
    fee_record_list.append(fee_record)

    start = records.find('\"', end + 1)
    end = records.find('\"', start + 1)
    token = records[start:end+1].strip() 
    token_list.append(token)
    fd.close()

    if len(fee_record_list) == 0 or len(token_list) == 0:
        raise Exception("No token or fee record in restaurant.conf")

    logging.info(consumer_address)
    logging.info(private_key)
    logging.info(view_key)
    logging.info(fee_record_list[-1])
    logging.info(token_list[-1])

def save_config():
    fd = open("restaurant.conf", "w+")
    fd.write(consumer_address.strip())
    fd.write('\n')
    fd.write(private_key.strip())
    fd.write('\n')
    fd.write(view_key.strip())
    fd.write('\n')
    fd.write(fee_record_list[-1])
    fd.write('\n')
    fd.write(token_list[-1])

    fd.close()

# query transaction by transaction id
# return the transaction
def get_transaction(trx_id):
    url = "https://vm.aleo.org/api/testnet3/transaction/"
    trx_url = url + trx_id;
    logging.info("request transaction: %s" % trx_url)

    status = 0
    count = 0
    while (status != 200 and count < 10):
        response = requests.get(trx_url)
        status = response.status_code
        if status == 200:
            return response.json()

        count += 1
        time.sleep(2)

    logging.error("Failed to get transaction %s" % trx_id)
    logging.error("Response status: %d" % response.status_code)
    return ""

def get_current_height():
    response = requests.get("https://vm.aleo.org/api/testnet3/latest/height")
    status = response.status_code
    if status == 200:
        return response.json()

    return "get block height error %d" % status

# decrypt cipher record
# return the plain text record
def decrypt_record(cipher):
    cmd = "snarkos developer decrypt --ciphertext "
    cmd += cipher
    cmd += " --view-key "
    cmd += view_key
    logging.info("decrypt %s" % cmd)

    try:
        record_plain = subprocess.check_output(cmd, shell=True).strip()
        logging.info(record_plain)
        return record_plain
    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        logging.error("Failed to decrypt cipher record.\n%s" % error_output)
        return error_output

@app.route("/")
def home():
        return render_template('restaurant.html')

@app.route('/select_category', methods=["POST"])
def select_category():
    global selected_category
    selected_category = request.form.get("index")
    logging.info('selected category = %s' % selected_category)
    return 'Success'

@app.route('/select_department', methods=["POST"])
def select_department():
    global selected_department
    selected_department = request.form.get("index")
    logging.info('selected department = %s' % selected_department)
    return 'Success'

@app.route('/pay', methods=['POST'])
def pay():
    global selected_category, selected_department
    error = ''
    date = request.form['date'].strip()
    consumer = request.form['consumer'].strip()
    amount = request.form['amount'].strip()
    company = request.form['company'].strip()
    approver1 = request.form['approver'].strip()
    provider = 'aleo18pfln645uyxsg5x7qq6pc4wca8gegkfgk83j9e89vllvlr8cccpq97l6sj'

    logging.info('date = %s, consumer = %s' % (date, consumer))
    logging.info('amount = %s, category = %s, company = %s' % (amount, selected_category, company))
    logging.info('department = %s, first approver = %s' % (selected_department, approver1))

    if selected_category == '':
        error = 'Please select category'
        logging.error(error)
        return render_template('restaurant.html', error = error)
    elif selected_department == '':
        error = 'Please select department'
        logging.error(error)
        return render_template('restaurant.html', error = error)

    cmd = exe_cmd_prefix + aleo_program + 'transfer_private_with_receipt '
    input_params = '%s %s %su64 ' % (token_list[-1], provider, amount)
    receipt_info = '\"{category: %su32, date: %su32, company: %s, dep: %su32, approver: %s}\"' % (selected_category, date, company, selected_department, approver1)
    input_params += receipt_info
    cmd += input_params
    cmd += ''' --private-key ''' + private_key
    cmd += query
    cmd += broadcast
    cmd += fee_prefix
    cmd += fee_record_list[-1]

    logging.info(get_current_height())
    logging.info(cmd)

    try:
        output = subprocess.check_output(cmd, shell=True)
        logging.info(output)

        if output.find("Successfully") >= 0:
            index = output.rfind("at1")
            if index >= 0:
                trxid = output[index:].strip()
                trx = get_transaction(trxid)
                fee_record = "Error"
                if trx != "":
                    fee_record_cipher = trx["fee"]["transition"]["outputs"][0]["value"]
                    fee_record = decrypt_record(fee_record_cipher)

                    cipher_token = trx["execution"]["transitions"][0]["outputs"][0]["value"]
                    plain_token = decrypt_record(cipher_token.strip())
                    plain_token = '\"' + plain_token + '\"'
                    token_list.append(plain_token)

                    receipt = trx["execution"]["transitions"][0]["outputs"][2]["value"]
                else:
                    error = "Failed to query transaction. Please check it on block chain. %s" % trxid

                if fee_record != "Error":
                    fee_record = '\"' + fee_record + '\"'
                    fee_record_list.append(fee_record)
                    save_config()
                else:
                    if error == "":
                        error = "Failed to decrypt fee record cipher."
                    logging.error(error)

                logging.info('Receipt: %s' % receipt)
                return render_template('restaurant.html', error = error, receipt = receipt)
            else:
                error = "No transaction found in the successful result."
        else:
            logging.error("Failed to excute: \n%s" % cmd)
            error = "Failed to excute transaction. Please try it later."

    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        error = "Subprocess Error: %s" % error_output
        logging.error(error)

    return render_template('restaurant.html', error = error)


if __name__ == "__main__":
        logging.getLogger().setLevel(logging.INFO)
        load_config()

        app.run(host = '0.0.0.0', port = 8850)
