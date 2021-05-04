#!/bin/bash

export CLIENT_SECRET=`cat client_secret`
export FLASK_APP=token_saver.py
flask run --host=0.0.0.0
