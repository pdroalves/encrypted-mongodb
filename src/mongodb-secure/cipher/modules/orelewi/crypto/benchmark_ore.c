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

#include "ore.h"
#include "errors.h"

#include <stdint.h>
#include <stdio.h>

#define ERR_CHECK(x) if((err = x) != ERROR_NONE) { return err; }

#define BILLION  1000000000L
#define MILLION  1000000L
#define N 100000

double compute_time_ms(struct timespec start,struct timespec stop){
  return (( stop.tv_sec - start.tv_sec )*BILLION + ( stop.tv_nsec - start.tv_nsec ))/MILLION;
}

double runEncrypt(int nbits){
  int block_len = ((rand() % (nbits - 2)) + 2);
  struct timespec start, stop;

  // Messages
  uint64_t n1 = rand() % (1 << nbits);

  int err;

  // Setup
  ore_params params;
  ERR_CHECK(init_ore_params(params, nbits, block_len));

  ore_secret_key sk;
  ERR_CHECK(ore_setup(sk, params));

  // Init ciphertext
  ore_ciphertext ctxt1;
  ERR_CHECK(init_ore_ciphertext(ctxt1, params));

  // Benchmark
  clock_gettime( CLOCK_REALTIME, &start);
  for(int i = 0; i < N;i++){
    ERR_CHECK(ore_encrypt_ui(ctxt1, sk, n1));
  }
  clock_gettime( CLOCK_REALTIME, &stop);

  ERR_CHECK(clear_ore_ciphertext(ctxt1));
  ERR_CHECK(ore_cleanup(sk));

  return compute_time_ms(start,stop)/N;
 }

double runCompare(int nbits){
  int block_len = ((rand() % (nbits - 2)) + 2);
  struct timespec start, stop;

  // Messages
  uint64_t n1 = rand() % (1 << nbits);
  uint64_t n2 = rand() % (1 << nbits);

  int err;

  // Setup
  ore_params params;
  ERR_CHECK(init_ore_params(params, nbits, block_len));

  ore_secret_key sk;
  ERR_CHECK(ore_setup(sk, params));

  // Init ciphertext
  ore_ciphertext ctxt1;
  ERR_CHECK(init_ore_ciphertext(ctxt1, params));
  ore_ciphertext ctxt2;
  ERR_CHECK(init_ore_ciphertext(ctxt2, params));
  
  ERR_CHECK(ore_encrypt_ui(ctxt1, sk, n1));
  ERR_CHECK(ore_encrypt_ui(ctxt2, sk, n2));

  int res1;
  // Benchmark
  clock_gettime( CLOCK_REALTIME, &start);
  for(int i = 0; i < N;i++){
    ERR_CHECK(ore_compare(&res1, ctxt1, ctxt2));
  }
  clock_gettime( CLOCK_REALTIME, &stop);

  ERR_CHECK(clear_ore_ciphertext(ctxt1));
  ERR_CHECK(clear_ore_ciphertext(ctxt2));
  ERR_CHECK(ore_cleanup(sk));

  return compute_time_ms(start,stop)/N;
 }


/**
 * Generates two random 64-bit integers and encrypts them, checking to make sure
 * that the ciphertexts are compared correctly.
 *
 * The ciphertexts are represented with parameters for which the number of bits
 * is 31 and the block length is a random integer between 2 and 31.
 *
 * The encrypted integers are also chosen randomly.
 *
 * @return 0 on success, -1 on failure, and an error if it occurred during the
 * encryption or comparison phase
 */
static int bench_ore() {
  int nbits = 31;

  double diff;

  diff = runEncrypt(nbits);
  printf("Encrypt: %.091lf\n", diff);
  diff = runCompare(nbits);
  printf("Compare: %.091lf\n", diff);

  return 1;
}

int main(int argc, char** argv) {
  srand((unsigned) time(NULL));

  printf("Benchmarking ORE... ");

  bench_ore();  

  return 0;
}
