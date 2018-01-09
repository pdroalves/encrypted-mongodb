# encrypted-mongodb

We suppose that an instance of MongoDB is already set and running.

## Installation
There is nothing very particular for installation of this library. I suggest (as best practice) the use of a virtual environment (like virtualenv), but you are free to install the required packages direct to the root.

Using pip you can install the dependencies (described in src/requirements.txt). After that you must compile and install secmongo and the orelewi package.

```bash
    cd src/
    pip install -r requirements.txt
    python setup.py install
    cd orelewi/pymodule/
    python setup.py install
```

## Example
Implementation found in client.py and test_client.py
