/*
 * debug.h
 *
 *  Created on: 14. 2. 2018
 *      Author: horinek
 */

#ifndef SRC_DEBUG_H_
#define SRC_DEBUG_H_

#ifdef ENABLE_DEBUG_UART
	#define DEBUG(format, ...) \
		do {\
			if (usb_connected){\
				printf_P(PSTR(format), ##__VA_ARGS__);\
			}\
		} while(0)\

				/*while(!usb_uart.isTxBufferEmpty());\*/


	#define assert(cond) \
		do{ \
		if (!(cond)) \
			{\
				PGM_P __file__ = PSTR(__FILE__); \
				DEBUG("Assertion failed %S@%d!\n", __file__, __LINE__); \
			} \
		} while(0);
#else
	#define DEBUG(format, ...)
	#define assert(cond)
#endif

#endif /* SRC_DEBUG_H_ */
