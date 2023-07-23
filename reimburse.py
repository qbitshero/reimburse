#!/usr/bin/python

from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import hashlib, subprocess
import os, requests, json, time, logging

app = Flask(__name__)

exe_cmd_prefix = 'snarkos developer execute '
aleo_program = 'token_receipt.aleo '
query = ''' --query https://vm.aleo.org/api '''
broadcast = ''' --broadcast https://vm.aleo.org/api/testnet3/transaction/broadcast '''
fee_prefix = ''' --fee 30000 --record '''
approver1_address = ''
approver1_private_key = ''
approver1_view_key = ''
approver2_address = ''
approver2_private_key = ''
approver2_view_key = ''
consumer_address = ''
consumer_private_key = ''
consumer_view_key = ''

fee_record_list = []
token_list = []

def load_config():
    global approver1_address, approver1_private_key, approver1_view_key
    global approver2_address, approver2_private_key, approver2_view_key
    global consumer_address, consumer_private_key, consumer_view_key
    global fee_record_list, token_list

    fd = open("reimburse.conf", "r+")
    approver1_address = fd.readline().strip()
    approver1_private_key = fd.readline().strip()
    approver1_view_key = fd.readline().strip()
    approver2_address = fd.readline().strip()
    approver2_private_key = fd.readline().strip()
    approver2_view_key = fd.readline().strip()

    consumer_address = fd.readline().strip()
    consumer_private_key = fd.readline().strip()
    consumer_view_key = fd.readline().strip()

    records = fd.read().strip()
    end = records.find('\"', 1)
    fee_record = records[:end+1].strip()
    fee_record_list.append(fee_record)

    start = records.find('\"', end + 1)
    end = records.find('\"', start + 1)
    fee_record = records[start:end+1].strip()
    fee_record_list.append(fee_record)

    start = records.find('\"', end + 1)
    end = records.find('\"', start + 1)
    token = records[start:end+1].strip()
    token_list.append(token)
    fd.close()

    if len(fee_record_list) == 0 or len(token_list) == 0:
        raise Exception("No token or fee record in reimburse.conf")

    logging.info("load config...")
    logging.info(approver1_address)
    logging.info(approver1_private_key)
    logging.info(approver1_view_key)
    logging.info(fee_record_list[0])

    logging.info(approver2_address)
    logging.info(approver2_private_key)
    logging.info(approver2_view_key)
    logging.info(fee_record_list[1])
    logging.info(token_list[-1])

    logging.info(consumer_address)
    logging.info(consumer_private_key)
    logging.info(consumer_view_key)

def save_config():
    fd = open("reimburse.conf", "w+")
    fd.write(approver1_address.strip())
    fd.write('\n')
    fd.write(approver1_private_key.strip())
    fd.write('\n')
    fd.write(approver1_view_key.strip())
    fd.write('\n')
    fd.write(approver2_address.strip())
    fd.write('\n')
    fd.write(approver2_private_key.strip())
    fd.write('\n')
    fd.write(approver2_view_key.strip())
    fd.write('\n')
    fd.write(consumer_address.strip())
    fd.write('\n')
    fd.write(consumer_private_key.strip())
    fd.write('\n')
    fd.write(consumer_view_key.strip())
    fd.write('\n')

    fd.write(fee_record_list[0])
    fd.write('\n')
    fd.write(fee_record_list[1])
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
def decrypt_record(cipher, view_key):
    cmd = "snarkos developer decrypt --ciphertext "
    cmd += cipher
    cmd += " --view-key "
    cmd += view_key
    logging.info("decrypt: %s" % cmd)

    try:
        record_plain = subprocess.check_output(cmd, shell=True).strip()
        start = record_plain.find('{')
        record_plain = record_plain[start:]
        logging.info(record_plain)
        return (record_plain, '')
    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        error = "Failed to decrypt cipher record.\n%s" % error_output
        logging.error(error)
        return (cipher, error)

@app.route("/")
def home():
    return render_template('reimburse.html')

@app.route('/decrypt_receipt', methods=['POST'])
def decrypt_receipt():
    global approver1_view_key, approver2_view_key

    cipher = request.form.get('receipt')
    start = cipher.find('record')
    cipher = cipher[start:]
    cs = cipher.split()
    cipher = cs[0]
    approver = request.form.get('approver')
    view_key = ''
    if approver == '1':
        view_key = approver1_view_key
    else:
        view_key = approver2_view_key

    (record, error) = decrypt_record(cipher, view_key)
    if error == '':
        logging.info("plain receipt: %s" % record);

    return jsonify({"receipt": record, "error" : error})

