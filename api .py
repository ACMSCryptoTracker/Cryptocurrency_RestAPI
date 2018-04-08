import os,shutil,sys
from flask.json import dumps
from flask.json import JSONEncoder
from flask import Flask, request, redirect, url_for,render_template,jsonify,json
from werkzeug import secure_filename
from flask_jsglue import JSGlue
from multiprocessing import Process, Value
from flask import session
import psycopg2
import requests
import configparser
from threading import Thread
import urllib3
import time
urllib3.disable_warnings()

#Read Config File 
Config = configparser.ConfigParser()
Config.read("config.ini")

#Get database info from config file
hostname = Config.get("cryptocurrency","hostname") 
username = Config.get("cryptocurrency","username")
password = Config.get("cryptocurrency","password")
database = Config.get("cryptocurrency","database")
port=Config.get("cryptocurrency","port")
url = Config.get("cryptocurrency","url")

conn = psycopg2.connect(host=hostname, user=username, password=password, dbname=database,port=port)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
curr = conn.cursor()


app = Flask(__name__)
@app.route('/', methods=['GET','POST'])
def home():
	return "Home Page"

@app.route('/currentData',methods=['GET','POST'])
def currentData():
	curr_list=[]
	json_object={}
	selectQuery="select currency from currency_current"	
  	curr.execute(selectQuery)
	conn.commit()
	if curr.rowcount == 0:
		json_object['Success']=0
		json_object['message']="Error"
	else:
		result=curr.fetchall()
		for r in result :
			curr_list.append(r[0])
		#return jsonify(curr_list)
		json_object['Success']=1
		json_object['message']="Successfully Fetched Data"
		json_object['data']=curr_list
	return jsonify(json_object)

@app.route('/setAlert', methods=['GET','POST'])
def setAlert():
	userid=request.args.get('userid')
	alert_type=request.args.get('type')
	currency_sym=request.args.get('currency_symbol')
	conversion_sym=request.args.get('conversion_symbol')
	insertQuery=""
	if(alert_type == 'THRESHOLD_ALERT'):
		price=request.args.get('price')
		threshold_min=request.args.get('threshold_min')
		threshold_max=request.args.get('threshold_max')
		insertQuery="insert into public.user(userid,alert_type,coin_symbol,conversion_symbol,price,threshold_min,threshold_max) values ({}.'{}','{}','{}',{},{},{})".format(userid,alert_type,currency_sym,conversion_sym,price,threshold_min,threshold_max)
	elif(alert_type == 'PRICE_ALERT'):
		price=request.args.get('price')
		price_inc_by=request.args.get('price_inc_by')
		price_dec_by=request.args.get('price_dec_by')
		insertQuery="insert into public.user(userid,alert_type,coin_symbol,conversion_symbol,price,price_inc_by,price_dec_by) values ({}.'{}','{}','{}',{},{},{})".format(userid,alert_type,currency_sym,conversion_sym,price,price_inc_by,price_dec_by)
	elif(alert_type == 'VOLUME_ALERT'):
		volume=request.args.get('volume')
		volume_inc_by=request.args.get('volume_inc_by')
		volume_dec_by=request.args.get('volume_dec_by')
		insertQuery="insert into public.user(userid,alert_type,coin_symbol,conversion_symbol,volume,volume_inc_by,volume_dec_by) values ({}.'{}','{}','{}',{},{},{})".format(userid,alert_type,currency_sym,conversion_sym,volume,volume_inc_by,volume_dec_by)
	elif(alert_type == 'MARKETCAP_ALERT'):
		marketcap=request.args.get('marketcap')
		marketcap_inc_by=request.args.get('marketcap_inc_by')
		marketcap_dec_by=request.args.get('marketcap_dec_by')
		insertQuery="insert into public.user(userid,alert_type,coin_symbol,conversion_symbol,marketcap,marketcap_inc_by,marketcap_dec_by) values ({}.'{}','{}','{}',{},{},{})".format(userid,alert_type,currency_sym,conversion_sym,marketcap,marketcap_inc_by,marketcap_dec_by)
	curr.execute(insertQuery)
	conn.commit()
	json_object['Success']=1
	json_object['Message']="Successfully insert Data"
	return jsonify(json_object),200
		
@app.route('/login',methods=['POST','GET'])
def login():
	email=request.args.get('email')
	password=request.args.get('password')
	#email='urjakothari5@gmail.com'
	#password='abcd'	
	selectQuery="select * from public.user where email='{}'".format(email)
	curr.execute(selectQuery)
	json_object={}
	if curr.rowcount == 0:
		json_object['Success']=0
		json_object['message']="Email is not registered"
		return jsonify(json_object),404
	else:
		result=curr.fetchall()
		if result[0][1] == password:
			json_object['Success']=1
			json_object['Message']="Successfully login"
			json_object['email']=result[0][2]
			json_object['name']=result[0][3]
			return jsonify(json_object),200
		else:
			json_object['Success']=0
			json_object['message']="Incorrect Password"
			return jsonify(json_object),404

@app.route('/registeration',methods=['POST','GET'])	
def registeration():
	name=request.args.get('name')
	email=request.args.get('email')
	password=request.args.get('password')
	curr.execute("select * from public.user where email='{}'".format(email))
	json_object={}
	if(curr.rowcount == 0): 
		insertQuery="insert into public.user(name,email,password) values ('{}','{}','{}')".format(name,email,password)
		curr.execute(insertQuery)
		conn.commit()
		json_object['Success']=1
		json_object['Message']="Successfully insert Data"
		return jsonify(json_object),200
	else:
		json_object['Success']=0
		json_object['Message']="This email is already registered"
		return jsonify(json_object),404

@app.route("/compareGraphs",methods=['GET','POST'])
def LineGraph():
    json_object={}
    if 'duration' in request.args:
        duration=request.args['duration']
        if duration in ['day','month','year']:
	    selectQuery="select path from public.filepath where duration='{}' and crypto_name='{}'".format(duration,'All')
	    curr.execute(selectQuery)
	    result=curr.fetchall()
	     
            json_object['Success']=1
            json_object['message']="Successfully rendered graph"
            json_object['data']=result[0][0]
            return jsonify(json_object)
        else:
            json_object['Success']=0
            json_object['message']="Invalid parameter value"
            json_object['data']='null'
            return jsonify(json_object)
    else:
        json_object['Success']=0
        json_object['message']="Missing Parameters"
        json_object['data']='null'
        return jsonify(json_object)

@app.route("/coinGraph",methods=['GET','POST'])
def IndividualGraph():
    json_object={}
    if 'cryptoname' and 'duration' in request.args:
        cryptoname=request.args['cryptoname']
        duration=request.args['duration']
        
        if cryptoname in ['BTC','ETH','XRP','LTC','BCH'] and duration in ['day','month','year']:
            selectQuery="select path from public.filepath where duration='{}' and crypto_name='{}'".format(duration,cryptoname)
	    curr.execute(selectQuery)
	    result=curr.fetchall()
            json_object['Success']=1
            json_object['message']='Succesfully rendered chart'
            json_object['data']=result[0][0]
            return jsonify(json_object)
        else:
            json_object['Success']=0
            json_object['message']='Invalid Parameter values'
            json_object['data']='null'
            return jsonify(json_object)
    else:
        json_object['Success']=0
        json_object['message']="Missing Paramters"
        json_object['data']='null'
        return jsonify(json_object)
    
        #return "Invalid Paramters"
              	
			
if (__name__ == "__main__"):
	app.run(debug=True,use_reloader=False)
	conn.close()
