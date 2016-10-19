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

#ifndef __FLAGS_H__
#define __FLAGS_H__

// Set this flag to use AES as the underlying PRF (rather than HMAC) for the
// basic ORE construction (ore). Currently, we only support encrypting 64-bit
// values when AES is the underlying PRF. The HMAC implementation supports
// encrypting messages from an arbitrary plaintext space.

#define USE_AES

// Set this flag to use AES to instantiate the random oracle in the block ORE
// (ore_blk) construction. This construction can be proven secure if we, for
// instance, model AES as an ideal cipher (see Section 7 of the paper for a
// full discussion: http://eprint.iacr.org/2016/612.pdf). If this flag is
// turned off, then the random oracle is instantiated using SHA-256.

#define USE_AES_RO

#endif /* __FLAGS_H__ */
