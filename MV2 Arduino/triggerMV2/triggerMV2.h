#include <SPI.h>
#include <SerialCommand.h>   // 2012 version found on GitHub : https://github.com/kroimon/Arduino-SerialCommand
SerialCommand sCmd;

/*  ANALOG/DIGITAL MODE  */
bool AD; // DIGITAL MODE : 0 | ANALOG MODE : 1

/*  GENERAL CORRECTIONS  */
#define A_OFFSET	     	0x200    // Analog offset to avoid negative values (not handled)
#define A_SHIFT		     	6        // Shift value to 16 bits format

/*  PINS CONFIGURATION (Arduino Uno)  */
#define SPI_CLK_FREQ          1000000
#define CHIP_SELECT_PIN       10
// COMMON
#define NDIGITAL_ANALOG_PIN   8
#define VDD_PIN				      	A5 
// DIGITAL MODE
#define D_DR_PIN			      	2
#define D_INIT_PIN			    	7
#define D_SPI_MOSI			    	11
#define D_SPI_MISO			     	12
#define D_SPI_CLK             13
// ANALOG MODE
#define A_BX_PIN			      	A0
#define A_BY_PIN			      	A1
#define A_BZ_PIN		      		A2
#define A_TEMP_PIN	         	A3
#define A_REF_PIN			      	A4
#define A_EMR_PIN             2
#define A_INV_PIN		      		4
#define A_LP_PIN		      		7
#define A_MA0_PIN		      		10
#define A_MA1_PIN		      		11
#define A_RA0_PIN		      		12
#define A_RA1_PIN			      	13

/*  16 BITS COMMANDS WORDS  */
// Registers setting
uint16_t initSetReg00 = 0b1110110000110000;
uint16_t initSetReg01 = 0b1110110100000010;
uint16_t initSetReg10 = 0b1110111000001000;
// Only X (single axis mode) : MA = 01
uint16_t sBx_request = 0b1110110001110000;
uint16_t sBx_readout = 0b1101110001110000;
// Only Y (single axis mode) : MA = 10
uint16_t sBy_request = 0b1110110010110001;
uint16_t sBy_readout = 0b1101110010110001;
// Only Z (single axis mode) : MA = 11
uint16_t sBz_request = 0b1110110011110010;
uint16_t sBz_readout = 0b1101110011110010;
// Three axis mode : MA = 00
uint16_t Bx_request = 0b1110110000110000;
uint16_t Bx_readout = 0b1101110000110000;
uint16_t By_request = 0b1110110000110001;
uint16_t By_readout = 0b1101110000110001;
uint16_t Bz_request = 0b1110110000110010;
uint16_t Bz_readout = 0b1101110000110010;

/*  VARIABLES  */
// Raw values from pins
uint16_t X;
uint16_t Y;
uint16_t Z;

//////////////////////////////////// FUNCTIONS ///////////////////////////////////

void CommonConfig() {
  pinMode(VDD_PIN, INPUT);
  pinMode(A_BX_PIN, INPUT);
  pinMode(A_BY_PIN, INPUT);
  pinMode(A_BZ_PIN, INPUT);
  pinMode(A_TEMP_PIN, INPUT);
  pinMode(A_REF_PIN, INPUT);
  pinMode(A_INV_PIN, OUTPUT);
  digitalWrite(A_INV_PIN, LOW);  // Initialize INV output to LOW
}

void Set_AMode() {
  CommonConfig();  // Set common PINs
  pinMode(NDIGITAL_ANALOG_PIN, OUTPUT);  // Set PINs used in analog mode
  pinMode(A_MA0_PIN, OUTPUT);
  pinMode(A_MA1_PIN, OUTPUT);
  pinMode(A_RA0_PIN, OUTPUT);
  pinMode(A_RA1_PIN, OUTPUT);
  pinMode(A_LP_PIN, OUTPUT);
  pinMode(A_EMR_PIN, OUTPUT);
  digitalWrite(NDIGITAL_ANALOG_PIN, HIGH);  // Analog/digital selector must be HIGH
  digitalWrite(A_MA0_PIN, LOW);  // Initialize all other controls to LOW (logic 0)
  digitalWrite(A_MA1_PIN, LOW);
  digitalWrite(A_RA0_PIN, LOW);
  digitalWrite(A_RA1_PIN, LOW);
  digitalWrite(A_LP_PIN, LOW);
  digitalWrite(A_EMR_PIN, LOW);
  AD = 1;
  Serial.println("Set Mode : Analog");
}

