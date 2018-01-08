#include <Python.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "ore.h"
#include "crypto.h"
#include "errors.h"
#include "flags.h"

#define CEIL(x, y) (((x) + (y) - 1) / (y))
static int _error_flag;
#define ERR_CHECK(x) if((_error_flag = x) != ERROR_NONE) { printf("Erro %d\n",_error_flag);exit(1); }

/* Converts a block/__m128i object to a array of uint64_t
 */
PyObject *Py_byte_array_To_PyArray(byte* b, int length){
    PyObject *pylist = PyTuple_New(length);
    PyObject *item;

    for(int i = 0; i < length; i++){
        item = PyInt_FromLong((long)b[i]);
        PyTuple_SetItem(pylist, i, item);
    }
    
    return pylist;
}

PyObject *Py_AES_KEY_To_PyArray(AES_KEY key){
    PyObject *aeskey = PyTuple_New(16);

    for( int i = 0; i < 16; i++){
        PyObject *aesblock = PyTuple_New(2); // round key    
        PyTuple_SetItem(aesblock, 0, PyLong_FromUnsignedLongLong(key.rd_key[i][0]));
        PyTuple_SetItem(aesblock, 1, PyLong_FromUnsignedLongLong(key.rd_key[i][1]));
        PyTuple_SetItem(aeskey, i, aesblock);
    }
    
    return aeskey;
}

void Py_AESKEY_to_block_array(block* b, PyObject *obj, int length){
        // Set operands
    PyObject *iter = PyObject_GetIter(obj);
    if (!iter) {
        // error not iterator
        printf("Error! No iterator!\n");
    }
    int nwords = PyObject_Size(obj);
    assert(nwords < length);

    for( int i = 0; i < nwords; i++){
        PyObject *next = PyIter_Next(iter);
        if (!next) {
            // nothing left in the iterator
            printf("Iterator empty.\n");
            break;
        }

        b[i][0] = (uint64_t) PyLong_AsUnsignedLongLong(PyTuple_GetItem(next,0));
        b[i][1] = (uint64_t) PyLong_AsUnsignedLongLong(PyTuple_GetItem(next,1));
    }
    
    return;
}

static PyObject *py_ore_setup(PyObject *self, PyObject *args){
    ore_params params;
    uint32_t nbits, block_len;

    if (!PyArg_ParseTuple(args, "II", &nbits, &block_len))
        return NULL;
    ERR_CHECK(init_ore_params(params, nbits, block_len));

    ore_secret_key sk;
    ERR_CHECK(ore_setup(sk, params));
    return Py_BuildValue("iO",
                         sk->key->key.rounds,
                         Py_AES_KEY_To_PyArray(sk->key->key));

}

static PyObject *py_ore_encrypt(PyObject *self, PyObject *args){
    uint32_t nbits, block_len;
    ore_secret_key sk;
    ore_params params;
    ore_ciphertext ctx;
    PyObject *tuplesk;
    uint64_t msg;
    
    if (!PyArg_ParseTuple(args, "IOII", &msg, &tuplesk, &nbits, &block_len))
        return NULL;
    ERR_CHECK(init_ore_params(params, nbits, block_len));

    // Sk
    sk->initialized = true;
    memcpy(sk->params, params, sizeof(ore_params));
    
    sk->key->key.rounds = (int) PyInt_AsLong(PyTuple_GetItem(tuplesk, 0));
    Py_AESKEY_to_block_array(sk->key->key.rd_key, PyTuple_GetItem(tuplesk, 1),
                             sk->key->key.rounds);

    // Ciphertext
    ERR_CHECK(init_ore_blk_ciphertext(ctx, params));
    ERR_CHECK(ore_blk_encrypt_ui(ctx, sk, msg));

    PyObject *ctxleft = Py_byte_array_To_PyArray(ctx->comp_left, _py_ore_blk_ciphertext_len_left(ctx->params));
    PyObject *ctxright = Py_byte_array_To_PyArray(ctx->comp_right, _py_ore_blk_ciphertext_len_right(ctx->params));
    ERR_CHECK(clear_ore_blk_ciphertext(ctx));

    return Py_BuildValue("OO", ctxleft, ctxright);
}


//////////////////
// Python Setup //
//////////////////

static PyMethodDef OREMethods[] = {
        {"keygen",  py_ore_setup, METH_VARARGS,
         "Generates the master private key."},
        {"encrypt",  py_ore_encrypt, METH_VARARGS,
         "Encrypts a message."},
        {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC initLewiWuORE(void)
{ 
    // srand((unsigned) time(NULL));
    srand(42);

    (void) Py_InitModule("LewiWuORE", OREMethods);
}
