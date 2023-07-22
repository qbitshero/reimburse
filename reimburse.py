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

fee_record_list = []
token_list = []

def load_config():
    global approver1_address, approver1_private_key, approver1_view_key
    global approver2_address, approver2_private_key, approver2_view_key
    global fee_record_list, token_list

    fd = open("reimburse.conf", "r+")
    approver1_address = fd.readline().strip()
    approver1_private_key = fd.readline().strip()
    approver1_view_key = fd.readline().strip()
    approver2_address = fd.readline().strip()
    approver2_private_key = fd.readline().strip()
    approver2_view_key = fd.readline().strip()

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

    fd.write(fee_record_list[0])
    fd.write(fee_record_list[1])
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
        return record_plain
    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        logging.error("Failed to decrypt cipher record.\n%s" % error_output)

    return "Error"

@app.route("/")
def home():
    return render_template('reimburse.html')

@app.route("/first_approve")
def first_approve():
    logging.info("@first_approve")
    return render_template('reimburse.html')

@app.route("/second_approve")
def second_approve():
    logging.info("@second_approve")
    return render_template('reimburse.html')

@app.route('/decrypt_receipt', methods=['POST'])
def decrypt_receipt():
    global approver1_view_key, approver2_view_key

    cipher = request.form.get('receipt')
    approver = request.form.get('approver')
    view_key = ''
    if approver == '1':
        view_key = approver1_view_key
    else:
        view_key = approver2_view_key

    record = decrypt_record(cipher, view_key)

    if record ==  "Error":
        logging.error("Failed to dectypt receipt.")

    logging.info("plain receipt: %s" % record);
    return jsonify({"receipt": record})

@app.route('/approve', methods=['POST'])
def approve():
    receipt = request.form.get('receipt')
    approver = request.form.get('approver')
    logging.info("@approve receipt = %s, approver = %s" % (receipt, approver))
    return jsonify({"receipt" : "=================="})

@app.route('/reject', methods=['POST'])
def reject():
    receipt = request.form.get('receipt')
    approver = request.form.get('approver')
    logging.info("@reject receipt = %s, approver = %s" % (receipt, approver))
    return jsonify({"reject" : "=================="})

# user signs up with aleo account, and gets an login token
@app.route('/sign_up', methods=['POST'])
def sign_up():
    address = request.form['address'].strip()
    logging.info("start sign up for %s" % address)
    (error, token) = create_account(address = address, amount = SERVICE1_CREDITS, service_id = SERVICE1_ID)
    logging.info("end sign up")

    return render_template('index.html', error = error, token = token)

# user signs in with cipher certificate
@app.route('/login', methods=['POST'])
def login():
    cipher_cert = request.form['cert'].strip()
    logging.info("cipher certificate: %s\n" % cipher_cert)

    cert = decrypt_record(cipher_cert.strip()).strip()

    cmd = exe_cmd_prefix + aleo_program + 'check_cert '
    input_params = '\"%s\" %uu64' % (cert, SERVICE1_UNIT)
    cmd += input_params
    cmd += ''' --private-key ''' + server_private_key
    cmd += query
    cmd += broadcast
    cmd += fee_prefix
    cmd += server_fee_records[-1] 

    logging.info(get_current_height())
    logging.info(cmd)
    result = False
    error = ""
    try:
        output = subprocess.check_output(cmd, shell=True)
        logging.info(output)
        if output.find("Successfully") >= 0:
            index = output.rfind("at1")
            if index >= 0:
                trxid = output[index:].strip()
                trx = get_transaction(trxid)
                logging.info(trx)

                fee_record = "Error"
                if trx != "":
                    fee_record_cipher = trx["fee"]["transition"]["outputs"][0]["value"]
                    fee_record = decrypt_record(fee_record_cipher)
                    result = True
                else:
                    error = "Failed to query transaction. Please check it on block chain. %s" % trxid

                if fee_record != "Error":
                    fee_record = '\"' + fee_record + '\"'
                    server_fee_records.append(fee_record)
                    save_config()
                else:
                    if error == "":
                        error = "Failed to decrypt fee record cipher."
                    logging.error(error)

            else:
                error = "No transaction found in the successful result."
                logging.error(error)
        else:
            error = "Failed to excute transaction. Please try it later."
            logging.error("Faild to excute: \n%s" % cmd)

    except subprocess.CalledProcessError as e:
        error_output = e.output.decode().strip()
        logging.error("Subprocess Error: %s" % error_output)
        error = "Subprocess Error: %s" % error_output

    return render_template('index.html', result = result, error = error)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    load_config()

    app.run(host = '0.0.0.0', port = 8851)
