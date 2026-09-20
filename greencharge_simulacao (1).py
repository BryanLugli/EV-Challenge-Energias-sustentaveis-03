"""
GreenCharge - Sistema de Gestão Inteligente de Eletropostos com Energia Solar
Sprint 2 - Prova de Conceito Funcional

Equipe:
  Bryan Lugli      - RM571350
  Beckman Lugli    - RM573442
  Guilherme Xavier - RM573053

EV Challenge 2026 - FIAP - Energias Renováveis e Sustentabilidade

Este script simula o funcionamento do sistema GreenCharge:
  - Leitura de geração solar (simulada no lugar da API GoodWe)
  - Lógica de recarga inteligente baseada na disponibilidade solar
  - Geração de relatório com CO2 evitado e economia financeira
  - Exportação de dados em JSON e CSV
"""

import json
import csv
import random
import math
import os
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIGURAÇÕES DO SISTEMA
# ─────────────────────────────────────────────
CAPACIDADE_PAINEL_KWP   = 5.0     # kWp instalados no eletroposto
POTENCIA_CARREGADOR_KW  = 7.4     # kW por ponto de recarga (AC monofásico)
NUM_PONTOS_RECARGA      = 4       # número de eletropostos no local
TARIFA_KWHE             = 0.85    # R$/kWh (tarifa ANEEL - referência SP 2024)
FATOR_EMISSAO_CO2       = 0.0897  # kg CO2 / kWh (fator médio SIN - MCTI 2023)
DIAS_SIMULACAO          = 30      # período do relatório
SEED_ALEATORIA          = 42      # garante reproducibilidade da simulação

random.seed(SEED_ALEATORIA)

# ─────────────────────────────────────────────
# GERAÇÃO SOLAR SIMULADA (substitui API GoodWe)
# ─────────────────────────────────────────────
def simular_geracao_solar_hora(hora: int, dia_do_ano: int) -> float:
    """
    Modela a curva de irradiância solar usando a equação do ângulo horário.
    
    Baseado no modelo de irradiância clara do céu (Clear Sky Model - Bird 1984),
    adaptado para latitude de São Paulo (-23,5°).
    
    Args:
        hora: hora do dia (0-23)
        dia_do_ano: dia sequencial do ano (1-365)
    
    Returns:
        Potência gerada em kW pelo painel de CAPACIDADE_PAINEL_KWP kWp
    """
    if hora < 6 or hora > 19:
        return 0.0

    # Declinação solar (fórmula de Spencer)
    declinacao = 23.45 * math.sin(math.radians(360 / 365 * (dia_do_ano - 81)))

    # Ângulo horário (graus — 15° por hora, 0 ao meio-dia solar)
    angulo_horario = 15 * (hora - 12)

    # Altitude solar (graus acima do horizonte) — latitude SP: -23.5°
    lat_rad = math.radians(-23.5)
    dec_rad = math.radians(declinacao)
    ha_rad  = math.radians(angulo_horario)

    seno_altitude = (
        math.sin(lat_rad) * math.sin(dec_rad)
        + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad)
    )
    altitude_graus = math.degrees(math.asin(max(0, seno_altitude)))

    # Irradiância em kW/m² (simplificada — Clear Sky)
    if altitude_graus <= 0:
        return 0.0
    irradiancia = 0.85 * math.sin(math.radians(altitude_graus))

    # Variação climática aleatória (±20%)
    fator_clima = random.uniform(0.80, 1.10)

    # Eficiência do painel: 18% (monocristalino típico) × área para 1 kWp (≈ 6,5 m²/kWp)
    area_m2        = CAPACIDADE_PAINEL_KWP * 6.5
    eficiencia     = 0.18
    potencia_kw    = irradiancia * area_m2 * eficiencia * fator_clima

    return round(min(potencia_kw, CAPACIDADE_PAINEL_KWP), 3)


