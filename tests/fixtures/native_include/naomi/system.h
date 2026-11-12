#include <stdint.h>
extern unsigned char test_sram_storage[];
#define UNCACHED_MIRROR 0
#define SRAM_BASE ((uintptr_t)&test_sram_storage[1])
#define SRAM_SIZE 0x8000
