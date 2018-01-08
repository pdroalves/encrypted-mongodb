import time
from client import Client
from secmongo import SecMongo

def client_encryption(client, doc):
    client.encrypt(doc)

def secmongo_insert(driver, enc_doc):
    driver.insert(enc_doc)

def secmongo_insert_index(driver, node):
    driver.insert_index(node)

def test_client_encryption(benchmark):
    client = Client(Client.keygen())
    client.set_attr("movieid", "index")
    client.set_attr("customerid", "index")
    client.set_attr("rating", "index")
    client.set_attr("date", "static")
    doc = {"movieid":1, "customerid":1, "rating":5, "date":"2017-01-01"}

    # benchmark something
    benchmark(client_encryption, client = client, doc = doc)

# def test_secmongo_insert(benchmark):
#     client = Client(Client.keygen())
#     client.set_attr("movieid", "index")
#     client.set_attr("customerid", "index")
#     client.set_attr("rating", "index")
#     client.set_attr("date", "static")
#     doc = {"movieid":1, "customerid":1, "rating":5, "date":"2017-01-01"}
    
#     s = SecMongo(add_cipher_param=pow(client.ciphers["h_add"].keys["pub"]["n"], 2))
#     s.open_database("benchmark")
#     s.set_collection("benchmark")
#     s.drop_collection()

#     benchmark(secmongo_insert, driver = s, enc_doc = client.encrypt(doc))