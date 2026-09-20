# EV-Challenge-Energias-sustentaveis-03

# GreenCharge — Sprint 03: Prototipagem Funcional e Integração

Essa sprint é sobre mostrar a integração funcionando de verdade, não só no papel. Pegamos o
motor de decisão em Python que já tínhamos validado na Sprint 2 e construímos um protótipo
simulado que representa o **Controlador do Eletroposto (EVSE)** — a peça que recebe a decisão
e transforma isso em ação real.

## O que tem aqui

| Arquivo | O que é |
|---|---|
| `greencharge_prototipo.ino` | Código do protótipo pro Wokwi (ESP32) — a mesma lógica de decisão da Sprint 2, agora rodando no controlador |
| `greencharge_diagram.json` | Circuito do Wokwi (ESP32 + 3 LEDs de status) |
| `relatorio_integracao.pdf` | Documentação técnica completa: equipe, esquema de integração, justificativa, resultados e conexão com a disciplina |
| `entrega-sprint3-gs.txt` | Nome e RM de cada integrante + links de vídeo e repositório |

## Como rodar no Wokwi

1. Entra em **wokwi.com**, faz login e clica em **"+ New Project"**.
2. Escolhe o template **ESP32**.
3. Na aba do código (`sketch.ino`), apaga o conteúdo padrão e cola o `greencharge_prototipo.ino`.
4. Na aba `diagram.json`, apaga tudo e cola o `greencharge_diagram.json` (já vem com os 3 LEDs
   nos pinos D25, D26 e D27 do ESP32).
5. Aperta o **▶ Play**.
6. Abre o Monitor Serial pra ver os dados de cada cenário — geração solar, kWh solar/rede,
   CO₂ evitado, economia.
7. Os LEDs vão trocando entre verde (100% solar), amarelo (misto) e vermelho (100% rede) a
   cada uns 4 segundos. É essa tela que dá pra gravar no vídeo.

## Como isso se conecta com a Sprint 2

A regra de decisão que colocamos no ESP32 (função `decidirFonteRecarga()`) é basicamente a
mesma coisa que a `decidir_fonte_recarga()` do `greencharge_simulacao.py`: usa solar primeiro,
completa com a rede só no que faltar. A ideia é que esse protótipo não é uma peça isolada —
ele é o próximo passo natural do diagrama de arquitetura que já tínhamos: o bloco "Controlador
OCPP/EVSE" que pega a decisão do motor Python e faz alguma coisa de verdade com ela.


