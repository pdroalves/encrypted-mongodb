#include <Python.h>
#include <relic.h>
#include <assert.h>
#include "numpy/arrayobject.h"

/**
 * @obj input data
 * @param number of words
 * @return array of words
 */
void Py_Convert_DigT_Obj_Array(dig_t *array, PyObject *obj){
  // Set operands
  PyObject *iter = PyObject_GetIter(obj);
  if (!iter) {
    // error not iterator
    printf("Error! No iterator!\n");
  }
  int nwords = PyObject_Size(obj);

  // Recover data
  for(int i = 0; i < nwords; i++) {
    PyObject *next = PyIter_Next(iter);
    if (!next) {
      // nothing left in the iterator
      printf("Iterator empty.\n");
      break;
    }

    if (!PyLong_Check(next)) {
      // error, we were expecting a long point value
      printf("Error! Wrong input!");
    }

    array[i] = PyLong_AsUnsignedLong(next);
  }

  return;
}

PyObject *Py_Convert_DigT_Array_to_Object(dig_t *array, int length)
  { PyObject *pylist, *item;
    int i;
    pylist = PyList_New(length);
    if (pylist != NULL) {
      for (i=0; i<length; i++) {
        item = PyLong_FromUnsignedLong(array[i]);
        PyList_SetItem(pylist, i, item);
      }
    }
    return pylist;
  }

void Py_UI_Convert_Obj_Array(uint8_t *array, PyObject *obj){
  // Set operands
  PyObject *iter = PyObject_GetIter(obj);
  if (!iter) {
    // error not iterator
    printf("Error! No iterator!\n");
  }
  int nwords = PyObject_Size(obj);

  // Recover data
  for(int i = 0; i < nwords; i++) {
    PyObject *next = PyIter_Next(iter);
    if (!next) {
      // nothing left in the iterator
      printf("Iterator empty.\n");
      break;
    }

    if (!PyInt_Check(next)) {
      // error, we were expecting a long point value
      printf("Error! Wrong input!");
    }

    array[i] = (uint8_t)PyInt_AsLong(next);
  }

  return;
}

PyObject *Py_UI_Convert_Array_Obj(uint8_t *array, int length)
  { 
    PyObject *pylist = PyTuple_New(length);
    PyObject *item;
    
    if (pylist != NULL) 
      for (int i = 0; i < length; i++) {
        item = PyLong_FromUnsignedLong(array[i]);
        PyTuple_SetItem(pylist, i, item);
      }
    
    return pylist;
  }
   


/////////////////////////////////////////
// Generate master public/private keys //
/////////////////////////////////////////
static PyObject *
masterkeygen(PyObject *self, PyObject *args){
  bn_t msk;
	g1_t mpk;

	// Set to NULL
	bn_null(msk);
	g1_null(mpk);

	// Alloc and initialize
	bn_new(msk);
	g1_new(mpk);

  cp_ibe_gen(msk,mpk);

  bn_t n;
  g1_get_ord(n);
  bn_print(n);
  
  // printf("\nMaster public key:\n");
  // g1_print(mpk);
  // printf("\nMaster private key:\n");
  // bn_print(msk);

	return Py_BuildValue( "(iO)(OOOI)",
                        (msk->sign == BN_POS? 1:-1),
                        Py_Convert_DigT_Array_to_Object(msk->dp,msk->used),
                        Py_Convert_DigT_Array_to_Object(mpk->x,msk->used),
                        Py_Convert_DigT_Array_to_Object(mpk->y,msk->used),
                        Py_Convert_DigT_Array_to_Object(mpk->z,msk->used),
                        mpk->norm);
}

//////////////////////////////////
// Generate an id's private key //
//////////////////////////////////

static PyObject *
keygen_prv(PyObject *self, PyObject *args){
  PyObject *tuple;

  // Parse the input
  if (!PyArg_ParseTuple(args, "O", &tuple))
    return NULL;
  assert(PyTuple_Size(tuple) >= 2);

  char *id = PyString_AsString(PyTuple_GetItem(tuple,0));
  PyObject *mastertuple = PyTuple_GetSlice(tuple,1,PyTuple_Size(tuple));   

  // Number of words for master private key
  int nwords = PyTuple_Size(mastertuple);

  // Builds master private key
  bn_t msk;
  bn_new(msk);
  bn_grow(msk,nwords);

  Py_Convert_DigT_Obj_Array(msk->dp, mastertuple);
  msk->used = nwords;
    // printf("\nMaster private key:\n");
    // bn_print(msk);

  // // Computes the private key for the provided id
  g2_t prv;
  g2_null(prv);
  g2_new(prv);
  cp_ibe_gen_prv(prv,id,strlen(id),msk);

  // printf("\nprivate key:\n");
  // g2_print(prv);

  return Py_BuildValue("(OOOI)",
                        Py_Convert_DigT_Array_to_Object(*prv->x, 2*FP_DIGS),
                        Py_Convert_DigT_Array_to_Object(*prv->y, 2*FP_DIGS),
                        Py_Convert_DigT_Array_to_Object(*prv->z, 2*FP_DIGS),
                        prv->norm);
}

