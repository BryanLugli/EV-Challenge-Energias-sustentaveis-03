// ============================================================
// GreenCharge - Prototipo do Controlador do Eletroposto (EVSE)
// Sprint 3 - Prototipagem Funcional e Integracao
// EV Challenge 2026 - FIAP - Energias Renovaveis e Sustentabilidade
//
// Equipe:
//   Bryan Lugli      - RM571350
//   Beckman Lugli    - RM573442
//   Guilherme Xavier - RM573053
//
// Plataforma: ESP32 (simulado no Wokwi)
// ============================================================

// Forward declarations dos tipos usados nas funcoes abaixo.
// Necessario porque o Arduino/ESP32 gera sozinho as assinaturas das
// funcoes e as insere no TOPO do arquivo, antes de onde "struct Decisao"
// e "struct Cenario" sao definidos mais abaixo. Sem isso, o compilador
// nao reconhece esses tipos e o build falha.
struct Decisao;
struct Cenario;

// ------------------------------------------------------------
//
// O QUE ESSE PROTOTIPO REPRESENTA:
// No diagrama de arquitetura do GreenCharge (Sprint 2), o fluxo e:
//
//   Geracao solar (API GoodWe / Clear Sky Model)
//        -> Motor de Decisao (Python, ja validado na Sprint 2)
//        -> Controlador OCPP / EVSE  <-- ESTE PROTOTIPO
//        -> Acao real no carregador (liga/desliga, LED de status)
//
// Este ESP32 simula exatamente o bloco "Controlador OCPP / EVSE":
// ele recebe (aqui, simulados) os mesmos dados que o motor de decisao
// em Python ja calcula (geracao solar em kW e veiculos conectados),
// roda A MESMA REGRA de prioridade solar, e traduz a decisao em
// comandos automatizados reais: acender o LED certo, mostrar os
// dados no Monitor Serial, exatamente como um controlador de
// eletroposto real faria ao decidir a fonte de energia da recarga.
//
// ============================================================

// ------------------------------------------------------------
// 1) PARAMETROS DO SISTEMA (identicos ao greencharge_simulacao.py
//    da Sprint 2, para manter a mesma logica de decisao)
// ------------------------------------------------------------
const float POTENCIA_CARREGADOR_KW = 7.4;   // kW por ponto de recarga (AC monofasico)
const int   NUM_PONTOS_RECARGA     = 4;     // eletropostos no local
const float TARIFA_KWH             = 0.85;  // R$/kWh (ANEEL - referencia SP)
const float FATOR_EMISSAO_CO2      = 0.0897; // kg CO2 / kWh (SIN - MCTI 2023)

// ------------------------------------------------------------
// 2) HARDWARE (E/S) - LEDs de status do controlador
// ------------------------------------------------------------
const int LED_SOLAR = 25;  // Verde  -> 100% da recarga vem do sol
const int LED_MISTO = 26;  // Amarelo -> parte solar, parte rede
const int LED_REDE  = 27;  // Vermelho -> 100% da recarga vem da rede

void apagarLeds() {
  digitalWrite(LED_SOLAR, LOW);
  digitalWrite(LED_MISTO, LOW);
  digitalWrite(LED_REDE, LOW);
}

// ------------------------------------------------------------
// 3) LOGICA DE DECISAO (a mesma regra de decidir_fonte_recarga()
//    do motor Python da Sprint 2: solar primeiro, rede so no que falta)
// ------------------------------------------------------------
struct Decisao {
  float kwhSolar;
  float kwhRede;
  int carregadoresAtivos;
};

Decisao decidirFonteRecarga(float geracaoSolarKw, int veiculosConectados) {
  Decisao d;
  float demandaTotalKw = veiculosConectados * POTENCIA_CARREGADOR_KW;

  if (demandaTotalKw == 0) {
    d.kwhSolar = 0;
    d.kwhRede = 0;
    d.carregadoresAtivos = 0;
    return d;
  }

  float solarUsada = min(geracaoSolarKw, demandaTotalKw);
  float redeUsada  = demandaTotalKw - solarUsada;

  d.kwhSolar = solarUsada;
  d.kwhRede = redeUsada;
  d.carregadoresAtivos = veiculosConectados;
  return d;
}

// ------------------------------------------------------------
// 4) COMANDO AUTOMATIZADO: aciona o LED conforme a decisao
// ------------------------------------------------------------
void acionarStatus(Decisao d) {
  apagarLeds();
  if (d.carregadoresAtivos == 0) {
    return; // nenhum veiculo conectado -> controlador em standby, sem LED
  }
  if (d.kwhRede == 0) {
    digitalWrite(LED_SOLAR, HIGH);      // 100% solar
  } else if (d.kwhSolar == 0) {
    digitalWrite(LED_REDE, HIGH);       // 100% rede
  } else {
    digitalWrite(LED_MISTO, HIGH);      // misto solar + rede
  }
}

