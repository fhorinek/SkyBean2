/*
 * common.h
 *
 *  Created on: 7.11.2013
 *      Author: horinek
 */

#ifndef vCOMMON_H_
#define vCOMMON_H_

#include "xlib/core/clock.h"
#include "xlib/core/rtc.h"
#include "xlib/core/timer.h"
#include "xlib/core/usart.h"
#include "xlib/core/i2c.h"
#include "xlib/core/usart.h"
#include "xlib/core/system.h"
#include "xlib/core/watchdog.h"

#include "eeprom_fix.h"

#define SENSOR_TYPE_MS

//always clean when changing sensor type or clock speed!!!
#ifdef SENSOR_TYPE_MS
	#define SENSOR	MS5611 sensor
#else
	#define SENSOR	BMP180 sensor
#endif

//#define FLUID_LIFT
#define FLUID_LIFT_REFRESH	20
//1 == 20ms

//uart debug & timing pin
//#define ENABLE_DEFAULT_CFG
//#define ENABLE_DEBUG_TIMING
#define ENABLE_DEBUG_UART

extern uint8_t usb_connected;

extern Usart usb_uart;

#include "debug.h"

//pinout
//port A
#define LEDG			porta0
#define LEDR			porta1
#define BUTTON_PIN		porta2
#define BM_PIN			porta4
#define GPS_EN			porta5


#define BAT_MEAS_PIPE	pipea0
#define BAT_MEAS_ADC	ext_porta3

#define BUTTON_DOWN		(GpioRead(BUTTON_PIN) == LOW)
#define USB_CONNECTED	(GpioRead(USB_IN) == HIGH)

//port D
#define USB_IN			portd4
#define USB_UART_RX		portd6
#define USB_UART_TX		portd7

//port R
#define B_EN			portr1

//leds
#define LEDR_ON			GpioWrite(LEDR, LOW);
#define LEDR_OFF		GpioWrite(LEDR, HI);
#define LEDG_ON			GpioWrite(LEDG, LOW);
#define LEDG_OFF		GpioWrite(LEDG, HI);


//auto power off constants
//#define AUTO_TIMEOUT	(60000 * 5) //5min
#define AUTO_THOLD		1 //+-1m == max diff 2m

#define DEBUG_PIN 	GPS_EN

union byte4
{
	uint32_t uint32;
	int32_t int32;
	uint8_t uint8[4];
};

union byte2
{
	uint16_t uint16;
	int16_t int16;
	uint8_t uint8[2];
};

void LoadEEPROM();
void resetEEPROM();
void dumpEE(bool show_cfg);

void StoreVolume();
void StoreLift();
void StoreSink();
void LoadProfile();

void sys_tick_init();
uint32_t sys_tick_get();

#endif /* vCOMMON_H_ */
