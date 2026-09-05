/*
 * Minimal freestanding <stdint.h> for the CFG-sufficiency spike.
 *
 * WHY THIS EXISTS (documented deviation, see RESULTS.md): the `libclang`
 * PyPI wheel ships only libclang.dll — it does NOT bundle clang's resource
 * directory (lib/clang/<ver>/include/), which is where a normal clang
 * install keeps its compiler-provided freestanding headers (stdint.h,
 * stddef.h, stdbool.h, stdarg.h, float.h, limits.h). The C11 standard
 * (6.10.8.3 / freestanding scope) makes these the *compiler's*
 * responsibility, not the target's — CMSIS's core_cm4.h and every HAL
 * header `#include <stdint.h>` and get nothing without this shim.
 *
 * This defines exactly the fixed-width types via clang's own builtin type
 * macros (__INT32_TYPE__ etc.) — the same technique clang's real stdint.h
 * uses internally. It is not a stand-in for the target's real libc; it
 * only needs to make parsing succeed, not produce a linkable binary.
 */
#ifndef _SPIKE_STDINT_H
#define _SPIKE_STDINT_H

typedef __INT8_TYPE__   int8_t;
typedef __INT16_TYPE__  int16_t;
typedef __INT32_TYPE__  int32_t;
typedef __INT64_TYPE__  int64_t;
typedef __UINT8_TYPE__  uint8_t;
typedef __UINT16_TYPE__ uint16_t;
typedef __UINT32_TYPE__ uint32_t;
typedef __UINT64_TYPE__ uint64_t;

typedef __INTPTR_TYPE__  intptr_t;
typedef __UINTPTR_TYPE__ uintptr_t;
typedef __INTMAX_TYPE__  intmax_t;
typedef __UINTMAX_TYPE__ uintmax_t;

typedef int8_t   int_least8_t;
typedef int16_t  int_least16_t;
typedef int32_t  int_least32_t;
typedef int64_t  int_least64_t;
typedef uint8_t  uint_least8_t;
typedef uint16_t uint_least16_t;
typedef uint32_t uint_least32_t;
typedef uint64_t uint_least64_t;

typedef int32_t  int_fast8_t;
typedef int32_t  int_fast16_t;
typedef int32_t  int_fast32_t;
typedef int64_t  int_fast64_t;
typedef uint32_t uint_fast8_t;
typedef uint32_t uint_fast16_t;
typedef uint32_t uint_fast32_t;
typedef uint64_t uint_fast64_t;

#define INT8_MIN   (-128)
#define INT16_MIN  (-32768)
#define INT32_MIN  (-2147483647-1)
#define INT64_MIN  (-9223372036854775807LL-1)
#define INT8_MAX   127
#define INT16_MAX  32767
#define INT32_MAX  2147483647
#define INT64_MAX  9223372036854775807LL
#define UINT8_MAX  0xff
#define UINT16_MAX 0xffff
#define UINT32_MAX 0xffffffffU
#define UINT64_MAX 0xffffffffffffffffULL

#define INTPTR_MIN  INT32_MIN
#define INTPTR_MAX  INT32_MAX
#define UINTPTR_MAX UINT32_MAX

#define SIZE_MAX UINT32_MAX

#define INT8_C(x)   x
#define INT16_C(x)  x
#define INT32_C(x)  x
#define INT64_C(x)  x ## LL
#define UINT8_C(x)  x ## U
#define UINT16_C(x) x ## U
#define UINT32_C(x) x ## U
#define UINT64_C(x) x ## ULL

#endif /* _SPIKE_STDINT_H */
