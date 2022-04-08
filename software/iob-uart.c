#include <stdint.h>
#include "iob-uart.h"

//TX FUNCTIONS
void uart_txwait() {
    while(!UART_GET_TXREADY());
}

void uart_putc(char c) {
    while(!UART_GET_TXREADY());
    UART_SET_TXDATA(c);
}

//RX FUNCTIONS
void uart_rxwait() {
    while(!UART_GET_RXREADY());
}

char uart_getc() {
    while(!UART_GET_RXREADY());
    return UART_GET_RXDATA();
}

//UART basic functions
void uart_init(int base_address, uint16_t div) {
  //capture base address for good
  UART_INIT_BASEADDR(base_address);
  
  //pulse soft reset
  UART_SET_SOFTRESET(1);
  UART_SET_SOFTRESET(0);

  //Set the division factor div
  //div should be equal to round (fclk/baudrate)
  //E.g for fclk = 100 Mhz for a baudrate of 115200 we should UART_SET_DIV(868)
  UART_SET_DIV(div);

  //enable TX and RX
  UART_SET_TXEN(1);
  UART_SET_RXEN(1);
}

void uart_finish() {
  uart_putc(EOT);
  uart_txwait();
}

//Print string, excluding end of string (0)
void uart_puts(const char *s) {
  while (*s) uart_putc(*s++);
}

//Sends the name of the file to use, including end of string (0)
void uart_sendstr (char* name) {
  int i=0;
  do
    uart_putc(name[i]);
  while (name[i++]);
}

//Receives file into mem
int uart_recvfile(char* file_name, char **mem) {

  uart_puts(UART_PROGNAME);
  uart_puts (": requesting to receive file\n");

  //send file receive request
  uart_putc (FRX);

  //send file name
  uart_sendstr(file_name);


  //receive file size
  int file_size = (unsigned int) uart_getc();
  file_size |= ((unsigned int) uart_getc()) << 8;
  file_size |= ((unsigned int) uart_getc()) << 16;
  file_size |= ((unsigned int) uart_getc()) << 24;

  //allocate space for file if file pointer not initialized
  if((*mem) == NULL) {
    (*mem) = (char *) malloc(file_size);
    if ((*mem) == NULL) {
      uart_puts(UART_PROGNAME);
      uart_puts("Error: malloc failed");
    }
  }

  //send ACK before receiving file
  uart_putc(ACK);

  //write file to memory
  for (int i = 0; i < file_size; i++) {
    (*mem)[i] = uart_getc();
  }

  uart_puts(UART_PROGNAME);
  uart_puts(": file received\n");

  return file_size;
}

//Sends mem contents to a file
void uart_sendfile(char *file_name, int file_size, char *mem) {

  uart_puts(UART_PROGNAME);
  uart_puts(": requesting to send file\n");

  //send file transmit command
  uart_putc(FTX);
	
  //send file name
  uart_sendstr(file_name);
	
  // send file size
  uart_putc((char)(file_size & 0x0ff));
  uart_putc((char)((file_size & 0x0ff00) >> 8));
  uart_putc((char)((file_size & 0x0ff0000) >> 16));
  uart_putc((char)((file_size & 0x0ff000000) >> 24));
  
  // send file contents
  for (int i = 0; i < file_size; i++)
    uart_putc(mem[i]);

  uart_puts(UART_PROGNAME);
  uart_puts(": file sent\n");
}
