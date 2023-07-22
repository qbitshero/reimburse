#!/bin/bash
nohup ./restaurant.py > lrestaurant.log 2>&1 &
nohup ./reimburse.py > lreimburse.log 2>&1 &
