import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple

class HospitalCapacityAnalyzer:
    def __init__(self, discount_rate: float = 0.01):
        """
        Analyzer for hospital capacity expansion analysis
        
        Args:
            discount_rate: Annual discount rate for NPV calculations (default 5%)
        """
        self.discount_rate = discount_rate
        self.daily_discount_rate = (1 + discount_rate) ** (1/365) - 1
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
            # NPV = Annual_Benefit / annual_discount_rate (perpetuity formula)
            annual_benefit_social = marginal_social * 365
            annual_benefit_operational = marginal_operational * 365
            annual_benefit_total = marginal_total * 365
            
            npv_social = annual_benefit_social / self.discount_rate if self.discount_rate > 0 else 0
            npv_operational = annual_benefit_operational / self.discount_rate if self.discount_rate > 0 else 0
            npv_total = annual_benefit_total / self.discount_rate if self.discount_rate > 0 else 0
            
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
        ax3.set_ylabel('VAN de beneficio marginal diario')
        ax3.set_title(f'VAN por Tipo de Costo (Tasa: {self.discount_rate:.1%})')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Summary Statistics
        ax4.axis('off')
        
        # Calculate additional metrics for operational costs
        max_npv_operational_value = max(npv_operational) if npv_operational else 0
        positive_operational = [m for m in marginal_data if m['marginal_operational'] > 0]
        last_beneficial_operational = positive_operational[-1]['bed_number'] if positive_operational else 0
        cumulative_npv_operational = sum(m['npv_operational'] * m['bed_increment'] for m in marginal_data if m['marginal_operational'] > 0)
        
        # Check for non-unit increments
        non_unit_increments = [m for m in marginal_data if m['bed_increment'] != 1]
        increment_info = f" (Incrementos: {', '.join([str(m['bed_increment']) for m in marginal_data[:5]])}...)" if non_unit_increments else ""
        
        stats_text = f"""
        RESUMEN ECONÓMICO - {hospital} {unit}
        
        ANÁLISIS TOTAL:
        Punto Óptimo: +{analysis['optimal_beds']} camas
        Costo mínimo: ${analysis['min_total_cost']:,.0f}
        VAN máximo total: ${analysis['max_npv_per_bed']:,.0f}
        
        ANÁLISIS OPERATIVO:
        VAN máximo operativo: ${max_npv_operational_value:,.0f}
        Última cama beneficiosa (op): +{last_beneficial_operational}
        VAN acumulado operativo: ${cumulative_npv_operational:,.0f}
        
        ANÁLISIS SOCIAL:
        VAN acumulado social: ${analysis['cumulative_npv'] - cumulative_npv_operational:,.0f}
        
        Tasa de descuento: {self.discount_rate:.1%} anual{increment_info}
        """
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
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
        
        # Store summary data for potential external use
        self.summary_data = summary_data
        
        print(f"\n=== ANÁLISIS COMPLETADO ===")
        print(f"Se analizaron {len(self.results)} unidades")
        print("Archivos generados:")
        for key, result in self.results.items():
            print(f"  - {result['plot_file']}")
        print("  - resumen_analisis_capacidad.png")
        print("  - resumen_analisis_capacidad.csv")
    
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
        
        # Plot 4: Summary table
        ax4.axis('off')
        
        # Create summary statistics
        total_van = df['VAN_Total_Acumulado'].sum()
        total_van_operational = df['VAN_Operativo_Acumulado'].sum()
        total_optimal_beds = df['Camas_Optimas'].sum()
        avg_van_per_bed_total = df['VAN_Maximo_Cama_Total'].mean()
        avg_van_per_bed_operational = df['VAN_Maximo_Cama_Operativo'].mean()
        
        summary_text = f"""
        RESUMEN EJECUTIVO
        
        ANÁLISIS TOTAL:
        VAN total expansión: ${total_van:,.0f}
        VAN promedio por cama: ${avg_van_per_bed_total:,.0f}
        Total camas óptimas: {total_optimal_beds}
        
        ANÁLISIS OPERATIVO:
        VAN operativo expansión: ${total_van_operational:,.0f}
        VAN operativo promedio: ${avg_van_per_bed_operational:,.0f}
        
        RANKING POR VAN OPERATIVO:
        """
        
        # Add ranking by operational NPV
        df_sorted = df.sort_values('VAN_Maximo_Cama_Operativo', ascending=False)
        for i, row in df_sorted.head(5).iterrows():
            summary_text += f"\n{row['Hospital']} {row['Unidad']}: ${row['VAN_Maximo_Cama_Operativo']:,.0f}"
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('resumen_analisis_capacidad.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main execution function"""
    # Initialize analyzer with 1% discount rate
    analyzer = HospitalCapacityAnalyzer(discount_rate=(100/99-1))
    
    # Run complete analysis
    analyzer.analyze_all_units()

if __name__ == "__main__":
    main()
