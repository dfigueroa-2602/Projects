#pragma once

// Forward declarations for functions used before their definitions

// --- CAT/Command functions ---
void Command_GETFreqA();
void Command_SETFreqA();
void Command_IF();
void Command_ID();
void Command_PS();
void Command_PS1();
void Command_AI();
void Command_AI0();
void Command_GetMD();
void Command_SetMD();
void Command_RX();
void Command_TX0();
void Command_TX1();
void Command_TX2();
void Command_AG0();
void Command_XT1();
void Command_RT1();
void Command_RC();
void Command_FL0();
void Command_RS();
void Command_VX(char mode);

// --- DSP/Radio functions ---
void switch_rxtx(uint8_t tx_enable);
void stepsize_showcursor();
void dec2();
void sdr_rx_00();
void sdr_rx_01();
void sdr_rx_02();
void sdr_rx_03();
void sdr_rx_04();
void sdr_rx_05();
void sdr_rx_06();
void sdr_rx_07();
int16_t sdr_rx_common_i();
int16_t sdr_rx_common_q();

// --- Other functions ---
int cw_tx(char ch);
int cw_tx(char* msg);
void cw_decode();
int16_t smeter(int16_t ref = 0);
void process(int16_t i_ac2, int16_t q_ac2);