# ─────────────────────────────────────────────
# LÓGICA DE RECARGA INTELIGENTE
# ─────────────────────────────────────────────
def decidir_fonte_recarga(geracao_solar_kw: float, veiculos_conectados: int) -> dict:
    """
    Algoritmo central do GreenCharge:
      1. Prioriza energia solar disponível.
      2. Complementa com rede elétrica apenas se necessário.
      3. Limita o número de carregadores ativos se houver excedente solar.

    Args:
        geracao_solar_kw: potência solar disponível no momento
        veiculos_conectados: quantos EVs estão conectados

    Returns:
        Dicionário com energia_solar_kw, energia_rede_kw, carregadores_ativos
    """
    demanda_total_kw = veiculos_conectados * POTENCIA_CARREGADOR_KW

    if demanda_total_kw == 0:
        return {"energia_solar_kw": 0, "energia_rede_kw": 0, "carregadores_ativos": 0}

    # Quanto a solar consegue atender
    solar_usada = min(geracao_solar_kw, demanda_total_kw)
    rede_usada  = demanda_total_kw - solar_usada

    return {
        "energia_solar_kw": round(solar_usada, 3),
        "energia_rede_kw":  round(rede_usada, 3),
        "carregadores_ativos": veiculos_conectados,
    }


# ─────────────────────────────────────────────
# SIMULAÇÃO PRINCIPAL (30 DIAS × 24 HORAS)
# ─────────────────────────────────────────────
def executar_simulacao() -> list[dict]:
    """Roda a simulação hora a hora por DIAS_SIMULACAO dias."""
    registros = []
    data_inicio = datetime(2026, 5, 1)

    print("=" * 60)
    print("  GreenCharge - Simulação de 30 dias")
    print("=" * 60)

    for dia in range(DIAS_SIMULACAO):
        data_atual = data_inicio + timedelta(days=dia)
        dia_do_ano = data_atual.timetuple().tm_yday

        for hora in range(24):
            # Demanda de veículos: pico manhã/tarde, baixa madrugada
            if 7 <= hora <= 9 or 17 <= hora <= 20:
                max_veiculos = NUM_PONTOS_RECARGA
            elif 10 <= hora <= 16:
                max_veiculos = NUM_PONTOS_RECARGA - 1
            elif 21 <= hora <= 23 or 0 <= hora <= 6:
                max_veiculos = random.randint(0, 1)
            else:
                max_veiculos = 2

            veiculos = random.randint(0, max_veiculos)
            solar_kw = simular_geracao_solar_hora(hora, dia_do_ano)
            decisao  = decidir_fonte_recarga(solar_kw, veiculos)

            # Energia em kWh (1 hora)
            kwh_solar = decisao["energia_solar_kw"]
            kwh_rede  = decisao["energia_rede_kw"]
            kwh_total = kwh_solar + kwh_rede

            registro = {
                "data":               data_atual.strftime("%Y-%m-%d"),
                "hora":               hora,
                "dia_do_ano":         dia_do_ano,
                "veiculos_conectados": veiculos,
                "geracao_solar_kw":   solar_kw,
                "carregadores_ativos": decisao["carregadores_ativos"],
                "kwh_solar":          round(kwh_solar, 4),
                "kwh_rede":           round(kwh_rede, 4),
                "kwh_total":          round(kwh_total, 4),
                "co2_evitado_kg":     round(kwh_solar * FATOR_EMISSAO_CO2, 4),
                "economia_reais":     round(kwh_solar * TARIFA_KWHE, 4),
            }
            registros.append(registro)

    print(f"  Simulação concluída: {len(registros)} registros gerados.")
    return registros


