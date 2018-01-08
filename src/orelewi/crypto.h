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

#ifndef __CRYPTO_H__
#define __CRYPTO_H__

#include "aes.h"
#include "errors.h"
#include "flags.h"

#include <openssl/evp.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char byte;

// Structure representing a PRF key and output size of PRF.
#ifdef USE_AES

typedef struct {
  AES_KEY key;
} prf_key[1];

static const int PRF_INPUT_BYTES  = 16;
static const int PRF_OUTPUT_BYTES = 16;

#else

typedef struct {
  byte keybuf[32];
} prf_key[1];

static const int PRF_OUTPUT_BYTES = 32;

#endif

/**
 * Reads from /dev/urandom to sample a PRF key.
 *
 * @param key The PRF key to construct
 *
 * @return ERROR_NONE on success and ERROR_RANDOMNESS if reading
 * from /dev/urandom failed.
 */
int generate_prf_key(prf_key key);

/**
 * Evaluates the PRF given a key and input (as byte arrays), storing
 * the result in a destination byte array.
 *
 * @param dst    The destination byte array that will contain the output of the PRF
 * @param dstlen The size of the destination byte array
 * @param key    The PRF key
 * @param src    The byte array containing the input to the PRF
 * @param srclen The size of the input byte array
 *
 * @return ERROR_NONE on success, ERROR_DSTLEN_INVALID if the destination size
 *         is invalid
 */
int prf_eval(byte* dst, uint32_t dstlen, prf_key key, byte* src, uint32_t srclen);


/*****************************************************************************
 * Most of the functions below are only used for the more complex ORE scheme *
 * described in this paper: "Order-Revealing Encryption: New Constructions,  *
 * Applications, and Lower Bounds" (http://eprint.iacr.org/2016/612.pdf)     *
 *****************************************************************************/

static const int AES_KEY_BYTES       = 16;
static const int AES_BLOCK_LEN       = 16;
static const int AES_OUTPUT_BYTES    = 16;
static const int SHA256_OUTPUT_BYTES = 32;

/**
 * Reads from /dev/urandom to sample an AES key.
 *
 * @param key  The sampled AES key
 *
 * @return ERROR_NONE on success and ERROR_RANDOMNESS if reading from
 * /dev/urandom failed.
 */
int generate_aes_key(AES_KEY* key);

/**
 * Initializes the AES key (e.g., derive the round keys).
 *
 * @param key     The initialized AES key (output)
 * @param buf     The AES key to initialize
 * @param buflen  Length of the key buffer
 *
 * @return ERROR_NONE on success and ERROR_PRF_KEYLEN_INVALID if buffer has
 *         the wrong length
 */
int setup_aes_key(AES_KEY* key, byte* buf, uint32_t buflen);

/**
 * Evaluates AES(k, x) on a single block x.
 *
 * @param dst    The input block x that will be overwritten with AES(k, x)
 * @param key    The AES key k
 *
 * @return ERROR_NONE on success
 */
static inline int aes_eval_in_place(block* dst, const AES_KEY* key) {
  AES_ecb_encrypt_blk(dst, key);

  return ERROR_NONE;
}

/**
 * Evaluates AES(k, x) on a single block x.
 *
 * @param dst    The destination block that will contain the output of AES
 * @param key    The AES key k
 * @param src    The value x on which to evaluate AES
 *
 * @return ERROR_NONE on success
 */
static inline int aes_eval(block* dst, const AES_KEY* key, const block src) {
  *dst = src;
  return aes_eval_in_place(dst, key);
}

/**
 * Evaluates AES on multiple blocks (with the same underlying key)
 *
 * @param dst      A vector of blocks (of length nblocks) that will contain the
 *                 outputs of AES
 * @param nblocks  The number of input/output blocks
 * @param key      The AES key k
 * @param src      A vector of blocks (of length nblocks) on which to evaluate AES
 *
 * @return ERROR_NONE on success
 */
static inline int aes_eval_blocks(block* dst, uint32_t nblocks, const AES_KEY* key, const block* src) {
  memcpy(dst, src, nblocks * sizeof(block));
  AES_ecb_encrypt_blks(dst, nblocks, key);

  return ERROR_NONE;
}

/**
 * Evaluates a PRP (on an nbits domain) on a single value. The PRP is AES-based.
 *
 * @param dst    A buffer (at least nbits long) that will hold
 *               the output of the PRP
 * @param key    The key for the PRP
 * @param src    The input value to the PRP (nbits)
 * @param nbits  The number of bits in the domain of the PRP
 *
 * @return ERROR_NONE on success and a corresponding error code on failure
 *         (see errors.h for the full list of possible error codes)
*/
int prp_eval(byte* dst, const AES_KEY* key, const byte* src, uint32_t nbits);

/**
 * Evaluates a PRP (on an nbits domain) on all of the values in the domain.
 * The PRP is AES-based.
 *
 * @param dst    A buffer (at least nbits * 2^nbits long) that will hold
 *               all of the outputs of the PRP (values from 0, 1, ... ,
 *               2^nbits - 1)
 * @param key    The key for the PRP
 * @param nbits  The number of bits in the domain of the PRP
 *
 * @return ERROR_NONE on success and a corresponding error code on failure
 *         (see errors.h for the full list of possible error codes)
*/
int prp_eval_all(uint64_t* dst, const AES_KEY* key, uint32_t nbits);

/**
 * Evaluates a PRP inverse (on an nbits domain) on a single value.
 * The PRP is AES-based.
 *
 * @param dst    A buffer (at least nbits long) that will hold
 *               the output of the PRP inverse
 * @param key    The key for the PRP
 * @param src    The input value to the PRP (nbits long)
 * @param nbits  The number of bits in the domain of the PRP
 *
 * @return ERROR_NONE on success and a corresponding error code on failure
 *         (see errors.h for the full list of possible error codes)
*/
int prp_inv_eval(byte* dst, const AES_KEY* key, const byte* src, uint32_t nbits);

/**
 * Evaluates a PRP inverse (on an nbits domain) on all of the values
 * in the domain. The PRP is AES-based.
 *
 * @param dst    A buffer (at least nbits * 2^nbits long) that will hold all
 *               of the outputs of the PRP inverse (values from 0, 1, ... ,
 *               2^nbits - 1)
 * @param key    The key for the PRP
 * @param nbits  The number of bits in the domain of the PRP
 *
 * @return ERROR_NONE on success and a corresponding error code on failure
 *         (see errors.h for the full list of possible error codes)
*/
int prp_inv_eval_all(uint64_t* dst, const AES_KEY* key, uint32_t nbits);

/**
 * Evaluates SHA-256 on an input value.
 *
 * @param dst     A buffer that will hold the outputs of SHA-256
 * @param dstlen  The size of the output buffer
 * @param src     The input to SHA-256
 * @param nbits   The size of the input buffer
 *
 * @return ERROR_NONE on success and a corresponding error code on failure
 *         (see errors.h for the full list of possible error codes)
*/
int sha_256(byte* dst, uint32_t dstlen, byte* src, uint32_t srclen);

#endif /* __CRYPTO_H__ */
