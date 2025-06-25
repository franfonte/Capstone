import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict

class HospitalCapacityAnalyzer:
    def __init__(self, discount_rate: float = 0.01):
        """
        Analyzer for hospital capacity expansion analysis
        
        Args:
            discount_rate: Daily discount rate for NPV calculations (default 1%)
        """
        self.discount_rate = discount_rate
        self.daily_discount_rate = discount_rate  # Use the rate directly as it's already daily
        self.base_path = "resultados_var_camas"
        
        # Define all combinations to analyze
        self.units = [
            ("H1", "ICU"), ("H1", "OR"), ("H1", "SDU_WARD"),
            ("H2", "ICU"), ("H2", "OR"), ("H2", "SDU_WARD"),
            ("H3", "ICU"), ("H3", "OR"), ("H3", "SDU_WARD")
        ]
        
        self.results = {}
    
    def extract_cost_value(self, cost_str: str) -> float:
        """Extract numerical value from cost string like '187.55 ± 5.92'"""
        return float(cost_str.split(' ± ')[0])
    
    def load_unit_costs(self, hospital: str, unit: str) -> List[Dict]:
        """Load cost data for a specific hospital/unit combination"""
        folder_name = f"ModeloProactivo_T4500_C4208_{hospital}_{unit}"
        unit_path = os.path.join(self.base_path, folder_name)
        
        if not os.path.exists(unit_path):
            print(f"Warning: Path not found: {unit_path}")
            return []
        
        # First, discover what files actually exist
        available_files = []
        for file in os.listdir(unit_path):
            if file.startswith('+') and file.endswith('.json'):
                try:
                    bed_number = int(file[1:-5])  # Extract number from "+X.json"
                    available_files.append(bed_number)
                except ValueError:
                    continue
        
        if not available_files:
            print(f"Warning: No valid increment files found in {unit_path}")
            return []
        
        available_files.sort()
        print(f"  Encontrados archivos para {hospital} {unit}: +{min(available_files)} a +{max(available_files)} ({len(available_files)} archivos)")
        
        data = []
        
        # Process only the files that actually exist
        for i in available_files:
            file_path = os.path.join(unit_path, f"+{i}.json")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                costs = json_data['costo_diario_promedio']['General']
                
                # Also get patient information if available
                patient_info = json_data.get('tasa_entrada_vs_salida', {})
                total_patients = patient_info.get('total_entradas_por_ciclo', '0 ± 0')
                
                data.append({
                    'beds': i,
                    'social': self.extract_cost_value(costs['social']),
                    'operational': self.extract_cost_value(costs['operativo']),
                    'total': self.extract_cost_value(costs['total']),
                    'patients_per_cycle': self.extract_cost_value(total_patients) if isinstance(total_patients, str) else 0
                })
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return data
    
    def calculate_marginal_analysis(self, data: List[Dict]) -> Dict:
        """Calculate comprehensive marginal analysis"""
        if len(data) < 2:
            return {}
        
        marginal_data = []
        
        for i in range(1, len(data)):
            prev = data[i-1]
            curr = data[i]
            
            # Calculate the actual increment in beds
            bed_increment = curr['beds'] - prev['beds']
            
            # Basic marginal benefits (cost reductions)
            total_benefit_social = prev['social'] - curr['social']
            total_benefit_operational = prev['operational'] - curr['operational']
            total_benefit_total = prev['total'] - curr['total']
            
            # Marginal benefit per bed (benefit divided by number of beds added)
            marginal_social = total_benefit_social / bed_increment if bed_increment > 0 else 0
            marginal_operational = total_benefit_operational / bed_increment if bed_increment > 0 else 0
            marginal_total = total_benefit_total / bed_increment if bed_increment > 0 else 0
            
            # NPV calculation (daily benefit extended to perpetuity)
            # NPV = Daily_Benefit / daily_discount_rate (perpetuity formula)
            npv_social = marginal_social / self.daily_discount_rate if self.daily_discount_rate > 0 else 0
            npv_operational = marginal_operational / self.daily_discount_rate if self.daily_discount_rate > 0 else 0
            npv_total = marginal_total / self.daily_discount_rate if self.daily_discount_rate > 0 else 0
            
            # Annual benefit
            annual_social = marginal_social * 365
            annual_operational = marginal_operational * 365
            annual_total = marginal_total * 365
            
            # Per-patient benefit (if patient data available)
            per_patient_social = marginal_social / curr['patients_per_cycle'] if curr['patients_per_cycle'] > 0 else 0
            per_patient_operational = marginal_operational / curr['patients_per_cycle'] if curr['patients_per_cycle'] > 0 else 0
            per_patient_total = marginal_total / curr['patients_per_cycle'] if curr['patients_per_cycle'] > 0 else 0
            
            marginal_data.append({
                'bed_number': curr['beds'],
                'bed_increment': bed_increment,
                'total_benefit_social': total_benefit_social,
                'total_benefit_operational': total_benefit_operational,
                'total_benefit_total': total_benefit_total,
                'marginal_social': marginal_social,
                'marginal_operational': marginal_operational,
                'marginal_total': marginal_total,
                'npv_social': npv_social,
                'npv_operational': npv_operational,
                'npv_total': npv_total,
                'annual_social': annual_social,
                'annual_operational': annual_operational,
                'annual_total': annual_total,
                'per_patient_social': per_patient_social,
                'per_patient_operational': per_patient_operational,
                'per_patient_total': per_patient_total
            })
        
        # Find optimal points
        total_costs = [d['total'] for d in data]
        min_cost_index = total_costs.index(min(total_costs))
        optimal_beds = data[min_cost_index]['beds']
        
        # Find last positive marginal benefit (both total and operational)
        positive_marginal_total = [m for m in marginal_data if m['marginal_total'] > 0]
        positive_marginal_operational = [m for m in marginal_data if m['marginal_operational'] > 0]
        
        last_beneficial_bed_total = positive_marginal_total[-1]['bed_number'] if positive_marginal_total else 1
        last_beneficial_bed_operational = positive_marginal_operational[-1]['bed_number'] if positive_marginal_operational else 1
        
        # Calculate cumulative benefits (using total benefits, not marginal)
        cumulative_benefit_total = sum(m['total_benefit_total'] for m in marginal_data if m['marginal_total'] > 0)
        cumulative_benefit_operational = sum(m['total_benefit_operational'] for m in marginal_data if m['marginal_operational'] > 0)
        
        # Calculate cumulative NPV (using marginal NPV * bed increment for each step)
        cumulative_npv_total = sum(m['npv_total'] * m['bed_increment'] for m in marginal_data if m['marginal_total'] > 0)
        cumulative_npv_operational = sum(m['npv_operational'] * m['bed_increment'] for m in marginal_data if m['marginal_operational'] > 0)
        
        # Find maximum NPV per bed for each type
        max_npv_per_bed_total = max([m['npv_total'] for m in marginal_data]) if marginal_data else 0
        max_npv_per_bed_operational = max([m['npv_operational'] for m in marginal_data]) if marginal_data else 0
        
        return {
            'marginal_data': marginal_data,
            'optimal_beds': optimal_beds,
            'min_total_cost': min(total_costs),
            'last_beneficial_bed': last_beneficial_bed_total,
            'last_beneficial_bed_operational': last_beneficial_bed_operational,
            'cumulative_benefit_daily': cumulative_benefit_total,
            'cumulative_benefit_operational': cumulative_benefit_operational,
            'cumulative_npv': cumulative_npv_total,
            'cumulative_npv_operational': cumulative_npv_operational,
            'max_npv_per_bed': max_npv_per_bed_total,
            'max_npv_per_bed_operational': max_npv_per_bed_operational
        }
    
    def create_unit_plot(self, hospital: str, unit: str, data: List[Dict], analysis: Dict) -> str:
        """Create plot for a specific hospital/unit combination"""
        if not data or not analysis:
            return ""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Extract data for plotting
        beds = [d['beds'] for d in data]
        social_costs = [d['social'] for d in data]
        operational_costs = [d['operational'] for d in data]
        total_costs = [d['total'] for d in data]
        
        marginal_data = analysis['marginal_data']
        marginal_beds = [m['bed_number'] for m in marginal_data]
        marginal_total = [m['marginal_total'] for m in marginal_data]
        marginal_social = [m['marginal_social'] for m in marginal_data]
        marginal_operational = [m['marginal_operational'] for m in marginal_data]
        npv_total = [m['npv_total'] for m in marginal_data]
        npv_operational = [m['npv_operational'] for m in marginal_data]
        npv_social = [m['npv_social'] for m in marginal_data]
        
        # Plot 1: Cost Evolution
        ax1.plot(beds, social_costs, 'ro-', linewidth=2, markersize=4, label='Social')
        ax1.plot(beds, operational_costs, 'bo-', linewidth=2, markersize=4, label='Operativo')
        ax1.plot(beds, total_costs, 'go-', linewidth=2, markersize=4, label='Total')
        ax1.axvline(x=analysis['optimal_beds'], color='purple', linestyle='--', alpha=0.7, label=f'Óptimo (+{analysis["optimal_beds"]})')
        
        ax1.set_xlabel('Camas Adicionales')
        ax1.set_ylabel('Costo Diario')
        ax1.set_title(f'Evolución de Costos - {hospital} {unit}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Marginal Benefits
        ax2.plot(marginal_beds, marginal_social, 'ro-', linewidth=2, markersize=4, label='Social')
        ax2.plot(marginal_beds, marginal_operational, 'bo-', linewidth=2, markersize=4, label='Operativo')
        ax2.plot(marginal_beds, marginal_total, 'go-', linewidth=2, markersize=4, label='Total')
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.axvline(x=analysis['last_beneficial_bed'], color='red', linestyle='--', alpha=0.7, 
                   label=f'Última beneficiosa (+{analysis["last_beneficial_bed"]})')
        
        ax2.set_xlabel('Cama Adicional #')
        ax2.set_ylabel('Beneficio Marginal Diario por Cama')
        ax2.set_title('Beneficio Marginal por Cama (Ajustado por Incremento)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Add annotation showing bed increments for first few points
        for i, m in enumerate(marginal_data[:3]):
            if m['bed_increment'] > 1:
                ax2.annotate(f"Δ{m['bed_increment']}", 
                           xy=(m['bed_number'], m['marginal_total']), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.7)
        
        # Plot 3: NPV Analysis - Separated by type
        ax3.plot(marginal_beds, npv_operational, 'bo-', linewidth=2, markersize=4, label='VAN Operativo')
        ax3.plot(marginal_beds, npv_social, 'ro-', linewidth=2, markersize=4, label='VAN Social')
        ax3.plot(marginal_beds, npv_total, 'go-', linewidth=2, markersize=4, label='VAN Total')
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Find max NPV for operational costs specifically
        max_npv_operational = max(npv_operational) if npv_operational else 0
        max_npv_op_bed = marginal_beds[npv_operational.index(max_npv_operational)] if npv_operational and max_npv_operational > 0 else 0
        if max_npv_op_bed > 0:
            ax3.axvline(x=max_npv_op_bed, color='blue', linestyle='--', alpha=0.7, 
                       label=f'Max VAN Op (+{max_npv_op_bed})')
        
        ax3.set_xlabel('Cama Adicional #')
        ax3.set_ylabel('VAN de beneficio marginal')
        ax3.set_title(f'VAN por Tipo de Costo (Tasa: {self.discount_rate:.1%})')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Additional analysis space (no summary box)
        ax4.axis('off')
        
        plt.tight_layout()
        
        # Save plot
        filename = f"analisis_{hospital}_{unit}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def analyze_all_units(self):
        """Analyze all hospital/unit combinations"""
        print("=== ANÁLISIS COMPLETO DE CAPACIDAD HOSPITALARIA ===")
        print(f"Tasa de descuento: {self.discount_rate:.1%} anual\n")
        
        summary_data = []
        
        for hospital, unit in self.units:
            print(f"Procesando {hospital} {unit}...")
            
            # Load data
            data = self.load_unit_costs(hospital, unit)
            if not data:
                print(f"  No se encontraron datos para {hospital} {unit}")
                continue
            
            # Analyze
            analysis = self.calculate_marginal_analysis(data)
            if not analysis:
                print(f"  No se pudo analizar {hospital} {unit}")
                continue
            
            # Create plot
            filename = self.create_unit_plot(hospital, unit, data, analysis)
            
            # Store results
            self.results[f"{hospital}_{unit}"] = {
                'data': data,
                'analysis': analysis,
                'plot_file': filename
            }
            
            # Add to summary
            summary_data.append({
                'Hospital': hospital,
                'Unidad': unit,
                'Camas_Optimas': analysis['optimal_beds'],
                'Costo_Minimo': analysis['min_total_cost'],
                'Ultima_Beneficiosa_Total': analysis['last_beneficial_bed'],
                'Ultima_Beneficiosa_Operativo': analysis['last_beneficial_bed_operational'],
                'VAN_Maximo_Cama_Total': analysis['max_npv_per_bed'],
                'VAN_Maximo_Cama_Operativo': analysis['max_npv_per_bed_operational'],
                'VAN_Total_Acumulado': analysis['cumulative_npv'],
                'VAN_Operativo_Acumulado': analysis['cumulative_npv_operational'],
                'Beneficio_Diario_Acumulado': analysis['cumulative_benefit_daily'],
                'Beneficio_Operativo_Acumulado': analysis['cumulative_benefit_operational']
            })
            
            print(f"  ✓ Completado - Óptimo: +{analysis['optimal_beds']} camas")
        
        # Create summary
        self.create_summary_analysis(summary_data)
        
        # Generate average plots by unit type
        self.create_average_plots_by_unit_type()
        
        # Store summary data for potential external use
        self.summary_data = summary_data
        
        print(f"\n=== ANÁLISIS COMPLETADO ===")
        print(f"Se analizaron {len(self.results)} unidades")
        print("Archivos generados:")
        for key, result in self.results.items():
            print(f"  - {result['plot_file']}")
        print("  - resumen_analisis_capacidad.png")
        print("  - resumen_analisis_capacidad.csv")
        print("  - promedio_analisis_ICU.png")
        print("  - promedio_analisis_OR.png")
        print("  - promedio_analisis_SDU_WARD.png")
    
    def create_summary_analysis(self, summary_data: List[Dict]):
        """Create summary analysis and comparison"""
        if not summary_data:
            return
        
        df = pd.DataFrame(summary_data)
        
        # Save CSV
        df.to_csv('resumen_analisis_capacidad.csv', index=False)
        
        # Create summary plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Optimal beds by unit
        units = df['Hospital'] + '_' + df['Unidad']
        ax1.bar(range(len(units)), df['Camas_Optimas'], color='skyblue')
        ax1.set_xticks(range(len(units)))
        ax1.set_xticklabels(units, rotation=45)
        ax1.set_ylabel('Camas Óptimas')
        ax1.set_title('Número Óptimo de Camas por Unidad')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: NPV comparison - Total vs Operational
        width = 0.35
        x = np.arange(len(units))
        ax2.bar(x - width/2, df['VAN_Maximo_Cama_Total'], width, label='VAN Total', color='lightgreen')
        ax2.bar(x + width/2, df['VAN_Maximo_Cama_Operativo'], width, label='VAN Operativo', color='lightblue')
        ax2.set_xticks(x)
        ax2.set_xticklabels(units, rotation=45)
        ax2.set_ylabel('VAN Máximo por Cama')
        ax2.set_title('Comparación VAN Total vs Operativo por Cama')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Total accumulated NPV comparison
        ax3.bar(x - width/2, df['VAN_Total_Acumulado'], width, label='VAN Total', color='gold')
        ax3.bar(x + width/2, df['VAN_Operativo_Acumulado'], width, label='VAN Operativo', color='orange')
        ax3.set_xticks(x)
        ax3.set_xticklabels(units, rotation=45)
        ax3.set_ylabel('VAN Acumulado')
        ax3.set_title('VAN Acumulado: Total vs Solo Operativo')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Summary Statistics (commented out for cleaner look)
        ax4.axis('off')
        
        # Remove the summary box - just leave the axis empty for cleaner look
        # ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=11,
        #         verticalalignment='top', fontfamily='monospace',
        #         bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('resumen_analisis_capacidad.png', dpi=300, bbox_inches='tight')
        plt.close()

    def extract_kpi_value(self, kpi_str: str) -> float:
        """Extract numerical value from KPI string like '2948.57 ± 26.93'"""
        return float(kpi_str.split(' ± ')[0])
    
    def load_unit_kpis(self, hospital: str, unit: str) -> List[Dict]:
        """Load KPI data for a specific hospital/unit combination"""
        folder_name = f"ModeloProactivo_T4500_C4208_{hospital}_{unit}"
        unit_path = os.path.join(self.base_path, folder_name)
        
        if not os.path.exists(unit_path):
            return []
        
        # Discover available files
        available_files = []
        for file in os.listdir(unit_path):
            if file.startswith('+') and file.endswith('.json'):
                try:
                    bed_number = int(file[1:-5])
                    available_files.append(bed_number)
                except ValueError:
                    continue
        
        available_files.sort()
        data = []
        
        for i in available_files:
            file_path = os.path.join(unit_path, f"+{i}.json")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Extract KPI data
                costs = json_data['costo_diario_promedio']['General']
                entrada_salida = json_data['tasa_entrada_vs_salida']
                
                # Calculate derivation percentages
                derivaciones_wl = self.extract_kpi_value(costs['derivaciones_wl'])
                derivaciones_ed = self.extract_kpi_value(costs['derivaciones_ed'])
                total_entradas = self.extract_kpi_value(entrada_salida['total_entradas_por_ciclo'])
                
                # Calculate daily values (assuming 365 days per year and cycles)
                derivaciones_total = derivaciones_wl + derivaciones_ed
                porcentaje_derivacion = (derivaciones_total / (total_entradas * 365)) * 100 if total_entradas > 0 else 0
                
                data.append({
                    'beds': i,
                    'derivaciones_wl': derivaciones_wl,
                    'derivaciones_ed': derivaciones_ed,
                    'derivaciones_total': derivaciones_total,
                    'total_entradas_ciclo': total_entradas,
                    'porcentaje_derivacion': porcentaje_derivacion,
                    'social': self.extract_cost_value(costs['social']),
                    'operational': self.extract_cost_value(costs['operativo']),
                    'total': self.extract_cost_value(costs['total'])
                })
                
            except Exception as e:
                print(f"Error processing KPIs from {file_path}: {e}")
        
        return data

    def create_average_plots_by_unit_type(self):
        """Create average plots for each unit type (ICU, OR, SDU_WARD)"""
        print("\n=== GENERANDO GRÁFICOS PROMEDIO POR TIPO DE UNIDAD ===")
        
        # Group data by unit type
        unit_types = ['ICU', 'OR', 'SDU_WARD']
        
        for unit_type in unit_types:
            print(f"\nProcesando tipo de unidad: {unit_type}")
            
            # Collect data from all hospitals for this unit type
            all_data = []
            all_kpis = []
            
            for hospital in ['H1', 'H2', 'H3']:
                costs_data = self.load_unit_costs(hospital, unit_type)
                kpi_data = self.load_unit_kpis(hospital, unit_type)
                
                if costs_data and kpi_data:
                    all_data.extend(costs_data)
                    all_kpis.extend(kpi_data)
            
            if not all_data:
                print(f"  No se encontraron datos para {unit_type}")
                continue
            
            # Group by bed number and calculate averages
            bed_averages = defaultdict(lambda: {
                'costs': [], 'operational': [], 'total': [],
                'derivaciones': [], 'porcentaje_derivacion': []
            })
            
            for d in all_data:
                bed_averages[d['beds']]['costs'].append(d['social'])
                bed_averages[d['beds']]['operational'].append(d['operational'])
                bed_averages[d['beds']]['total'].append(d['total'])
            
            for k in all_kpis:
                bed_averages[k['beds']]['derivaciones'].append(k['derivaciones_total'])
                bed_averages[k['beds']]['porcentaje_derivacion'].append(k['porcentaje_derivacion'])
            
            # Calculate averages with outlier detection and smoothing
            avg_data = []
            for beds in sorted(bed_averages.keys()):
                data = bed_averages[beds]
                if data['costs'] and data['derivaciones']:
                    # Check if we have enough data points (ideally 3 hospitals)
                    n_hospitals = len(data['costs'])
                    
                    # Calculate basic averages
                    social_avg = np.mean(data['costs'])
                    operational_avg = np.mean(data['operational'])
                    total_avg = np.mean(data['total'])
                    derivaciones_avg = np.mean(data['derivaciones'])
                    porcentaje_derivacion_avg = np.mean(data['porcentaje_derivacion'])
                    
                    # Apply smoothing if we have fewer than 3 data points
                    if n_hospitals < 3 and len(avg_data) >= 2:
                        # Use linear interpolation from adjacent points to smooth anomalies
                        prev_point = avg_data[-1]
                        prev_prev_point = avg_data[-2] if len(avg_data) >= 2 else None
                        
                        if prev_prev_point:
                            # Check if current values are outliers compared to trend
                            trend_total = prev_point['total_avg'] - (prev_point['total_avg'] - prev_prev_point['total_avg'])
                            
                            # If current average deviates more than 20% from trend, apply smoothing
                            if abs(total_avg - trend_total) / trend_total > 0.2:
                                print(f"      🔧 Aplicando suavizado para {unit_type} cama +{beds} (n_hospitales={n_hospitals})")
                                # Smooth using weighted average with trend
                                weight_current = 0.7  # Give some weight to actual data
                                weight_trend = 0.3    # Use trend for smoothing
                                
                                total_avg = weight_current * total_avg + weight_trend * trend_total
                                social_avg = weight_current * social_avg + weight_trend * (trend_total - operational_avg)
                    
                    avg_data.append({
                        'beds': beds,
                        'social_avg': social_avg,
                        'operational_avg': operational_avg,
                        'total_avg': total_avg,
                        'derivaciones_avg': derivaciones_avg,
                        'porcentaje_derivacion_avg': porcentaje_derivacion_avg,
                        'n_hospitals': n_hospitals
                    })
            
            if len(avg_data) < 2:
                print(f"  Datos insuficientes para {unit_type}")
                continue
            
            # Calculate marginal analysis for averages
            marginal_avg = []
            for i in range(1, len(avg_data)):
                prev = avg_data[i-1]
                curr = avg_data[i]
                
                bed_increment = curr['beds'] - prev['beds']
                
                # Calculate marginal benefits (cost reduction) - TOTAL benefits for the increment
                marginal_social_total = prev['social_avg'] - curr['social_avg']
                marginal_operational_total = prev['operational_avg'] - curr['operational_avg']
                marginal_total_total = prev['total_avg'] - curr['total_avg']
                
                # Calculate marginal benefits PER CAMA (dividing by actual bed increment)
                marginal_social_per_bed = marginal_social_total / bed_increment if bed_increment > 0 else 0
                marginal_operational_per_bed = marginal_operational_total / bed_increment if bed_increment > 0 else 0
                marginal_total_per_bed = marginal_total_total / bed_increment if bed_increment > 0 else 0
                
                # Calculate NPV per bed
                npv_operational_per_bed = marginal_operational_per_bed / self.daily_discount_rate if self.daily_discount_rate > 0 else 0
                npv_total_per_bed = marginal_total_per_bed / self.daily_discount_rate if self.daily_discount_rate > 0 else 0
                
                marginal_avg.append({
                    'bed_number': curr['beds'],
                    'bed_increment': bed_increment,
                    'marginal_operational_total': marginal_operational_total,
                    'marginal_total_total': marginal_total_total,
                    'marginal_operational_per_bed': marginal_operational_per_bed,
                    'marginal_total_per_bed': marginal_total_per_bed,
                    'npv_operational_per_bed': npv_operational_per_bed,
                    'npv_total_per_bed': npv_total_per_bed,
                    'porcentaje_derivacion': curr['porcentaje_derivacion_avg']
                })
            
            # Detect and correct outliers
            marginal_avg = self.apply_outlier_smoothing(marginal_avg, unit_type)
            
            # Create plot
            self.create_unit_type_average_plot(unit_type, avg_data, marginal_avg)
    
    def apply_outlier_smoothing(self, marginal_data: List[Dict], unit_type: str) -> List[Dict]:
        """
        Apply advanced statistical smoothing to detect and correct outliers in marginal benefit data.
        Uses multiple methods for better detection of anomalies.
        
        Args:
            marginal_data: List of marginal benefit calculations
            unit_type: Type of unit (ICU, OR, SDU_WARD)
            
        Returns:
            Smoothed marginal data
        """
        if len(marginal_data) < 4:
            return marginal_data
        
        # Extract marginal benefits per bed
        marginal_benefits = [m['marginal_total_per_bed'] for m in marginal_data]
        bed_numbers = [m['bed_number'] for m in marginal_data]
        
        # Method 1: IQR-based outlier detection (standard)
        q1 = np.percentile(marginal_benefits, 25)
        q3 = np.percentile(marginal_benefits, 75)
        iqr = q3 - q1
        iqr_lower = q1 - 1.5 * iqr
        iqr_upper = q3 + 1.5 * iqr
        
        # Method 2: Z-score outlier detection (more sensitive)
        mean_benefit = np.mean(marginal_benefits)
        std_benefit = np.std(marginal_benefits)
        z_threshold = 2.0  # More sensitive than usual 2.5 or 3.0
        
        # Method 3: Local deviation detection (for spikes)
        local_outliers = []
        for i in range(1, len(marginal_benefits) - 1):
            prev_val = marginal_benefits[i-1]
            curr_val = marginal_benefits[i]
            next_val = marginal_benefits[i+1]
            
            # Check if current value is significantly different from neighbors
            expected_val = (prev_val + next_val) / 2
            deviation = abs(curr_val - expected_val)
            local_std = np.std([prev_val, curr_val, next_val])
            
            # If deviation is > 2 times local std, it's a local outlier
            if local_std > 0 and deviation > 2 * local_std:
                # Additional check: must also be significantly higher than expected
                if curr_val > expected_val + local_std:
                    local_outliers.append(i)
        
        # Identify outliers using combined methods
        outlier_indices = []
        
        for i, benefit in enumerate(marginal_benefits):
            is_outlier = False
            reasons = []
            
            # IQR method
            if benefit < iqr_lower or benefit > iqr_upper:
                is_outlier = True
                reasons.append("IQR")
            
            # Z-score method
            if std_benefit > 0:
                z_score = abs(benefit - mean_benefit) / std_benefit
                if z_score > z_threshold:
                    is_outlier = True
                    reasons.append(f"Z-score({z_score:.1f})")
            
            # Local spike detection
            if i in local_outliers:
                is_outlier = True
                reasons.append("Spike")
            
            if is_outlier:
                outlier_indices.append(i)
                reason_str = "+".join(reasons)
                print(f"      🚨 Outlier detectado en {unit_type} cama +{bed_numbers[i]}: ${benefit:.0f}/cama [{reason_str}]")
        
        # Apply smoothing to outliers
        smoothed_data = marginal_data.copy()
        
        for i in outlier_indices:
            original_benefit = marginal_benefits[i]
            
            # Choose smoothing method based on position and context
            if i == 0:
                # First point: use trend from next two points
                if len(marginal_benefits) >= 3:
                    trend = marginal_benefits[2] - marginal_benefits[1]
                    smoothed_benefit = marginal_benefits[1] + trend
                else:
                    smoothed_benefit = marginal_benefits[1]
                    
            elif i == len(marginal_benefits) - 1:
                # Last point: use trend from previous two points
                if len(marginal_benefits) >= 3:
                    trend = marginal_benefits[-2] - marginal_benefits[-3]
                    smoothed_benefit = marginal_benefits[-2] + trend
                else:
                    smoothed_benefit = marginal_benefits[-2]
                    
            else:
                # Middle point: use weighted interpolation with trend consideration
                prev_val = marginal_benefits[i-1]
                next_val = marginal_benefits[i+1]
                
                # Simple interpolation
                simple_interp = (prev_val + next_val) / 2
                
                # Trend-based estimation
                if i >= 2:
                    trend = (marginal_benefits[i-1] - marginal_benefits[i-2])
                    trend_estimate = prev_val + trend
                else:
                    trend_estimate = simple_interp
                
                # Weighted combination (favor interpolation for stability)
                smoothed_benefit = 0.7 * simple_interp + 0.3 * trend_estimate
            
            # Ensure smoothed value is reasonable (not negative for benefits)
            if smoothed_benefit < 0 and original_benefit >= 0:
                smoothed_benefit = max(0, np.mean([prev_val, next_val]) if i > 0 and i < len(marginal_benefits)-1 else 0)
            
            print(f"      🔧 Corrigiendo {unit_type} cama +{bed_numbers[i]}: ${original_benefit:.0f} → ${smoothed_benefit:.0f}/cama")
            
            # Update all related values proportionally
            ratio = smoothed_benefit / original_benefit if original_benefit != 0 else 1
            
            smoothed_data[i]['marginal_total_per_bed'] = smoothed_benefit
            smoothed_data[i]['marginal_operational_per_bed'] *= ratio
            smoothed_data[i]['npv_total_per_bed'] = smoothed_benefit / self.daily_discount_rate if self.daily_discount_rate > 0 else 0
            smoothed_data[i]['npv_operational_per_bed'] = smoothed_data[i]['marginal_operational_per_bed'] / self.daily_discount_rate if self.daily_discount_rate > 0 else 0
        
        return smoothed_data

    def create_unit_type_average_plot(self, unit_type: str, avg_data: List[Dict], marginal_avg: List[Dict]):
        """Create average plot for a specific unit type"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        beds = [d['beds'] for d in avg_data]
        social_costs = [d['social_avg'] for d in avg_data]
        operational_costs = [d['operational_avg'] for d in avg_data]
        total_costs = [d['total_avg'] for d in avg_data]
        derivacion_pct = [d['porcentaje_derivacion_avg'] for d in avg_data]
        
        # Plot 1: Cost Evolution
        ax1.plot(beds, social_costs, 'o-', label='Costo Social', linewidth=2, markersize=6)
        ax1.plot(beds, operational_costs, 's-', label='Costo Operativo', linewidth=2, markersize=6)
        ax1.plot(beds, total_costs, '^-', label='Costo Total', linewidth=2, markersize=6)
        ax1.set_xlabel('Incremento de Camas')
        ax1.set_ylabel('Costo Diario Promedio (USD)')
        ax1.set_title(f'Evolución de Costos - {unit_type} (Promedio 3 Hospitales)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Marginal Benefits per bed
        if marginal_avg:
            marginal_beds = [m['bed_number'] for m in marginal_avg]
            marginal_operational_per_bed = [m['marginal_operational_per_bed'] for m in marginal_avg]
            marginal_total_per_bed = [m['marginal_total_per_bed'] for m in marginal_avg]
            bed_increments = [m['bed_increment'] for m in marginal_avg]
            
            # Plot lines instead of bars
            ax2.plot(marginal_beds, marginal_operational_per_bed, 'o-', 
                    label='Beneficio Operativo/Cama', linewidth=2, markersize=6)
            ax2.plot(marginal_beds, marginal_total_per_bed, 's-', 
                    label='Beneficio Total/Cama', linewidth=2, markersize=6)
            ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax2.set_xlabel('Incremento de Camas')
            ax2.set_ylabel('Beneficio Marginal por Cama (USD/día)')
            ax2.set_title(f'Beneficio Marginal por Cama - {unit_type}')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Add annotations for bed increments where they are not 1
            for i, (bed, increment) in enumerate(zip(marginal_beds, bed_increments)):
                if increment > 1:
                    ax2.annotate(f'Δ{increment}', xy=(bed, marginal_total_per_bed[i]), 
                               xytext=(5, 5), textcoords='offset points', fontsize=8,
                               bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.7))
        
        # Plot 3: NPV Analysis per bed
        if marginal_avg:
            npv_operational_per_bed = [m['npv_operational_per_bed'] for m in marginal_avg]
            npv_total_per_bed = [m['npv_total_per_bed'] for m in marginal_avg]
            
            # Plot lines instead of bars
            ax3.plot(marginal_beds, npv_operational_per_bed, 'o-', 
                    label='VAN Operativo/Cama', linewidth=2, markersize=6)
            ax3.plot(marginal_beds, npv_total_per_bed, 's-', 
                    label='VAN Total/Cama', linewidth=2, markersize=6)
            ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax3.set_xlabel('Incremento de Camas')
            ax3.set_ylabel('VAN por Cama (USD)')
            ax3.set_title(f'Valor Actual Neto por Cama - {unit_type}')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # Plot 4: Derivation Percentage
        ax4.plot(beds, derivacion_pct, 'ro-', linewidth=2, markersize=6)
        ax4.set_xlabel('Incremento de Camas')
        ax4.set_ylabel('Porcentaje de Derivación (%)')
        ax4.set_title(f'Evolución del Porcentaje de Derivación - {unit_type}')
        ax4.grid(True, alpha=0.3)
        
        # Remove summary statistics box for cleaner look
        
        plt.tight_layout()
        
        filename = f'promedio_analisis_{unit_type}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Gráfico promedio generado: {filename}")

def main():
    """Main execution function"""
    # Initialize analyzer with 1% discount rate
    analyzer = HospitalCapacityAnalyzer(discount_rate=(100/99-1))
    
    # Run complete analysis
    analyzer.analyze_all_units()

if __name__ == "__main__":
    main()
