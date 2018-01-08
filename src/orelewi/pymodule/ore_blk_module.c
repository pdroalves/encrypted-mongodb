#include <Python.h>
#include <crypto.h>
#include <ore_blk.h>
#include <errors.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define CEIL(x, y) (((x) + (y) - 1) / (y))
static int _error_flag;
#define ERR_CHECK(x) if((_error_flag = x) != ERROR_NONE) { printf("Erro %d\n",_error_flag);exit(1); }

/**
 * Computes the length of a left ciphertext.
 *
 * @param params The parameters for the ORE scheme
 *
 * @return the length of a left ciphertext for the specific choice of
 *         parameters
 */
static inline int _py_ore_blk_ciphertext_len_left(ore_blk_params params) {
    uint32_t nblocks = CEIL(params->nbits, params->block_len);

    return (AES_BLOCK_LEN + CEIL(params->nbits, 8)) * nblocks;
}

/**
 * Computes the length of a right ciphertext.
 *
 * @param params The parameters for the ORE scheme
 *
 * @return the length of a right ciphertext for the specific choice of
 *         parameters
 */
static inline int _py_ore_blk_ciphertext_len_right(ore_blk_params params) {
    uint32_t block_len = params->block_len;
    uint32_t nslots = 1 << block_len;
    uint32_t nblocks = CEIL(params->nbits, block_len);

    return AES_BLOCK_LEN + CEIL(nslots, 8) * nblocks;
}


// void print128_num(__m128i var)
// {
//     uint64_t *v64val = (uint64_t*) &var;
//     printf("Numerical: %llu %llu\n", v64val[1], v64val[0]);
// }

/* Converts a block/__m128i object to a array of uint64_t
 */
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


static PyObject *
py_ore_blk_setup(PyObject *self, PyObject *args){
    ore_blk_params params;
    uint32_t nbits, block_len;

    if (!PyArg_ParseTuple(args, "II", &nbits, &block_len))
        return NULL;
    ERR_CHECK(init_ore_blk_params(params, nbits, block_len));

    ore_blk_secret_key sk;
    ore_blk_setup(sk, params);

    return Py_BuildValue("iOiO",
                         sk->prf_key.rounds,
                         Py_AES_KEY_To_PyArray(sk->prf_key),
                         sk->prp_key.rounds,
                         Py_AES_KEY_To_PyArray(sk->prp_key));

}

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

static PyObject *
py_ore_blk_encrypt(PyObject *self, PyObject *args){
    ore_blk_secret_key sk;
    ore_blk_params params;
    ore_blk_ciphertext ctx;
    PyObject *tuplesk;
    uint64_t msg;
    
    params->initialized = true;

    if (!PyArg_ParseTuple(args, "IOII", &msg, &tuplesk, &params->nbits,&params->block_len))
        return NULL;

    // Sk
    sk->initialized = true;
    sk->prf_key.rounds = (int)PyInt_AsLong(PyTuple_GetItem(tuplesk,0));
    Py_AESKEY_to_block_array(sk->prf_key.rd_key,PyTuple_GetItem(tuplesk,1),sk->prf_key.rounds);
    sk->prp_key.rounds = (int)PyInt_AsLong(PyTuple_GetItem(tuplesk,2));
    Py_AESKEY_to_block_array(sk->prp_key.rd_key,PyTuple_GetItem(tuplesk,3),sk->prp_key.rounds);
    sk->params->initialized = true;
    sk->params->nbits = params->nbits;
    sk->params->block_len = params->block_len;

    // Ciphertext
    ERR_CHECK(init_ore_blk_ciphertext(ctx, params));

    ERR_CHECK(ore_blk_encrypt_ui(ctx, sk, msg));

    PyObject *ctxleft = Py_byte_array_To_PyArray(ctx->comp_left,_py_ore_blk_ciphertext_len_left(ctx->params));
    PyObject *ctxright = Py_byte_array_To_PyArray(ctx->comp_right,_py_ore_blk_ciphertext_len_right(ctx->params));
    ERR_CHECK(clear_ore_blk_ciphertext(ctx));

    return Py_BuildValue("OO", ctxleft, ctxright);
}

/* Converts a block/__m128i object to a array of uint64_t
 */
void Py_To_PyArray_bytearray(byte *b, PyObject* obj){

    // Set operands
    PyObject *iter = PyObject_GetIter(obj);
    if (!iter) 
        // error not iterator
        printf("Error! No iterator!\n");
    
    int nwords = PyObject_Size(obj);

    // printf("will print...\n");
    // Recover data
    for(int i = 0; i < nwords; i++) {
        PyObject *next = PyIter_Next(iter);
        if (!next) {
            // nothing left in the iterator
            printf("Iterator empty.\n");
            break;
        }

        b[i] = (byte)PyInt_AsLong(next);
    }
    return;
}

static PyObject *
py_ore_blk_compare(PyObject *self, PyObject *args){
    ore_blk_ciphertext ctx1;
    ore_blk_ciphertext ctx2;
    PyObject *ctx1left;
    PyObject *ctx1right;
    PyObject *ctx2left;
    PyObject *ctx2right;
    ore_blk_params params;

    params->initialized = true;

    if (!PyArg_ParseTuple(args, "IIOOOO", &params->nbits,
                                                                            &params->block_len,
                                                                            &ctx1left,
                                                                            &ctx1right,
                                                                            &ctx2left,
                                                                            &ctx2right))
        return NULL;
    
    ERR_CHECK(init_ore_blk_ciphertext(ctx1, params));
    ERR_CHECK(init_ore_blk_ciphertext(ctx2, params));
    
    // Ciphertext
    ctx1->initialized = true;
    Py_To_PyArray_bytearray(ctx1->comp_left, ctx1left);
    Py_To_PyArray_bytearray(ctx1->comp_right, ctx1right);
    ctx1->params->initialized = true;
    ctx1->params->nbits = params->nbits;
    ctx1->params->block_len = params->block_len;

    // Ciphertext
    ctx2->initialized = true;
    Py_To_PyArray_bytearray(ctx2->comp_left, ctx2left);
    Py_To_PyArray_bytearray(ctx2->comp_right, ctx2right);
    ctx2->params->initialized = true;
    ctx2->params->nbits = params->nbits;
    ctx2->params->block_len = params->block_len;
    
    int res;
    ERR_CHECK(ore_blk_compare(&res, ctx1, ctx2));

    ERR_CHECK(clear_ore_blk_ciphertext(ctx1));
    ERR_CHECK(clear_ore_blk_ciphertext(ctx2));

    return Py_BuildValue("i", res);

}

//////////////////
// Python Setup //
//////////////////

static PyMethodDef OREBLKMethods[] = {
        {"keygen",  py_ore_blk_setup, METH_VARARGS,
         "Generates the master private key."},
        {"encrypt",  py_ore_blk_encrypt, METH_VARARGS,
         "Encrypts a message."},
        {"compare",  py_ore_blk_compare, METH_VARARGS,
         "Compares two ciphertexts."},
        {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initLewiWuOREBlk(void)
{ 
    // srand((unsigned) time(NULL));
    srand(42);

    (void) Py_InitModule("LewiWuOREBlk", OREBLKMethods);
}
