#ifndef COMMON_H_
#define COMMON_H_

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <avr/eeprom.h>
#include <avr/wdt.h>
#include <util/delay.h>
#include <util/atomic.h>

#ifdef __cplusplus
	#include "oofix.h"
#endif

#define LOW		0
#define HIGH	1
#define MEDIUM	2
#define NONE	3

#define LO		LOW
#define HI		HIGH
#define ME		MEDIUM

#define OUTPUT	HIGH
#define INPUT	LOW

#define ON		HIGH
#define OFF		LOW

#define MSB		HIGH
#define LSB		LOW

#define READ	HIGH
#define WRITE	LOW

#define BUFFER_SIZE	64

#ifdef abs
#undef abs
#endif

#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#define abs(x) ((x)>0?(x):-(x))

#ifdef __cplusplus
extern "C" {
#endif

void EnableInterrupts();
void DisableInterrupts();
void CCPIOWrite(volatile uint8_t * address, uint8_t value);
uint8_t CalcCRC(uint8_t old_crc, uint8_t key, uint8_t data);

#ifdef __cplusplus
}
#endif


#endif /* COMMON_H_ */
