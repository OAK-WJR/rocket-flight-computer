/* The independent -nostdlib image supplies only the libc primitive it uses.
 * Volatile byte stores prevent loop-to-memset recognition/recursion. */
#include <stddef.h>
void *memset(void *dest, int value, size_t size) {
    volatile unsigned char *p = (volatile unsigned char *)dest;
    while (size-- != 0u) *p++ = (unsigned char)value;
    return dest;
}
