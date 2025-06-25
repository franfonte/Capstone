import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict

class KPIDerivationAnalyzer:
    def __init__(self):
        """Analyzer specifically for derivation KPIs"""
        self.base_path = "resultados_var_camas"
        
        # Define all combinations to analyze
        self.units = [
            ("H1", "ICU"), ("H1", "OR"), ("H1", "SDU_WARD"),
            ("H2", "ICU"), ("H2", "OR"), ("H2", "SDU_WARD"),
            ("H3", "ICU"), ("H3", "OR"), ("H3", "SDU_WARD")
        ]
    
    def extract_value(self, value_str: str) -> float:
        """Extract numerical value from string like '2948.57 ± 26.93'"""
        return float(value_str.split(' ± ')[0])
    
    def load_kpi_data(self, hospital: str, unit: str) -> List[Dict]:
        """Load comprehensive KPI data for a specific hospital/unit combination"""
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
                
                # Extract comprehensive KPI data
                costs = json_data['costo_diario_promedio']['General']
                entrada_salida = json_data['tasa_entrada_vs_salida']
                
                # Extract derivation data
                derivaciones_wl = self.extract_value(costs['derivaciones_wl'])
                derivaciones_ed = self.extract_value(costs['derivaciones_ed'])
                total_entradas = self.extract_value(entrada_salida['total_entradas_por_ciclo'])
                
                # Calculate additional KPIs
                derivaciones_total = derivaciones_wl + derivaciones_ed
                
                # Calculate rates (daily basis)
                entradas_diarias = total_entradas * 365  # Convert cycle to daily
                porcentaje_derivacion_wl = (derivaciones_wl / entradas_diarias) * 100 if entradas_diarias > 0 else 0
                porcentaje_derivacion_ed = (derivaciones_ed / entradas_diarias) * 100 if entradas_diarias > 0 else 0
                porcentaje_derivacion_total = (derivaciones_total / entradas_diarias) * 100 if entradas_diarias > 0 else 0
                
                # Extract costs
                social_cost = self.extract_value(costs['social'])
                operational_cost = self.extract_value(costs['operativo'])
                total_cost = self.extract_value(costs['total'])
                
                # Extract traslados (transfers)
                traslados = self.extract_value(costs['traslados'])
                
                data.append({
                    'beds': i,
                    'derivaciones_wl': derivaciones_wl,
                    'derivaciones_ed': derivaciones_ed,
                    'derivaciones_total': derivaciones_total,
                    'entradas_diarias': entradas_diarias,
                    'porcentaje_derivacion_wl': porcentaje_derivacion_wl,
                    'porcentaje_derivacion_ed': porcentaje_derivacion_ed,
                    'porcentaje_derivacion_total': porcentaje_derivacion_total,
                    'social_cost': social_cost,
                    'operational_cost': operational_cost,
                    'total_cost': total_cost,
                    'traslados': traslados,
                    'costo_por_derivacion': total_cost / derivaciones_total if derivaciones_total > 0 else 0
                })
                
            except Exception as e:
                print(f"Error processing KPIs from {file_path}: {e}")
        
        return data
    
    def analyze_all_kpis(self):
        """Analyze KPIs for all units"""
        print("=== ANÁLISIS DETALLADO DE KPIs DE DERIVACIÓN ===")
        
        all_results = {}
        summary_data = []
        
        for hospital, unit in self.units:
            print(f"\nProcesando {hospital} {unit}...")
            
            data = self.load_kpi_data(hospital, unit)
            if not data:
                print(f"  No se encontraron datos para {hospital} {unit}")
                continue
            
            # Calculate metrics
            base_derivation = data[0]['porcentaje_derivacion_total']
            min_derivation = min(d['porcentaje_derivacion_total'] for d in data)
            max_reduction = base_derivation - min_derivation
            optimal_beds = next((d['beds'] for d in data if d['porcentaje_derivacion_total'] == min_derivation), 0)
            
            # Calculate cost efficiency
            cost_per_reduction = []
            for d in data[1:]:
                reduction = base_derivation - d['porcentaje_derivacion_total']
                if reduction > 0:
                    cost_per_point = (d['total_cost'] - data[0]['total_cost']) / reduction
                    cost_per_reduction.append(cost_per_point)
            
            avg_cost_per_point = np.mean(cost_per_reduction) if cost_per_reduction else 0
            
            all_results[f"{hospital}_{unit}"] = data
            
            summary_data.append({
                'Hospital': hospital,
                'Unidad': unit,
                'Derivacion_Base_%': base_derivation,
                'Derivacion_Minima_%': min_derivation,
                'Reduccion_Maxima_puntos': max_reduction,
                'Camas_Optimas_Derivacion': optimal_beds,
                'Costo_Promedio_por_Punto_Reduccion': avg_cost_per_point,
                'Derivaciones_Base_Diarias': data[0]['derivaciones_total'],
                'Derivaciones_Min_Diarias': min((d['derivaciones_total'] for d in data), default=0)
            })
            
            print(f"  ✓ Base: {base_derivation:.1f}% → Mín: {min_derivation:.1f}% (Reducción: {max_reduction:.1f} puntos)")
        
        # Create comprehensive analysis
        self.create_comprehensive_kpi_analysis(all_results, summary_data)
        
        # Create summary table
        df = pd.DataFrame(summary_data)
        df.to_csv('analisis_kpis_derivacion.csv', index=False)
        
        print(f"\n=== ANÁLISIS KPIs COMPLETADO ===")
        print("Archivos generados:")
        print("  - analisis_kpis_derivacion.csv")
        print("  - kpis_derivacion_por_unidad.png")
        print("  - comparativo_reduccion_derivacion.png")
    
    def create_comprehensive_kpi_analysis(self, all_results: Dict, summary_data: List[Dict]):
        """Create comprehensive KPI analysis plots"""
        
        # Create individual plots for each unit
        self.create_unit_kpi_plots(all_results)
        
        # Create comparative analysis
        self.create_comparative_analysis(summary_data)
    
    def create_unit_kpi_plots(self, all_results: Dict):
        """Create detailed KPI plots for each unit"""
        
        fig, axes = plt.subplots(3, 3, figsize=(20, 15))
        axes = axes.flatten()
        
        unit_names = {
            'ICU': 'Unidad de Cuidados Intensivos',
            'OR': 'Quirófanos',
            'SDU_WARD': 'Salas Generales'
        }
        
        for idx, (key, data) in enumerate(all_results.items()):
            if idx >= 9:
                break
                
            hospital, unit = key.split('_', 1)
            ax = axes[idx]
            
            beds = [d['beds'] for d in data]
            derivacion_total = [d['porcentaje_derivacion_total'] for d in data]
            derivacion_wl = [d['porcentaje_derivacion_wl'] for d in data]
            derivacion_ed = [d['porcentaje_derivacion_ed'] for d in data]
            
            # Plot derivation percentages
            ax.plot(beds, derivacion_total, 'o-', label='Total', linewidth=2, markersize=4)
            ax.plot(beds, derivacion_wl, 's-', label='Lista Espera', linewidth=1.5, markersize=3, alpha=0.7)
            ax.plot(beds, derivacion_ed, '^-', label='Emergencia', linewidth=1.5, markersize=3, alpha=0.7)
            
            ax.set_xlabel('Incremento de Camas')
            ax.set_ylabel('% Derivación')
            ax.set_title(f'{hospital} - {unit_names.get(unit, unit)}')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            
            # Add reduction annotation
            base_pct = derivacion_total[0]
            min_pct = min(derivacion_total)
            reduction = base_pct - min_pct
            
            ax.annotate(f'Reducción: {reduction:.1f}pp',
                       xy=(0.02, 0.98), xycoords='axes fraction',
                       fontsize=8, verticalalignment='top',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        plt.tight_layout()
        plt.savefig('kpis_derivacion_por_unidad.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_comparative_analysis(self, summary_data: List[Dict]):
        """Create comparative analysis across units"""
        
        df = pd.DataFrame(summary_data)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Reduction potential by unit type
        unit_types = ['ICU', 'OR', 'SDU_WARD']
        colors = ['lightblue', 'lightgreen', 'lightcoral']
        
        for i, unit_type in enumerate(unit_types):
            unit_data = df[df['Unidad'] == unit_type]
            hospitals = unit_data['Hospital']
            reductions = unit_data['Reduccion_Maxima_puntos']
            
            ax1.bar([f"{h}_{unit_type}" for h in hospitals], reductions, 
                   color=colors[i], alpha=0.7, label=unit_type)
        
        ax1.set_ylabel('Reducción Máxima (puntos porcentuales)')
        ax1.set_title('Potencial de Reducción de Derivación por Unidad')
        ax1.legend()
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Cost efficiency (cost per percentage point reduction)
        for i, unit_type in enumerate(unit_types):
            unit_data = df[df['Unidad'] == unit_type]
            hospitals = unit_data['Hospital']
            costs = unit_data['Costo_Promedio_por_Punto_Reduccion']
            
            ax2.bar([f"{h}_{unit_type}" for h in hospitals], costs, 
                   color=colors[i], alpha=0.7, label=unit_type)
        
        ax2.set_ylabel('Costo por Punto de Reducción (USD/día)')
        ax2.set_title('Costo-Efectividad de Reducción de Derivación')
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Base vs minimum derivation rates
        x = np.arange(len(df))
        width = 0.35
        
        ax3.bar(x - width/2, df['Derivacion_Base_%'], width, label='Base', alpha=0.7)
        ax3.bar(x + width/2, df['Derivacion_Minima_%'], width, label='Mínima', alpha=0.7)
        
        ax3.set_ylabel('Porcentaje de Derivación (%)')
        ax3.set_title('Derivación Base vs Mínima por Unidad')
        ax3.set_xticks(x)
        ax3.set_xticklabels([f"{row['Hospital']}_{row['Unidad']}" for _, row in df.iterrows()], rotation=45)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Optimal beds for derivation reduction
        unit_groups = df.groupby('Unidad')
        
        for unit_type, group in unit_groups:
            ax4.scatter(group['Camas_Optimas_Derivacion'], group['Reduccion_Maxima_puntos'], 
                       s=100, alpha=0.7, label=unit_type)
        
        ax4.set_xlabel('Camas Óptimas para Reducir Derivación')
        ax4.set_ylabel('Reducción Máxima (puntos porcentuales)')
        ax4.set_title('Relación: Camas Óptimas vs Reducción Conseguida')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Add summary statistics
        avg_reduction = df['Reduccion_Maxima_puntos'].mean()
        best_unit = df.loc[df['Reduccion_Maxima_puntos'].idxmax()]
        
        stats_text = f"""RESUMEN ESTADÍSTICO DE DERIVACIÓN
Reducción promedio: {avg_reduction:.1f} puntos porcentuales
Mejor unidad: {best_unit['Hospital']} {best_unit['Unidad']} ({best_unit['Reduccion_Maxima_puntos']:.1f}pp)
Rango de reducción: {df['Reduccion_Maxima_puntos'].min():.1f} - {df['Reduccion_Maxima_puntos'].max():.1f}pp
Camas promedio necesarias: {df['Camas_Optimas_Derivacion'].mean():.0f}"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=9,
                verticalalignment='bottom', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        plt.savefig('comparativo_reduccion_derivacion.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main execution function"""
    analyzer = KPIDerivationAnalyzer()
    analyzer.analyze_all_kpis()

if __name__ == "__main__":
    main()
