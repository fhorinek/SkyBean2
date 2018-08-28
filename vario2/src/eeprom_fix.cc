#include "eeprom_fix.h"

void eeprom_update_byte_fixed(uint8_t *__p, uint8_t __value)
{
	eeprom_busy_wait();
	uint8_t value = eeprom_read_byte(__p);
	eeprom_busy_wait();

	if (value != __value)
		eeprom_write_block(&__value, (void *)__p, sizeof(uint8_t));
}

void eeprom_update_word_fixed(uint16_t *__p, uint16_t __value)
{
	eeprom_busy_wait();
	uint16_t value = eeprom_read_word(__p);
	eeprom_busy_wait();

	if (value != __value)
		eeprom_write_block(&__value, (void *)__p, sizeof(uint16_t));
}
