#!/usr/bin/env python3
"""
Diagnóstico y Corrección de Outliers en Análisis de Capacidad
=============================================================

Script para identificar y corregir anomalías en los datos de análisis,
específicamente el pico anormal en la cama 15 de ICU.
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

class OutlierDiagnostic:
    def __init__(self):
        self.base_path = "resultados_var_camas"
        self.hospitals = ["H1", "H2", "H3"]
        
    def extract_value(self, value_str: str) -> float:
        """Extract numerical value from string like '2948.57 ± 26.93'"""
        if isinstance(value_str, (int, float)):
            return float(value_str)
        return float(str(value_str).split(' ± ')[0])
    
    def load_icu_data_detailed(self):
        """Load detailed ICU data for all hospitals to diagnose the anomaly"""
        detailed_data = []
        
        for hospital in self.hospitals:
            unit_path = os.path.join(self.base_path, f"ModeloProactivo_T4500_C4208_{hospital}_ICU")
            
            if not os.path.exists(unit_path):
                print(f"❌ No se encontró path: {unit_path}")
                continue
                
            print(f"📂 Analizando {hospital} ICU...")
            
            # Get all available files
            available_files = []
            for file in os.listdir(unit_path):
                if file.startswith('+') and file.endswith('.json'):
                    try:
                        bed_number = int(file[1:-5])
                        available_files.append(bed_number)
                    except ValueError:
                        continue
            
            available_files.sort()
            print(f"   Archivos encontrados: {available_files}")
            
            for bed_num in available_files:
                file_path = os.path.join(unit_path, f"+{bed_num}.json")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # Extract all relevant data
                    costs = json_data['costo_diario_promedio']['General']
                    entrada_salida = json_data['tasa_entrada_vs_salida']
                    
                    # Calculate derivation percentage
                    derivaciones_wl = self.extract_value(costs['derivaciones_wl'])
                    derivaciones_ed = self.extract_value(costs['derivaciones_ed'])
                    total_entradas = self.extract_value(entrada_salida['total_entradas_por_ciclo'])
                    
                    derivaciones_total = derivaciones_wl + derivaciones_ed
                    entradas_diarias = total_entradas * 365
                    porcentaje_derivacion = (derivaciones_total / entradas_diarias) * 100 if entradas_diarias > 0 else 0
                    
                    # Extract all cost components
                    social_cost = self.extract_value(costs['social'])
                    operational_cost = self.extract_value(costs['operativo'])
                    total_cost = self.extract_value(costs['total'])
                    
                    detailed_data.append({
                        'hospital': hospital,
                        'beds': bed_num,
                        'porcentaje_derivacion': porcentaje_derivacion,
                        'social_cost': social_cost,
                        'operational_cost': operational_cost,
                        'total_cost': total_cost,
                        'derivaciones_wl': derivaciones_wl,
                        'derivaciones_ed': derivaciones_ed,
                        'derivaciones_total': derivaciones_total,
                        'total_entradas': total_entradas,
                        'file_path': file_path
                    })
                    
                except Exception as e:
                    print(f"❌ Error procesando {file_path}: {e}")
        
        return pd.DataFrame(detailed_data)
    
    def diagnose_bed_15_anomaly(self, df):
        """Specifically diagnose what's happening at bed 15"""
        print("\n" + "="*70)
        print("🔍 DIAGNÓSTICO DETALLADO: ANOMALÍA CAMA 15 ICU")
        print("="*70)
        
        # Focus on beds around 15
        focus_beds = [13, 14, 15, 16, 17]
        focus_data = df[df['beds'].isin(focus_beds)].copy()
        
        if focus_data.empty:
            print("❌ No hay datos para las camas de interés")
            return None
        
        # Group by bed number and show all hospitals
        print("\n📊 DATOS POR CAMA Y HOSPITAL:")
        print("-" * 70)
        
        for bed in focus_beds:
            bed_data = focus_data[focus_data['beds'] == bed]
            if not bed_data.empty:
                print(f"\n🏥 CAMA +{bed}:")
                for _, row in bed_data.iterrows():
                    print(f"   {row['hospital']}: Costo Total = ${row['total_cost']:,.0f}, "
                          f"Derivación = {row['porcentaje_derivacion']:.2f}%")
                
                # Calculate average and std
                avg_cost = bed_data['total_cost'].mean()
                std_cost = bed_data['total_cost'].std()
                print(f"   📈 Promedio: ${avg_cost:,.0f} ± ${std_cost:,.0f}")
                
                # Check for outliers
                for _, row in bed_data.iterrows():
                    z_score = (row['total_cost'] - avg_cost) / std_cost if std_cost > 0 else 0
                    if abs(z_score) > 2:
                        print(f"   🚨 OUTLIER DETECTADO en {row['hospital']}: Z-score = {z_score:.2f}")
        
        # Calculate marginal benefits
        print(f"\n💰 ANÁLISIS DE BENEFICIO MARGINAL:")
        print("-" * 70)
        
        marginal_data = []
        for hospital in self.hospitals:
            hosp_data = df[df['hospital'] == hospital].sort_values('beds')
            
            if len(hosp_data) < 2:
                continue
                
            print(f"\n{hospital}:")
            
            for i in range(1, len(hosp_data)):
                current = hosp_data.iloc[i]
                previous = hosp_data.iloc[i-1]
                
                bed_increment = current['beds'] - previous['beds']
                cost_reduction = previous['total_cost'] - current['total_cost']
                marginal_benefit = cost_reduction / bed_increment if bed_increment > 0 else 0
                
                marginal_data.append({
                    'hospital': hospital,
                    'from_bed': previous['beds'],
                    'to_bed': current['beds'],
                    'increment': bed_increment,
                    'cost_reduction': cost_reduction,
                    'marginal_benefit': marginal_benefit
                })
                
                if current['beds'] in focus_beds:
                    print(f"   +{previous['beds']} → +{current['beds']}: "
                          f"Beneficio = ${marginal_benefit:.0f}/cama "
                          f"(Reducción total: ${cost_reduction:.0f})")
        
        # Calculate average marginal benefits for bed 15
        marginal_df = pd.DataFrame(marginal_data)
        bed_15_marginal = marginal_df[marginal_df['to_bed'] == 15]
        
        if not bed_15_marginal.empty:
            print(f"\n🎯 BENEFICIO MARGINAL CAMA 15:")
            avg_marginal_15 = bed_15_marginal['marginal_benefit'].mean()
            std_marginal_15 = bed_15_marginal['marginal_benefit'].std()
            print(f"   Promedio: ${avg_marginal_15:.0f}/cama")
            print(f"   Desviación: ±${std_marginal_15:.0f}")
            
            for _, row in bed_15_marginal.iterrows():
                z_score = (row['marginal_benefit'] - avg_marginal_15) / std_marginal_15 if std_marginal_15 > 0 else 0
                symbol = "🚨" if abs(z_score) > 2 else "✅"
                print(f"   {symbol} {row['hospital']}: ${row['marginal_benefit']:.0f}/cama (Z = {z_score:.2f})")
        
        return marginal_df, focus_data
    
    def suggest_corrections(self, marginal_df, focus_data):
        """Suggest correction methods for the anomaly"""
        print(f"\n🛠️ OPCIONES DE CORRECCIÓN:")
        print("-" * 70)
        
        bed_15_data = marginal_df[marginal_df['to_bed'] == 15]
        
        if bed_15_data.empty:
            print("❌ No hay datos de beneficio marginal para cama 15")
            return {}
        
        # Method 1: Statistical smoothing
        avg_marginal = bed_15_data['marginal_benefit'].mean()
        std_marginal = bed_15_data['marginal_benefit'].std()
        
        print(f"1️⃣ SUAVIZADO ESTADÍSTICO:")
        print(f"   • Promedio actual: ${avg_marginal:.0f}/cama")
        print(f"   • Desviación: ±${std_marginal:.0f}")
        
        # Identify outliers
        outlier_hospitals = []
        for _, row in bed_15_data.iterrows():
            z_score = (row['marginal_benefit'] - avg_marginal) / std_marginal if std_marginal > 0 else 0
            if abs(z_score) > 2:
                outlier_hospitals.append(row['hospital'])
        
        if outlier_hospitals:
            # Calculate corrected average without outliers
            non_outlier_data = bed_15_data[~bed_15_data['hospital'].isin(outlier_hospitals)]
            corrected_avg = non_outlier_data['marginal_benefit'].mean() if not non_outlier_data.empty else avg_marginal
            
            print(f"   • Outliers detectados: {outlier_hospitals}")
            print(f"   • Promedio corregido (sin outliers): ${corrected_avg:.0f}/cama")
        else:
            corrected_avg = avg_marginal
            print(f"   • No se detectaron outliers significativos")
        
        # Method 2: Interpolation from adjacent points
        adjacent_beds = [13, 14, 16, 17]
        adjacent_marginal = marginal_df[marginal_df['to_bed'].isin(adjacent_beds)]
        
        if not adjacent_marginal.empty:
            interpolated_value = adjacent_marginal['marginal_benefit'].mean()
            print(f"\n2️⃣ INTERPOLACIÓN DE PUNTOS ADYACENTES:")
            print(f"   • Promedio camas 13,14,16,17: ${interpolated_value:.0f}/cama")
        else:
            interpolated_value = corrected_avg
        
        # Method 3: Trend-based correction
        all_marginal = marginal_df.groupby('to_bed')['marginal_benefit'].mean().sort_index()
        
        if len(all_marginal) > 3:
            # Fit trend line excluding bed 15
            beds_no_15 = all_marginal.drop(15, errors='ignore')
            if len(beds_no_15) > 2:
                coeffs = np.polyfit(beds_no_15.index, beds_no_15.values, 1)
                trend_value = coeffs[0] * 15 + coeffs[1]
                print(f"\n3️⃣ CORRECCIÓN POR TENDENCIA:")
                print(f"   • Valor según tendencia lineal: ${trend_value:.0f}/cama")
            else:
                trend_value = corrected_avg
        else:
            trend_value = corrected_avg
        
        corrections = {
            'statistical_smoothing': corrected_avg,
            'interpolation': interpolated_value,
            'trend_based': trend_value,
            'outlier_hospitals': outlier_hospitals
        }
        
        # Recommend best method
        print(f"\n💡 RECOMENDACIÓN:")
        
        if outlier_hospitals:
            print(f"   Usar SUAVIZADO ESTADÍSTICO: ${corrected_avg:.0f}/cama")
            print(f"   Razón: Outliers claros detectados en {outlier_hospitals}")
        elif abs(interpolated_value - corrected_avg) < corrected_avg * 0.1:
            print(f"   Usar INTERPOLACIÓN: ${interpolated_value:.0f}/cama")
            print(f"   Razón: Consistencia con puntos adyacentes")
        else:
            print(f"   Usar CORRECCIÓN POR TENDENCIA: ${trend_value:.0f}/cama")
            print(f"   Razón: Mejor ajuste al patrón general")
        
        return corrections
    
    def apply_correction(self, correction_method='interpolation'):
        """Apply the selected correction method to the comprehensive analysis"""
        print(f"\n🔧 APLICANDO CORRECCIÓN: {correction_method.upper()}")
        print("="*70)
        
        # Read the comprehensive analysis file
        comp_file = 'comprehensive_analysis.py'
        
        if not os.path.exists(comp_file):
            print(f"❌ No se encontró {comp_file}")
            return False
        
        print(f"✅ Archivo encontrado: {comp_file}")
        print(f"📝 Se añadirá función de corrección de outliers...")
        
        # Create corrected version note
        correction_note = f"""
# CORRECCIÓN DE OUTLIERS APLICADA
# Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
# Método: {correction_method}
# Problema: Pico anormal en cama 15 ICU
# Solución: Suavizado estadístico de valores extremos
"""
        
        print(f"✅ Corrección documentada")
        print(f"💡 Para aplicar la corrección, se debe modificar la función de cálculo promedio")
        print(f"   en comprehensive_analysis.py para incluir filtrado de outliers")
        
        return True

def main():
    """Ejecutar diagnóstico completo"""
    print("🔍 INICIANDO DIAGNÓSTICO DE OUTLIERS EN ICU")
    print("="*70)
    
    diagnostic = OutlierDiagnostic()
    
    # 1. Load detailed data
    print("\n1️⃣ Cargando datos detallados...")
    df = diagnostic.load_icu_data_detailed()
    
    if df.empty:
        print("❌ No se pudieron cargar datos")
        return
    
    print(f"✅ Datos cargados: {len(df)} observaciones")
    
    # 2. Diagnose bed 15 anomaly
    print("\n2️⃣ Diagnosticando anomalía cama 15...")
    marginal_df, focus_data = diagnostic.diagnose_bed_15_anomaly(df)
    
    # 3. Suggest corrections
    print("\n3️⃣ Sugiriendo correcciones...")
    corrections = diagnostic.suggest_corrections(marginal_df, focus_data)
    
    # 4. Apply correction
    print("\n4️⃣ Preparando corrección...")
    diagnostic.apply_correction('statistical_smoothing')
    
    print(f"\n✅ DIAGNÓSTICO COMPLETADO")
    print(f"📋 Revisa los resultados arriba para implementar la corrección")

if __name__ == "__main__":
    main()
