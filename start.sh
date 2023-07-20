#!/bin/bash
nohup ./server.py > lserver.log 2>&1 &
nohup ./wallet.py > lwallet.log 2>&1 &
