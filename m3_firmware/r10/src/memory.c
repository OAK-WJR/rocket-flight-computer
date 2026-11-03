/* The independent -nostdlib image supplies the libc primitives it uses.
 * Volatile byte stores prevent loop-to-memset recognition/recursion. */
#include <stddef.h>
void *memset(void *dest, int value, size_t size) {
    volatile unsigned char *p = (volatile unsigned char *)dest;
    while (size-- != 0u) *p++ = (unsigned char)value;
    return dest;
}

/* The caller supplies non-overlapping ranges, as required by C memcpy. */
void *memcpy(void *dest,const void *source,size_t size) {
    volatile unsigned char *d=(volatile unsigned char *)dest;
    const unsigned char *s=(const unsigned char *)source;
    while (size--!=0u) *d++=*s++;
    return dest;
}

int memcmp(const void *left,const void *right,size_t size) {
    const unsigned char *a=(const unsigned char *)left,*b=(const unsigned char *)right;
    for (size_t i=0;i<size;++i) if (a[i]!=b[i]) return (int)a[i]-(int)b[i];
    return 0;
}