# ─────────────────────────────────────────────
# RELATÓRIO CONSOLIDADO
# ─────────────────────────────────────────────
def gerar_relatorio(registros: list[dict]) -> dict:
    """Consolida os dados e calcula métricas do período."""
    total_solar  = sum(r["kwh_solar"]      for r in registros)
    total_rede   = sum(r["kwh_rede"]       for r in registros)
    total_kwh    = sum(r["kwh_total"]      for r in registros)
    total_co2    = sum(r["co2_evitado_kg"] for r in registros)
    total_econ   = sum(r["economia_reais"] for r in registros)
    total_horas  = len([r for r in registros if r["kwh_total"] > 0])
    pct_solar    = (total_solar / total_kwh * 100) if total_kwh > 0 else 0

    relatorio = {
        "periodo":                      f"{registros[0]['data']} a {registros[-1]['data']}",
        "total_kwh_consumido":          round(total_kwh, 2),
        "total_kwh_solar":              round(total_solar, 2),
        "total_kwh_rede":               round(total_rede, 2),
        "percentual_solar_pct":         round(pct_solar, 2),
        "co2_evitado_total_kg":         round(total_co2, 2),
        "co2_evitado_total_ton":        round(total_co2 / 1000, 4),
        "economia_financeira_reais":    round(total_econ, 2),
        "horas_com_recarga":            total_horas,
        "meta_reducao_co2_anual_ton":   1.2,
        "projecao_anual_co2_ton":       round((total_co2 / 1000) * 12, 2),
        "ods_atendidos":                ["ODS 7", "ODS 9", "ODS 11", "ODS 13"],
        "capacidade_painel_kwp":        CAPACIDADE_PAINEL_KWP,
        "num_pontos_recarga":           NUM_PONTOS_RECARGA,
        "fator_emissao_co2_kg_kwh":     FATOR_EMISSAO_CO2,
        "tarifa_kwh_reais":             TARIFA_KWHE,
    }
    return relatorio


# ─────────────────────────────────────────────
# EXPORTAÇÃO DOS DADOS
# ─────────────────────────────────────────────
def exportar_csv(registros: list[dict], caminho: str):
    campos = list(registros[0].keys())
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(registros)
    print(f"  CSV salvo em: {caminho}")


def exportar_json(dados: dict, caminho: str):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  JSON salvo em: {caminho}")


# ─────────────────────────────────────────────
# IMPRESSÃO DO RELATÓRIO NO TERMINAL
# ─────────────────────────────────────────────
def imprimir_relatorio(rel: dict):
    print()
    print("=" * 60)
    print("  RELATÓRIO GREENCHARGE — PERÍODO: " + rel["periodo"])
    print("=" * 60)
    print(f"  Energia total consumida:   {rel['total_kwh_consumido']:>10.2f} kWh")
    print(f"  Energia solar utilizada:   {rel['total_kwh_solar']:>10.2f} kWh")
    print(f"  Energia da rede (grid):    {rel['total_kwh_rede']:>10.2f} kWh")
    print(f"  Aproveitamento solar:      {rel['percentual_solar_pct']:>9.1f} %")
    print("-" * 60)
    print(f"  CO₂ evitado no período:    {rel['co2_evitado_total_kg']:>10.2f} kg")
    print(f"  CO₂ evitado (toneladas):   {rel['co2_evitado_total_ton']:>10.4f} t")
    print(f"  Projeção anual de CO₂:     {rel['projecao_anual_co2_ton']:>10.2f} t")
    print(f"  Meta Sprint 1 (1 posto):               1.20 t/ano")
    print("-" * 60)
    print(f"  Economia financeira:       R$ {rel['economia_financeira_reais']:>8.2f}")
    print(f"  Tarifa de referência:      R$ {rel['tarifa_kwh_reais']:.2f}/kWh")
    print("-" * 60)
    print(f"  ODS atendidos:             {', '.join(rel['ods_atendidos'])}")
    print("=" * 60)
    print()


# ─────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("dados",      exist_ok=True)
    os.makedirs("relatorios", exist_ok=True)

    # 1. Simulação
    registros = executar_simulacao()

    # 2. Relatório
    relatorio = gerar_relatorio(registros)
    imprimir_relatorio(relatorio)

    # 3. Exportação
    exportar_csv(registros,  "dados/greencharge_historico_30dias.csv")
    exportar_json(relatorio, "relatorios/greencharge_relatorio_maio2026.json")

    print("  Simulação finalizada com sucesso!")
    print("  Arquivos gerados em ./dados/ e ./relatorios/")
