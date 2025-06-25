import json
import os
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple

class CorrelationAnalyzer:
    def __init__(self):
        """Analyzer for correlation between derivation percentage and total costs"""
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
    
    def load_correlation_data(self, hospital: str, unit: str) -> List[Dict]:
        """Load data for correlation analysis"""
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
                
                # Extract data
                costs = json_data['costo_diario_promedio']['General']
                entrada_salida = json_data['tasa_entrada_vs_salida']
                
                # Calculate derivation data
                derivaciones_wl = self.extract_value(costs['derivaciones_wl'])
                derivaciones_ed = self.extract_value(costs['derivaciones_ed'])
                total_entradas = self.extract_value(entrada_salida['total_entradas_por_ciclo'])
                
                # Calculate percentages and costs
                derivaciones_total = derivaciones_wl + derivaciones_ed
                entradas_diarias = total_entradas * 365
                porcentaje_derivacion = (derivaciones_total / entradas_diarias) * 100 if entradas_diarias > 0 else 0
                
                # Extract costs
                social_cost = self.extract_value(costs['social'])
                operational_cost = self.extract_value(costs['operativo'])
                total_cost = self.extract_value(costs['total'])
                derivation_cost = derivaciones_total  # Daily derivations as cost proxy
                
                data.append({
                    'hospital': hospital,
                    'unit': unit,
                    'beds': i,
                    'porcentaje_derivacion': porcentaje_derivacion,
                    'derivaciones_diarias': derivaciones_total,
                    'social_cost': social_cost,
                    'operational_cost': operational_cost,
                    'total_cost': total_cost,
                    'entradas_diarias': entradas_diarias
                })
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return data
    
    def analyze_correlations(self):
        """Analyze correlations between derivation percentage and costs"""
        print("=== ANÁLISIS DE CORRELACIÓN: DERIVACIÓN vs COSTOS ===")
        
        # Collect all data
        all_data = []
        unit_data = {}
        
        for hospital, unit in self.units:
            print(f"\nCargando datos {hospital} {unit}...")
            
            data = self.load_correlation_data(hospital, unit)
            if data:
                all_data.extend(data)
                unit_key = f"{hospital}_{unit}"
                unit_data[unit_key] = data
                print(f"  ✓ {len(data)} puntos de datos cargados")
            else:
                print(f"  ✗ No se encontraron datos")
        
        if not all_data:
            print("No hay datos suficientes para el análisis")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        # Calculate overall correlations
        self.calculate_overall_correlations(df)
        
        # Calculate correlations by unit type
        self.calculate_unit_type_correlations(df)
        
        # Create visualizations
        self.create_correlation_plots(df)
        
        # Generate detailed analysis
        self.generate_correlation_report(df, unit_data)
    
    def calculate_overall_correlations(self, df: pd.DataFrame):
        """Calculate overall correlation statistics"""
        print("\n=== CORRELACIONES GENERALES ===")
        
        # Pearson correlations
        corr_total_pearson, p_total_pearson = pearsonr(df['porcentaje_derivacion'], df['total_cost'])
        corr_social_pearson, p_social_pearson = pearsonr(df['porcentaje_derivacion'], df['social_cost'])
        corr_operational_pearson, p_operational_pearson = pearsonr(df['porcentaje_derivacion'], df['operational_cost'])
        
        # Spearman correlations (rank-based, more robust)
        corr_total_spearman, p_total_spearman = spearmanr(df['porcentaje_derivacion'], df['total_cost'])
        corr_social_spearman, p_social_spearman = spearmanr(df['porcentaje_derivacion'], df['social_cost'])
        corr_operational_spearman, p_operational_spearman = spearmanr(df['porcentaje_derivacion'], df['operational_cost'])
        
        print(f"\n**CORRELACIÓN PEARSON (lineal):**")
        print(f"Derivación vs Costo Total:      r = {corr_total_pearson:.4f}, p = {p_total_pearson:.2e}")
        print(f"Derivación vs Costo Social:     r = {corr_social_pearson:.4f}, p = {p_social_pearson:.2e}")
        print(f"Derivación vs Costo Operativo:  r = {corr_operational_pearson:.4f}, p = {p_operational_pearson:.2e}")
        
        print(f"\n**CORRELACIÓN SPEARMAN (monotónica):**")
        print(f"Derivación vs Costo Total:      ρ = {corr_total_spearman:.4f}, p = {p_total_spearman:.2e}")
        print(f"Derivación vs Costo Social:     ρ = {corr_social_spearman:.4f}, p = {p_social_spearman:.2e}")
        print(f"Derivación vs Costo Operativo:  ρ = {corr_operational_spearman:.4f}, p = {p_operational_spearman:.2e}")
        
        # Store results for later use
        self.overall_correlations = {
            'total_pearson': corr_total_pearson,
            'social_pearson': corr_social_pearson,
            'operational_pearson': corr_operational_pearson,
            'total_spearman': corr_total_spearman,
            'social_spearman': corr_social_spearman,
            'operational_spearman': corr_operational_spearman
        }
    
    def calculate_unit_type_correlations(self, df: pd.DataFrame):
        """Calculate correlations by unit type"""
        print("\n=== CORRELACIONES POR TIPO DE UNIDAD ===")
        
        unit_types = ['ICU', 'OR', 'SDU_WARD']
        self.unit_correlations = {}
        
        for unit_type in unit_types:
            unit_df = df[df['unit'] == unit_type]
            
            if len(unit_df) < 3:  # Need at least 3 points for correlation
                continue
            
            corr_total, p_total = pearsonr(unit_df['porcentaje_derivacion'], unit_df['total_cost'])
            corr_social, p_social = pearsonr(unit_df['porcentaje_derivacion'], unit_df['social_cost'])
            
            print(f"\n**{unit_type}:**")
            print(f"  Derivación vs Costo Total:  r = {corr_total:.4f}, p = {p_total:.3f}")
            print(f"  Derivación vs Costo Social: r = {corr_social:.4f}, p = {p_social:.3f}")
            print(f"  Puntos de datos: {len(unit_df)}")
            
            self.unit_correlations[unit_type] = {
                'total': corr_total,
                'social': corr_social,
                'n_points': len(unit_df)
            }
    
    def create_correlation_plots(self, df: pd.DataFrame):
        """Create correlation visualization plots"""
        print("\n=== GENERANDO GRÁFICOS DE CORRELACIÓN ===")
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Overall correlation - Total Cost
        ax1 = axes[0, 0]
        scatter = ax1.scatter(df['porcentaje_derivacion'], df['total_cost'], 
                            c=df['unit'].astype('category').cat.codes, 
                            alpha=0.7, s=50, cmap='viridis')
        ax1.set_xlabel('Porcentaje de Derivación (%)')
        ax1.set_ylabel('Costo Total Diario (USD)')
        ax1.set_title(f'Correlación: Derivación vs Costo Total\nr = {self.overall_correlations["total_pearson"]:.3f}')
        ax1.grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(df['porcentaje_derivacion'], df['total_cost'], 1)
        p = np.poly1d(z)
        ax1.plot(df['porcentaje_derivacion'], p(df['porcentaje_derivacion']), "r--", alpha=0.8)
        
        # Plot 2: Overall correlation - Social Cost
        ax2 = axes[0, 1]
        ax2.scatter(df['porcentaje_derivacion'], df['social_cost'], 
                   c=df['unit'].astype('category').cat.codes, 
                   alpha=0.7, s=50, cmap='viridis')
        ax2.set_xlabel('Porcentaje de Derivación (%)')
        ax2.set_ylabel('Costo Social Diario (USD)')
        ax2.set_title(f'Correlación: Derivación vs Costo Social\nr = {self.overall_correlations["social_pearson"]:.3f}')
        ax2.grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(df['porcentaje_derivacion'], df['social_cost'], 1)
        p = np.poly1d(z)
        ax2.plot(df['porcentaje_derivacion'], p(df['porcentaje_derivacion']), "r--", alpha=0.8)
        
        # Plot 3: By unit type - Total Cost
        ax3 = axes[1, 0]
        unit_types = ['ICU', 'OR', 'SDU_WARD']
        colors = ['blue', 'green', 'red']
        
        for i, unit_type in enumerate(unit_types):
            unit_df = df[df['unit'] == unit_type]
            if len(unit_df) > 0:
                ax3.scatter(unit_df['porcentaje_derivacion'], unit_df['total_cost'], 
                           c=colors[i], label=unit_type, alpha=0.7, s=50)
        
        ax3.set_xlabel('Porcentaje de Derivación (%)')
        ax3.set_ylabel('Costo Total Diario (USD)')
        ax3.set_title('Correlación por Tipo de Unidad - Costo Total')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Correlation summary
        ax4 = axes[1, 1]
        
        # Create summary table as text
        summary_text = f"""RESUMEN DE CORRELACIONES

CORRELACIÓN GENERAL (Pearson):
• Total:     r = {self.overall_correlations['total_pearson']:.3f}
• Social:    r = {self.overall_correlations['social_pearson']:.3f}
• Operativo: r = {self.overall_correlations['operational_pearson']:.3f}

CORRELACIÓN POR UNIDAD:"""
        
        for unit_type, corrs in self.unit_correlations.items():
            summary_text += f"\n• {unit_type}: r = {corrs['total']:.3f} (n={corrs['n_points']})"
        
        summary_text += f"""

INTERPRETACIÓN:
• r > 0.8: Correlación muy fuerte
• r > 0.6: Correlación fuerte  
• r > 0.4: Correlación moderada
• r > 0.2: Correlación débil

PUNTOS DE DATOS: {len(df)}
UNIDADES ANALIZADAS: {len(df['unit'].unique())}"""
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        
        plt.tight_layout()
        plt.savefig('analisis_correlacion_derivacion_costos.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("  ✓ Gráfico generado: analisis_correlacion_derivacion_costos.png")
    
    def generate_correlation_report(self, df: pd.DataFrame, unit_data: Dict):
        """Generate detailed correlation analysis report"""
        print("\n=== GENERANDO REPORTE DETALLADO ===")
        
        # Calculate R-squared values
        r2_total = self.overall_correlations['total_pearson'] ** 2
        r2_social = self.overall_correlations['social_pearson'] ** 2
        
        # Create detailed analysis
        report_data = []
        
        for unit_key, data in unit_data.items():
            if len(data) < 3:
                continue
                
            unit_df = pd.DataFrame(data)
            
            # Calculate derivation range
            derivation_range = unit_df['porcentaje_derivacion'].max() - unit_df['porcentaje_derivacion'].min()
            cost_range = unit_df['total_cost'].max() - unit_df['total_cost'].min()
            
            # Calculate correlation
            if len(unit_df) >= 3:
                corr_total, p_value = pearsonr(unit_df['porcentaje_derivacion'], unit_df['total_cost'])
                
                report_data.append({
                    'Unidad': unit_key,
                    'Puntos_Datos': len(unit_df),
                    'Derivacion_Min_%': unit_df['porcentaje_derivacion'].min(),
                    'Derivacion_Max_%': unit_df['porcentaje_derivacion'].max(),
                    'Rango_Derivacion': derivation_range,
                    'Costo_Min': unit_df['total_cost'].min(),
                    'Costo_Max': unit_df['total_cost'].max(),
                    'Rango_Costo': cost_range,
                    'Correlacion_r': corr_total,
                    'R_cuadrado': corr_total**2,
                    'P_valor': p_value,
                    'Significativo_95%': 'Sí' if p_value < 0.05 else 'No'
                })
        
        # Save detailed report
        report_df = pd.DataFrame(report_data)
        report_df.to_csv('analisis_correlacion_detallado.csv', index=False)
        
        # Print summary statistics
        print(f"\n**ESTADÍSTICAS GENERALES:**")
        print(f"Correlación Derivación-Costo Total: r = {self.overall_correlations['total_pearson']:.4f}")
        print(f"R² (varianza explicada): {r2_total:.1%}")
        print(f"Correlación Derivación-Costo Social: r = {self.overall_correlations['social_pearson']:.4f}")
        print(f"R² Social (varianza explicada): {r2_social:.1%}")
        
        strong_correlations = sum(1 for _, corrs in self.unit_correlations.items() if abs(corrs['total']) > 0.6)
        print(f"Unidades con correlación fuerte (|r| > 0.6): {strong_correlations}/{len(self.unit_correlations)}")
        
        print(f"\n**ARCHIVOS GENERADOS:**")
        print(f"• analisis_correlacion_derivacion_costos.png")
        print(f"• analisis_correlacion_detallado.csv")
        
        return report_df

def main():
    """Main execution function"""
    analyzer = CorrelationAnalyzer()
    analyzer.analyze_correlations()

if __name__ == "__main__":
    main()
