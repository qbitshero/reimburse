# login

## Introduction
This is a demo for 'login_token' which is an aleo program you can find on <https://github.com/qbitshero/login_token>.
It is a solution for keeping identity privacy. In this demo, there is a simple web wallet and a simple web login server. You can sign up on the server, then get a cipher token binded to the server. Then decrypt and save the token in wallet. After that, you can get certificate with the token in wallet. At last, you can sign in server with the certificate. The token contains 'amount' field. Some fee is consumed by login everytime. When all the 'amount' has been consumed, the token would be invalid and we need sign up again.

## How to run this demo backend

### The components of this demo
We hope to log in to all kinds of Apps by aleo account, so a simple wallet is needed in our demo. We also provide a simple login server, which can be an entrance of Apps. To make it easy, we bind aleo account, private key and view key to login server and wallet.
The main files are server.py, wallet.py, server.conf, wallet.conf, shutdown.sh and start.sh.

### Prerequisite
On the environment, snarkos and python2 (including flask framework) must be installed. New aleo account is not neccessary because we have binded account, private key and view key to this demo. You can check these info in server.conf and wallet.conf.

### Deploy wallet and login server
Before start servers, you need check account info in server.conf.
```
aleo1s6axzuxkxz8ksxdzqpnvktglraf7k3mayt05lhx652vc5zw53gqs326sjn
APrivateKey1zkp5Y4Ytn8mLaim2frzYJb5Ykv3SaTJxGuamByUyYYjf7Vb
AViewKey1odyPNFbkSds4qWpXYJtSGTSfBmDANWX1w8PpDWPkWj4v
"{
  owner: aleo1s6axzuxkxz8ksxdzqpnvktglraf7k3mayt05lhx652vc5zw53gqs326sjn.private,
  microcredits: 26126745u64.private,
  _nonce: 2323413134090000994936801575955738127056384399453514610532171369961822018768group.public
}"
```

And check account info in wallet.conf.
```
aleo18pfln645uyxsg5x7qq6pc4wca8gegkfgk83j9e89vllvlr8cccpq97l6sj
APrivateKey1zkpCZ3ZMaYNcHpdy1KgzFTueptSFfqDQDvgG7CGcjn4aRvf
AViewKey1dsZSvKEDohsqHsUL1JRXLme94Vo5WeLnLDo5FpBhjhnX
"{
  owner: aleo18pfln645uyxsg5x7qq6pc4wca8gegkfgk83j9e89vllvlr8cccpq97l6sj.private,
  microcredits: 17559032u64.private,
  _nonce: 7333537429231212666926831191472084069987067191615621638294926114254474673099group.public
}"
``` 

**You need transfer aleo credits to aleo1s6axzuxkxz8ksxdzqpnvktglraf7k3mayt05lhx652vc5zw53gqs326sjn and aleo18pfln645uyxsg5x7qq6pc4wca8gegkfgk83j9e89vllvlr8cccpq97l6sj. Then replace the credits records in server.conf and wallet.conf. Don't delete the double quotations near credits record.**

Now, let's start the demo.
```bash
./start.sh
```
This will start login server and wallet server, and output the log info to lserver.log and lwallet.log. You can open the web page on explorer now.

**Note: We use ports 8840 and 8841. Please modify them in server.py and wallet.py if neccessary.**

## The demo process with UI

### Outline
We give a UI demo, which contains 'sign up', 'save token', 'get certificate', 'sign in' and 'split identity'. These operations will trigger the transactions in 'login_token' on <https://github.com/qbitshero/login_token>. But 'init_service' transaction is not triggered, because we have already executed it with account aleo1s6axzuxkxz8ksxdzqpnvktglraf7k3mayt05lhx652vc5zw53gqs326sjn which is binded to login server.   
**You can test our demo on <http://182.44.44.148:8840/> and <http://182.44.44.148:8841/>. These 2 sites are very slow(some operation consumes 90s), because we have no GPU prover. If you cannot access these sites, please contact us. qbitshero@126.com**

