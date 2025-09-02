// ---- forward declarations (prototypes) ----
#pragma once   // must be the very first line

void rotaryEncoder();
void saveAllReceiverInformation();
void readAllReceiverInformation();
void loadSSBPatch();

void showFrequency(bool cleanDisplay = false);
void showStatus(bool cleanFreq = false);
void showBandTag();
void showModulation();
void showStep();
void showBandwidth();
void showCharge(bool forceShow = false);
void showVolume();
void updateLowerDisplayLine();
void showSMeter();

void doVolume(int8_t v);
void doStep(int8_t v);
void doBandwidth(uint8_t v);
void updateBFO();
void agcSetFunc();
void doSeek();
void applyBandConfiguration(bool extraSSBReset = false);
void bandSwitch(bool up);