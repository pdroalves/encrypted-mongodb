#!/usr/bin/python
# coding: utf-8

import json
from client import Client
from secmongo import SecMongo
from pymongo import MongoClient
from time import time
from bson.json_util import dumps
from datetime import timedelta
from datetime import date
from random import randint

client = Client(Client.keygen())

client.set_attr('domain','keyword')
client.set_attr('name','static')
client.set_attr('expires_on','range')
client.set_attr('registered_on','range')
client.set_attr('updated_on','range')
client.set_attr('name_servers','static')
client.set_attr('accesses','h_add')

s = SecMongo(add_cipher_param=pow(client.ciphers['h_add'].keys['pub']['n'],2))
s.open_database('whois')
s.set_collection('encrypted')
s.drop_collection()

# load in 44s
datafile = open('synthetic_dataset.json')
dataset = json.load(datafile)

print '%d items were loaded' % len(dataset)

# encrypt in 15.4 ms
client.encrypt(dataset[0])

def load_encrypted_data(dataset):
	count = 0
	start = float(time())
	for entry in dataset:
		if (count % 100) == 0 and count > 0:
			# ~65 elements/s
			print '%d - %f elements/s' % (count, 1000.0/(float(time())-start))
			start = time()
		count = count + 1
		ct = client.encrypt(entry)
		s.insert(ct)

start = float(time())
# 7629s to load
# 6973794640 bytes
load_encrypted_data(dataset)
end = time()
print 'Encrypted data loaded in %ds' % (end-start)


#######################################################################################################################
# Exemplo de entrada:
result = s.find()
ct = result.next()
print ct
print dumps( client.decrypt( ct ),indent = 4 )

#######################################################################################################################
print "Entradas com o e-mail 'www.Joey-Bhatia.com.br' "
for x in s.find(client.get_ibe_sk(['www.Joey-Bhatia.com.br'])):
	print dumps( client.decrypt( x ),indent = 4 )

#######################################################################################################################
print "Domínio registrado a mais tempo"
result = s.find(sort=[('registered_on',SecMongo.DESCENDING)])
value = client.decrypt(result.next())
value["registered_on"] = date.fromordinal(value["registered_on"]).strftime("%Y-%m-%d") 
value["expires_on"] = date.fromordinal(value["expires_on"]).strftime("%Y-%m-%d")
value["updated_on"] = date.fromordinal(value["updated_on"]).strftime("%Y-%m-%d")
print dumps( value,indent = 4 ) 

#######################################################################################################################
print "Adiciona randint(1,30) acessos a ['www.Joey-Bhatia.com.br','www.Clinton-Giampaolo.com.br','www.Dale-Burg.com.br']"
domains = ['www.Joey-Bhatia.com.br','www.Clinton-Giampaolo.com.br','www.Dale-Burg.com.br']
for domain in domains:
	diff = client.encrypt({'$inc':{'accesses':randint(1,30)}},kind='update')
	output = s.update(client.get_ibe_sk([domain]),diff)
	print output

print "Resultado: "
for domain in domains:
	for x in s.find(client.get_ibe_sk([domain])):
		print dumps( client.decrypt( x ),indent = 4 )