// ------------------------------------------------------------
// 5) CENARIOS DE DEMONSTRACAO
//    Valores realistas dentro dos limites fisicos do sistema
//    (painel de 5 kWp, 4 pontos de 7,4 kW cada), representando
//    horarios tipicos que aparecem no historico de 30 dias
//    gerado pela simulacao Python da Sprint 2.
// ------------------------------------------------------------
struct Cenario {
  const char* horario;
  const char* descricao;
  float geracaoSolarKw;
  int veiculosConectados;
};

Cenario cenarios[] = {
  { "07h", "Manha - sol fraco, pico de chegada",      1.2, 3 },
  { "12h", "Meio-dia - sol forte, poucos carros",      4.6, 2 },
  { "14h", "Tarde nublada - sol moderado, 4 carros",   2.0, 4 },
  { "19h", "Fim de tarde - sol quase nulo, pico",      0.3, 4 },
  { "22h", "Noite - sem veiculos conectados",          0.0, 0 },
  { "03h", "Madrugada - sem sol, 1 carro",             0.0, 1 },
};
const int NUM_CENARIOS = 6;

// ------------------------------------------------------------
// 6) EXIBICAO DOS DADOS NO MONITOR SERIAL
// ------------------------------------------------------------
void exibirDados(Cenario c, Decisao d) {
  float kwhTotal   = d.kwhSolar + d.kwhRede;
  float co2Evitado = d.kwhSolar * FATOR_EMISSAO_CO2;
  float economia   = d.kwhSolar * TARIFA_KWH;
  float pctSolar    = (kwhTotal > 0) ? (d.kwhSolar / kwhTotal * 100.0) : 0.0;

  Serial.println();
  Serial.print(">> ");
  Serial.print(c.horario);
  Serial.print(" - ");
  Serial.println(c.descricao);
  Serial.print("   Geracao solar: ");
  Serial.print(c.geracaoSolarKw, 2);
  Serial.println(" kW");
  Serial.print("   Veiculos conectados: ");
  Serial.println(c.veiculosConectados);
  Serial.print("   Carregadores ativos: ");
  Serial.println(d.carregadoresAtivos);
  Serial.print("   kWh solar: ");
  Serial.print(d.kwhSolar, 3);
  Serial.print("   |  kWh rede: ");
  Serial.print(d.kwhRede, 3);
  Serial.print("   |  Aproveitamento solar: ");
  Serial.print(pctSolar, 1);
  Serial.println("%");
  Serial.print("   CO2 evitado: ");
  Serial.print(co2Evitado, 3);
  Serial.print(" kg  |  Economia: R$ ");
  Serial.println(economia, 2);

  if (d.carregadoresAtivos == 0) {
    Serial.println("   STATUS: EM ESPERA (sem veiculo conectado)");
  } else if (d.kwhRede == 0) {
    Serial.println("   STATUS: RECARGA 100% SOLAR");
  } else if (d.kwhSolar == 0) {
    Serial.println("   STATUS: RECARGA 100% REDE ELETRICA");
  } else {
    Serial.println("   STATUS: RECARGA MISTA (SOLAR + REDE)");
  }
}

// ------------------------------------------------------------
// 7) SETUP
// ------------------------------------------------------------
void setup() {
  pinMode(LED_SOLAR, OUTPUT);
  pinMode(LED_MISTO, OUTPUT);
  pinMode(LED_REDE, OUTPUT);
  apagarLeds();

  Serial.begin(115200);
  delay(1000);

  Serial.println("============================================================");
  Serial.println(" GREENCHARGE - CONTROLADOR DO ELETROPOSTO (EVSE)");
  Serial.println(" Prototipo Sprint 3 - integra com o motor de decisao Python");
  Serial.println(" da Sprint 2 (mesma logica: solar primeiro, rede no que falta)");
  Serial.println("============================================================");
}

// ------------------------------------------------------------
// 8) LOOP PRINCIPAL - percorre os cenarios continuamente
// ------------------------------------------------------------
void loop() {
  for (int i = 0; i < NUM_CENARIOS; i++) {
    Cenario c = cenarios[i];
    Decisao d = decidirFonteRecarga(c.geracaoSolarKw, c.veiculosConectados);

    acionarStatus(d);
    exibirDados(c, d);

    // tempo do LED aceso, para dar tempo de filmar cada cenario no video
    delay(4000);
  }
}