void Set_DMode() {
  CommonConfig();  // Set common PINs
  pinMode(NDIGITAL_ANALOG_PIN, OUTPUT);  // Set PINs used in digital mode
  pinMode(D_DR_PIN, INPUT);
  pinMode(D_INIT_PIN, OUTPUT);
  pinMode(CHIP_SELECT_PIN, OUTPUT);
  digitalWrite(NDIGITAL_ANALOG_PIN, LOW);  // Analog/digital selector must be LOW 
  digitalWrite(CHIP_SELECT_PIN, HIGH);  // MagVector Chip Select (CS) must be deactived 
  digitalWrite(D_INIT_PIN, LOW);  // Initialize INIT to LOW
  AD = 0;
  Serial.println("Set Mode : Digital");
}

void WriteReg(int toWrite) {
  SPI.beginTransaction(SPISettings(SPI_CLK_FREQ, MSBFIRST, SPI_MODE0));
  digitalWrite(CHIP_SELECT_PIN,LOW);
  SPI.transfer16(toWrite);
  digitalWrite(CHIP_SELECT_PIN,HIGH);
  SPI.endTransaction();
}

int ReadReg(int toWrite) {
  int dataOut;
  SPI.beginTransaction(SPISettings(SPI_CLK_FREQ, MSBFIRST, SPI_MODE0));
  digitalWrite(CHIP_SELECT_PIN,LOW);
  dataOut=SPI.transfer16(toWrite);
  digitalWrite(CHIP_SELECT_PIN,HIGH);
  SPI.endTransaction();
  return dataOut;
}

uint16_t A_Digitize_Bx() {
	return ((analogRead(A_BX_PIN) - analogRead(A_REF_PIN)) + A_OFFSET) << A_SHIFT;
}

uint16_t A_Digitize_By() {
	return ((analogRead(A_BY_PIN) - analogRead(A_REF_PIN)) + A_OFFSET) << A_SHIFT;
}

uint16_t A_Digitize_Bz() {
	return ((analogRead(A_BZ_PIN) - analogRead(A_REF_PIN)) + A_OFFSET) << A_SHIFT;
}

void Get_xfield() {
  if (AD == 1) {
    X = A_Digitize_Bx();
  } else if (AD == 0) {
    WriteReg(sBx_request);   // Request single X readout
    delay(10);
    X=ReadReg(sBx_readout);   // Read out X
  }
  Serial.print(X);
  Serial.println("");
}

void Get_yfield() {
  if (AD == 1) {
    Y = A_Digitize_By();
  } else if (AD == 0) {
    WriteReg(sBy_request);   // Request single Y readout
    delay(10);
    Y=ReadReg(sBy_readout);   // Read out Y
  }
  Serial.print(Y);
  Serial.println("");
}

void Get_zfield() {
  if (AD == 1) {
    Z = A_Digitize_Bz();
  } else if (AD == 0) {
    WriteReg(sBz_request);   // Request single Z readout
    delay(10);
    Z=ReadReg(sBz_readout);   // Read out Z
  }
  Serial.print(Z);
  Serial.println("");
}

void Get_xyzfield() {
  if (AD == 1) {
    X = A_Digitize_Bx();
    Y = A_Digitize_By();
    Z = A_Digitize_Bz();
  } else if (AD == 0) {
    WriteReg(Bx_request);   // Request X readout
    delay(10);
    X=ReadReg(Bx_readout);   // Read out X
    WriteReg(By_request);   // Request Y readout
    Y=ReadReg(By_readout);   // Read out Y
    WriteReg(Bz_request);   // Request Z readout
    Z=ReadReg(Bz_readout);   // Read out Z
  }
  Serial.print(X);
  Serial.print(",");
  Serial.print(Y);
  Serial.print(",");
  Serial.print(Z);
  Serial.println("");
}