### Step1. Sign up
First, let's access server's home site.
We have no login token at present, so we need sign up with account 'aleo18pfln645uyxsg5x7qq6pc4wca8gegkfgk83j9e89vllvlr8cccpq97l6sj'. This account is binded to our demo, please don't use other account. This operation triggers 'create_user' transaction in 'login_token' on aleo chain. Refer to the following figure.
![avatar](res/signup.png)

### Step2. Get cipher login token
When step1 succeeds, we get cipher login token owned by 'aleo18pfln645uyxsg5x7qq6pc4wca8gegkfgk83j9e89vllvlr8cccpq97l6sj'. This token can be used many times, depends on the amount in token and login cost. Refer to the following figure.
![avatar](res/ciphertoken.png)

### Step3. Save token
Now we copy the cipher token in step2, and access wallet web site. Fill the cipher token into textbox, then click 'Save Token' button. This operation triggers no transaction, only decrypting cipher locally. Refer to the following figure.
![avatar](res/savetoken.png)

### Step4. Get plain login token
When step3 succeeds, we get plain login token. It has been saved to the wallet. Refer to the following figure.
![avatar](res/logintoken.png)

### Step5. Get certificate
Fill 'aleo1s6axzuxkxz8ksxdzqpnvktglraf7k3mayt05lhx652vc5zw53gqs326sjn' into Server Address textbox, then click 'Get Certificate' button. This operation triggers 'login' transaction in 'login_token' on aleo chain. And returns certificate and remaining token. We can use the remaining token next time until the amount in token is 0. Refer to the following figure.
![avatar](res/getcert.png)

### Step6. Certificate
When step5 succeeds, we get certificate. Refer to the following figure.
![avatar](res/cert.png)

### Step7. Sign in
Now we copy the certificate in step6, and return to login server's home site. Fill the certificate into textbox, then click 'Sign in' button. Because the cerfificate is cipher. The server will decrypt it first, and triggers 'check_cert' transaction in 'login_token' on aleo chain. Refer to the following figure.
![avatar](res/signin.png)

### Step8. Succeed
When step7 succeeds, the whole login process finish. **We stress that, from this on, the server can manage user session designed by itself. For exmaple, the cert keeps valid in 24 hours or more. The key point here is, there is no info about account in user session. And user can change a new identity with the remainint token in step5. This is what we expect.** Refer to the following figure.
![avatar](res/succeed.png)

### Step9. Split identity
It is easy to have multiple identities with one account. Just split the login token, and get certiticates from these new tokens. Every certificate is valid and no one else knows the relation between them. To demonstrate this, please replay step1 to step4. When get a plain login token, copy it. Access wallet web site, fill login token into textbox, input amount with 300000, then click 'Split Identity' button. This operation triggers 'split' transaction in 'login_token' on aleo chain. And return 2 new tokens. Refer to the following figure.
![avatar](res/split.png)

### Step10. New tokens
When step9 succeeds, we get 2 new tokens. You can continue to split identities as many as wanted. Refer to the following figure.
![avatar](res/newtokens.png)

### Debug experience
1. We use ports 8840 and 8841. If you found them already in use, maybe you run it 2 times, and you can shutdown it firstly. If these ports used by other program on the environment, please modify them in server.py and wallet.py.

2. After each successful transaction, the aleo credits record in server.conf or wallet.conf will be updated. But on failure step, we need check the status on <https://explorer.hamp.app/program?id=login_token.aleo>. 

    2.1 When the transaction is rejected, the credits record in server.conf or wallet.conf would not be updated. If the failure happeneds on wallet, transfer credits to the account binded to wallet, and replace the credits record in wallet.conf. If the failure happeneds on login server, do the same with server.conf. 

    2.2 When no rejection found on aleo explorer, the failure caused by network problem, retry the operation later.