def check_receipt(receipt, next_approver, state, private_key, fee_index):
    cmd = exe_cmd_prefix + aleo_program + 'check_receipt '
    input_params = '\"%s\" %s %uu32 ' % (receipt, next_approver, state)
    cmd += input_params
    cmd += ''' --private-key ''' + private_key
    cmd += query
    cmd += broadcast
    cmd += fee_prefix
    cmd += fee_record_list[fee_index]

    logging.info(get_current_height())
    logging.info(cmd)
    result_receipt = ""
    error = ""

    try:
        output = subprocess.check_output(cmd, shell=True)
        logging.info(output)
        if output.find("Successfully") >= 0:
            index = output.rfind("at1")
            if index >= 0:
                trxid = output[index:].strip()
                trx = get_transaction(trxid)
                fee_record = ""
                if trx != "":
                    fee_record_cipher = trx["fee"]["transition"]["outputs"][0]["value"]
                    view_key = ''
                    if fee_index == 0:
                        view_key = approver1_view_key
                    else:
                        view_key = approver2_view_key
                    (fee_record, error) = decrypt_record(fee_record_cipher, view_key)

                    result_receipt = trx["execution"]["transitions"][0]["outputs"][0]["value"]
                else:
                    error = "Failed to query transaction. Please check it on block chain. %s" % trxid

                if  error == '':
                    fee_record = '\"' + fee_record + '\"'
                    fee_record_list[fee_index] = fee_record
                    save_config()

                logging.info('Result receipt: %s' % result_receipt)
                return (result_receipt, error)
            else:
                error = "No transaction found in the successful result."
        else:
            logging.error("Failed to excute: \n%s" % cmd)
            error = "Failed to excute transaction. Please try it later."

    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        error = "Subprocess Error: %s" % error_output
        logging.error(error)

    return (receipt, error) 

@app.route('/approve', methods=['POST'])
def approve():
    receipt = request.form.get('receipt')
    start = receipt.find('{')
    end = receipt.find('}', start+1)
    receipt = receipt[start : end+1]
    approver = request.form.get('approver')
    logging.info("@approve receipt = %s, approver = %s" % (receipt, approver))
    private_key = ''
    fee_index = 0
    state = 0

    if approver == '1':
        private_key = approver1_private_key
        state = 2
    else:
        private_key = approver2_private_key
        fee_index = 1

    (result, error) = check_receipt(receipt, approver2_address, state, private_key, fee_index)

    return jsonify({"receipt" : result, "error" : error})

@app.route('/reject', methods=['POST'])
def reject():
    receipt = request.form.get('receipt')
    start = receipt.find('{')
    end = receipt.find('}', start+1)
    receipt = receipt[start : end+1]
    approver = request.form.get('approver')
    logging.info("@reject receipt = %s, approver = %s" % (receipt, approver))
    private_key = ''
    fee_index = 0
    state = 1

    if approver == '1':
        private_key = approver1_private_key
    else:
        private_key = approver2_private_key
        fee_index = 1

    (result, error) = check_receipt(receipt, approver2_address, state, private_key, fee_index)

    return jsonify({"receipt" : result, "error" : error})

@app.route('/reimburse', methods=['POST'])
def reimburse():
    receipt = request.form.get('receipt')
    start = receipt.find('{')
    end = receipt.find('}', start+1)
    receipt = receipt[start : end+1]

    cmd = exe_cmd_prefix + aleo_program + 'reimburse '
    input_params = '\"%s\" %s ' % (receipt, token_list[-1])
    cmd += input_params
    cmd += ''' --private-key ''' + approver2_private_key
    cmd += query
    cmd += broadcast
    cmd += fee_prefix
    cmd += fee_record_list[1]

    logging.info(get_current_height())
    logging.info(cmd)
    token = ""
    error = ""

    try:
        output = subprocess.check_output(cmd, shell=True)
        logging.info(output)
        if output.find("Successfully") >= 0:
            index = output.rfind("at1")
            if index >= 0: 
                trxid = output[index:].strip()
                trx = get_transaction(trxid)
                fee_record = ""
                if trx != "":
                    fee_record_cipher = trx["fee"]["transition"]["outputs"][0]["value"]
                    (fee_record, error) = decrypt_record(fee_record_cipher, approver2_view_key)
                    if error == '':
                        fee_record = '\"' + fee_record + '\"'
                        fee_record_list[-1] = fee_record
                        save_config()
    
                    remaining_token_cipher = trx["execution"]["transitions"][0]["outputs"][0]["value"]
                    (remaining_token, error) = decrypt_record(remaining_token_cipher, approver2_view_key)
                    if error == '':
                        remaining_token = '\"' + remaining_token + '\"'
                        token_list[-1] = remaining_token
                        save_config()

                    token = trx["execution"]["transitions"][0]["outputs"][1]["value"]
                else:
                    error = "Failed to query transaction. Please check it on block chain. %s" % trxid

                logging.info('Result cipher token: %s' % token)
                if error != '':
                    token = receipt

                return jsonify({"token": token, "error": error})
            else:
                error = "No transaction found in the successful result."
        else:
            logging.error("Failed to excute: \n%s" % cmd)
            error = "Failed to excute transaction. Please try it later."

    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        error = "Subprocess Error: %s" % error_output
        logging.error(error)

    return jsonify({"token" : receipt, "error" : error})

@app.route('/decrypt_token', methods=['POST'])
def decrypt_token():
    global consumer_view_key
    cipher = request.form.get('token')

    (record, error) = decrypt_record(cipher, consumer_view_key)

    if error == '':
        logging.info("Result token: %s" % record);

    return jsonify({"token": record, "error": error})

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    load_config()

    app.run(host = '0.0.0.0', port = 8851)
