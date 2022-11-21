#include "triggerMV2.h"

void setup() {
  Serial.begin(115200);
  Set_DMode(); // DEFAULT : DIGITAL MODE
  SPI.begin();
  delay(100);
  WriteReg(initSetReg00);
  WriteReg(initSetReg01);
  WriteReg(initSetReg10);
  sCmd.addCommand("a",    Set_AMode);
  sCmd.addCommand("d",    Set_DMode);
  sCmd.addCommand("x",    Get_xfield);
  sCmd.addCommand("y",    Get_yfield);
  sCmd.addCommand("z",    Get_zfield);
  sCmd.addCommand("f",    Get_xyzfield);
}

void loop() {
  sCmd.readSerial();
}