/////////////
// Encrypt //
/////////////
/**
 * input order:
 * 
 * identity
 * mpk.x
 * mpk.y
 * mpk.z
 * mpk.norm
 * msg
 */
static PyObject *
ibe_encrypt(PyObject *self, PyObject *args){

  PyObject *tuple;
  PyArrayObject *PyPT;
  PyArrayObject *PyCT;

  // Parse the input
  if (!PyArg_ParseTuple(args, "OOO", &tuple,&PyPT,&PyCT))
    return NULL;

  // Identity
  char *id = PyString_AsString(PyTuple_GetItem(tuple,0));
  
  // Master public key
  g1_t mpk;
  g1_null(mpk);
  g1_new(mpk);
  
  Py_Convert_DigT_Obj_Array(mpk->x,PyTuple_GetItem(tuple,1));
  Py_Convert_DigT_Obj_Array(mpk->y,PyTuple_GetItem(tuple,2));
  Py_Convert_DigT_Obj_Array(mpk->z,PyTuple_GetItem(tuple,3));
  mpk->norm = PyInt_AsLong(PyTuple_GetItem(tuple,4));
  
  // Msg
  uint8_t *pt = (uint8_t *)(PyArray_DATA(PyPT));
  uint8_t *ct = (uint8_t *)(PyArray_DATA(PyCT));
  int npt = PyObject_Size(PyPT);
  int nct = PyObject_Size(PyCT);

  assert(nct > 0);
  assert(npt > 0);
  
  // Encrypt
  cp_ibe_enc((uint8_t*)ct,&nct,(uint8_t*)pt,npt,id,strlen(id),mpk);

  PyObject *out = Py_BuildValue("O",Py_UI_Convert_Array_Obj((uint8_t*)ct,nct));

  return out;
}

/**
 * input order:
 *
 * sk.x
 * sk.y
 * sk.z
 * sk.norm
 * ct
 */
static PyObject *
ibe_decrypt(PyObject *self, PyObject *args){

  PyObject *tuple;
  PyArrayObject *PyPT;
  PyArrayObject *PyCT;

  // Parse the input
  if (!PyArg_ParseTuple(args, "OOO", &tuple,&PyPT,&PyCT))
    return NULL;
  assert(PyTuple_Size(tuple) == 5);

  // Private key
  g2_t sk;
  g2_null(sk);
  g2_new(sk);

  Py_Convert_DigT_Obj_Array(*sk->x,PyTuple_GetItem(tuple,0));
  Py_Convert_DigT_Obj_Array(*sk->y,PyTuple_GetItem(tuple,1));
  Py_Convert_DigT_Obj_Array(*sk->z,PyTuple_GetItem(tuple,2));
  sk->norm = PyInt_AsLong(PyTuple_GetItem(tuple,3));

  // Ciphertext
  int npt = PyObject_Size(PyPT);
  int nct = PyObject_Size(PyCT);
  assert(nct > 0);
  assert(npt > 0);

  uint8_t *pt = (uint8_t*)(PyArray_DATA(PyPT));
  uint8_t *ct = (uint8_t*)(PyArray_DATA(PyCT));
    
  // // Decrypt
  cp_ibe_dec((uint8_t*)pt, &npt, (uint8_t*)ct, nct, sk);
  PyObject *result = Py_UI_Convert_Array_Obj((uint8_t*)pt,npt);

  PyObject* out = Py_BuildValue("O",result);
  return out;
}

//////////////////
// Python Setup //
//////////////////

static PyMethodDef BFIBEMethods[] = {
    {"masterkeygen",  masterkeygen, METH_VARARGS,
     "Generates a tuple of master private and public keys."},
    {"keygen_prv",  keygen_prv, METH_VARARGS,
     "Generates the private key for some id using a master private key."},
    {"encrypt",  ibe_encrypt, METH_VARARGS,
     "Encrypts a message."},
    {"decrypt",  ibe_decrypt, METH_VARARGS,
     "Decrypts a message."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initBFIBE(void)
{ 
  int result = core_init();
  if (result != STS_OK) {
    core_clean();
    // printf("core init fail\n");
  }

  // init and set eliptic curves 
  ep_curve_init();
  // ep_param_set_any();
 
  (void) Py_InitModule("BFIBE", BFIBEMethods);
}
