#ifndef EEPFOM_FIX
#define EEPFOM_FIX

#include "common.h"

void eeprom_update_byte_fixed(uint8_t *__p, uint8_t __value);
void eeprom_update_word_fixed(uint16_t *__p, uint16_t __value);

#endif
