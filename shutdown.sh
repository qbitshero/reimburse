#!/bin/bash
 
#shutdown server and wallet

PID_NUM=`ps -ef | grep restaurant.py | grep -v grep | wc -l`
PID=`ps -ef | grep restaurant.py | grep -v grep | awk '{print $2}'`
echo $PID
if [ $PID_NUM -ne 0 ]; then
        kill $PID
fi

PID_NUM=`ps -ef | grep reimburse.py | grep -v grep | wc -l`
PID=`ps -ef | grep reimburse.py | grep -v grep | awk '{print $2}'`
echo $PID
if [ $PID_NUM -ne 0 ]; then
        kill $PID
fi
