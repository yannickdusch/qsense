#include <SPI.h>
#include "dataMV2.h"

void setup() {
  
  Serial.begin(115200);
  if (AD == 1) {
    AnalogConfig();
  } else if (AD == 0) {
    DigitalConfig();
    SPI.begin();
    delay(100);
    WriteReg(initSetReg00);
    WriteReg(initSetReg01);
    WriteReg(initSetReg10);
  }
}

void loop() {
  if (AD == 1) {
    X=A_Digitize_Bx();
    Y=A_Digitize_By();
    Z=A_Digitize_Bz();
    T=A_Digitize_To();
  } else if (AD == 0) {
    WriteReg(Bx_request);   // Request X readout
    X=ReadReg(Bx_readout);   // Read out X
    WriteReg(By_request);   // Request Y readout
    Y=ReadReg(By_readout);   // Read out Y
    WriteReg(Bz_request);   // Request Z readout
    Z=ReadReg(Bz_readout);   // Read out Z
    WriteReg(To_request);   // Request T readout
    T=ReadReg(To_readout);   // Read out T
  }
  delay(100);
  RawValues();
}
