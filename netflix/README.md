This directory contains some auxiliar scripts used to load and manipulate the [Netflix database](http://academictorrents.com/details/9b13183dc4d60676b773c9e2cd6de5e5542cee9a).

1. netflix_load.py
  - Parse, encrypt, and load Netflix's dataset to a MongoDB instance. The encryption keys are exported to keys.json (or some other file set with --keys).
    - Example: 
        ``` python netflix_load.py --path ~/netflix_dataset/training_set --url localhost```
2. netflix_encrypted.py
  - Run the queries described in JISA's paper over encrypted data. This script should be executed using ipython and the input parameters ("url" and "ikeys") must be manually edited inside the file.

3. netflix_unencrypted.py
  - Run the queries described in JISA's paper over unencrypted data. This script should be executed using ipython and the input parameter ("url") must be manually edited inside the file. It is expected that this dataset to be loaded using [mongoimport] (https://stackoverflow.com/questions/4686500/how-to-use-mongoimport-to-import-csv).
