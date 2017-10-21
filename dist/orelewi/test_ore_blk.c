/**
 * Copyright (c) 2016, David J. Wu, Kevin Lewi
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
 * REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
 * FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
 * INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
 * LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
 * OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
 * PERFORMANCE OF THIS SOFTWARE.
 */

#include "crypto.h"
#include "ore_blk.h"
#include "errors.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define CEIL(x, y) (((x) + (y) - 1) / (y))

static inline int _py_ore_blk_ciphertext_len_left(ore_blk_params params) {
  uint32_t nblocks = CEIL(params->nbits, params->block_len);

  return (AES_BLOCK_LEN + CEIL(params->nbits, 8)) * nblocks;
}
static inline int _py_ore_blk_ciphertext_len_right(ore_blk_params params) {
  uint32_t block_len = params->block_len;
  uint32_t nslots = 1 << block_len;
  uint32_t nblocks = CEIL(params->nbits, block_len);

  return AES_BLOCK_LEN + CEIL(nslots, 8) * nblocks;
}

static int _error;
#define ERR_CHECK(x) if((_error = x) != ERROR_NONE) { return _error; }

static const int N_TRIALS = 1;

void print128_num(__m128i var) 
{
    int64_t *v64val = (int64_t*) &var;
    printf("%llu %llu\n", v64val[0], v64val[1]);
}

/**
 * Generates two random 32-bit integers and encrypts them (with an 8-bit block size).
 *
 * The encrypted integers are chosen randomly.
 *
 * @return 0 on success, -1 on failure, and an error if it occurred during the
 * encryption or comparison phase
 */
static int check_ore_blk() {
  int nbits = 32;
  int block_len = 4;

  uint64_t n1 = rand() % (((uint64_t) 1) << nbits);
  uint64_t n2 = rand() % (((uint64_t) 1) << nbits);


  n1 = 3298645429;
  n2 = 3292279815;
  printf("n1: %llu\tn2:%llu\n",n1,n2);
  int cmp = (n1 < n2) ? -1 : 1;
  if (n1 == n2) {
    cmp = 0;
  }

  ore_blk_params params;
  ERR_CHECK(init_ore_blk_params(params, nbits, block_len));

  ore_blk_secret_key sk;
  ERR_CHECK(ore_blk_setup(sk, params));

  //printf("prf_key:\n");
  //for(int i = 0; i < 16;i++)
  //  print128_num(sk->prf_key.rd_key[i]);
  //printf("\nprp_key:\n");
  //for(int i = 0; i < 16;i++)
  //  print128_num(sk->prp_key.rd_key[i]);

  ore_blk_ciphertext ctxt1;
  ERR_CHECK(init_ore_blk_ciphertext(ctxt1, params));


  ore_blk_ciphertext ctxt2;
  ERR_CHECK(init_ore_blk_ciphertext(ctxt2, params));



  ERR_CHECK(ore_blk_encrypt_ui(ctxt1, sk, n1));
  ERR_CHECK(ore_blk_encrypt_ui(ctxt2, sk, n2));

  printf("ctx1 left size:%d\n",_py_ore_blk_ciphertext_len_left(ctxt1->params));
  printf("ctx1 right size:%d\n",_py_ore_blk_ciphertext_len_right(ctxt1->params));
  //printf("ctx1 left:\n");
  //for(int i = 0; i < _py_ore_blk_ciphertext_len_left(ctxt1->params);i++)
  //  printf("%d, ",ctxt1->comp_left[i]);
  //printf("ctx1 right:\n");
  //for(int i = 0; i < _py_ore_blk_ciphertext_len_right(ctxt1->params);i++)
  //  printf("%d, ",ctxt1->comp_right[i]);
  //printf("ctx2 left:\n");
  //for(int i = 0; i < _py_ore_blk_ciphertext_len_left(ctxt2->params);i++)
  //  printf("%d, ",ctxt2->comp_left[i]);
  //printf("ctx2 right:\n");
  //for(int i = 0; i < _py_ore_blk_ciphertext_len_right(ctxt2->params);i++)
  //  printf("%d, ",ctxt2->comp_right[i]);

  int ret = 0;
  int res;
  ERR_CHECK(ore_blk_compare(&res, ctxt1, ctxt2));
  if (res != cmp) {
    ret = -1;
  }

  ERR_CHECK(clear_ore_blk_ciphertext(ctxt1));
  ERR_CHECK(clear_ore_blk_ciphertext(ctxt2));

  return ret;
}

int main(int argc, char** argv) {
  // srand((unsigned) time(NULL));
  srand(42);

  printf("Testing ORE... ");
  fflush(stdout);

  for (int i = 0; i < N_TRIALS; i++) {
    if (check_ore_blk() != ERROR_NONE) {
      printf("FAIL\n");
      return -1;
    }
  }

  printf("PASS\n");
  return 0;
}
