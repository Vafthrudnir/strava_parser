#!/bin/bash

export CLIENT_SECRET=`cat client_secret`
export REFRESH_PASSWORD=`cat refresh_password`
export FLASK_APP=main.py
export FLASK_ENV=development
flask run #--host=0.0.0.0
