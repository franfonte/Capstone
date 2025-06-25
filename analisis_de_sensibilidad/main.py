import json
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

def extract_cost_value(cost_str):
    """Extract the numerical value from a cost string like '187.55 ± 5.92'"""
    return float(cost_str.split(' ± ')[0])

def load_h1_icu_costs():
    """Load cost data for H1 ICU from all increment files"""
    base_path = "/home/yoga/Capstone/analisis_de_sensibilidad/resultados_var_camas/ModeloProactivo_T4500_C4208_H1_ICU"
    
    increments = []
    social_costs = []
    operational_costs = []
    total_costs = []
    
    # Process files +1.json to +27.json
    for i in range(1, 28):
        file_path = os.path.join(base_path, f"+{i}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract costs from the General section
                costs = data['costo_diario_promedio']['General']
                
                increments.append(i)
                social_costs.append(extract_cost_value(costs['social']))
                operational_costs.append(extract_cost_value(costs['operativo']))
                total_costs.append(extract_cost_value(costs['total']))
                
                print(f"Camas +{i}: Social={social_costs[-1]:.2f}, Operativo={operational_costs[-1]:.2f}, Total={total_costs[-1]:.2f}")
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    return increments, social_costs, operational_costs, total_costs

def calculate_marginal_benefits(social_costs, operational_costs, total_costs):
    """Calculate marginal benefits (cost reductions) for each additional bed"""
    marginal_social = []
    marginal_operational = []
    marginal_total = []
    
    for i in range(1, len(social_costs)):
        # Marginal benefit = previous cost - current cost (positive = benefit, negative = additional cost)
        marginal_social.append(social_costs[i-1] - social_costs[i])
        marginal_operational.append(operational_costs[i-1] - operational_costs[i])
        marginal_total.append(total_costs[i-1] - total_costs[i])
    
    return marginal_social, marginal_operational, marginal_total

def plot_cost_evolution():
    """Plot the evolution of costs as beds are added to H1 ICU"""
    increments, social_costs, operational_costs, total_costs = load_h1_icu_costs()
    
    if not increments:
        print("No data found!")
        return
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
    
    # Plot 1: Cost Evolution
    ax1.plot(increments, social_costs, 'ro-', linewidth=2, markersize=6, label='Costo Social')
    ax1.plot(increments, operational_costs, 'bo-', linewidth=2, markersize=6, label='Costo Operativo')
    ax1.plot(increments, total_costs, 'go-', linewidth=2, markersize=6, label='Costo Total')
    
    ax1.set_xlabel('Camas Adicionales en H1 ICU', fontsize=12)
    ax1.set_ylabel('Costo Diario Promedio', fontsize=12)
    ax1.set_title('Evolución de Costos al Agregar Camas en H1 ICU', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(range(1, max(increments) + 1, 2))
    
    # Plot 2: Marginal Benefits
    if len(increments) > 1:
        marginal_social, marginal_operational, marginal_total = calculate_marginal_benefits(
            social_costs, operational_costs, total_costs
        )
        
        # X-axis for marginal benefits (from bed 2 to N)
        marginal_increments = increments[1:]
        
        ax2.plot(marginal_increments, marginal_social, 'ro-', linewidth=2, markersize=6, label='Beneficio Marginal Social')
        ax2.plot(marginal_increments, marginal_operational, 'bo-', linewidth=2, markersize=6, label='Beneficio Marginal Operativo')
        ax2.plot(marginal_increments, marginal_total, 'go-', linewidth=2, markersize=6, label='Beneficio Marginal Total')
        
        # Add horizontal line at y=0
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        ax2.set_xlabel('Cama Adicional #', fontsize=12)
        ax2.set_ylabel('Beneficio Marginal (Reducción de Costo)', fontsize=12)
        ax2.set_title('Beneficio Marginal de Agregar Cada Cama Adicional', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(range(2, max(increments) + 1, 2))
    
    plt.tight_layout()
    
    # Save the plot
    output_path = "/home/yoga/Capstone/analisis_de_sensibilidad/evolucion_costos_h1_icu.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nGráfico guardado en: {output_path}")
    
    # Print analysis
    print("\n=== ANÁLISIS DE EVOLUCIÓN DE COSTOS ===")
    print(f"Rango analizado: +{min(increments)} a +{max(increments)} camas")
    print(f"Costo social inicial (+1): {social_costs[0]:.2f}")
    print(f"Costo social final (+{max(increments)}): {social_costs[-1]:.2f}")
    print(f"Cambio total en costo social: {social_costs[-1] - social_costs[0]:.2f}")
    
    print(f"\nCosto operativo inicial (+1): {operational_costs[0]:.2f}")
    print(f"Costo operativo final (+{max(increments)}): {operational_costs[-1]:.2f}")
    print(f"Cambio total en costo operativo: {operational_costs[-1] - operational_costs[0]:.2f}")
    
    # Marginal analysis
    if len(increments) > 1:
        print("\n=== ANÁLISIS MARGINAL ===")
        
        # Find where marginal benefits become negative
        positive_marginal_total = [i for i, mb in enumerate(marginal_total) if mb > 0]
        if positive_marginal_total:
            last_positive = marginal_increments[positive_marginal_total[-1]]
            print(f"Última cama con beneficio marginal positivo: +{last_positive}")
        
        # Find where operational marginal benefit becomes negative
        positive_marginal_op = [i for i, mb in enumerate(marginal_operational) if mb > 0]
        if positive_marginal_op:
            last_positive_op = marginal_increments[positive_marginal_op[-1]]
            print(f"Última cama con beneficio marginal operativo positivo: +{last_positive_op}")
        
        # Show top 5 marginal benefits
        print(f"\nTop 5 beneficios marginales totales:")
        marginal_with_beds = list(zip(marginal_increments, marginal_total))
        marginal_with_beds.sort(key=lambda x: x[1], reverse=True)
        for i, (bed_num, benefit) in enumerate(marginal_with_beds[:5]):
            print(f"  {i+1}. Cama +{bed_num}: {benefit:.2f} reducción de costo")
    
    # Find optimal point
    min_total_cost = min(total_costs)
    min_total_index = total_costs.index(min_total_cost)
    optimal_beds = increments[min_total_index]
    
    print(f"\nCosto total mínimo: {min_total_cost:.2f} con +{optimal_beds} camas")
    print(f"Recomendación: Agregar {optimal_beds} camas para minimizar costo total")

if __name__ == "__main__":
    print("=== INICIANDO ANÁLISIS DE COSTOS H1 ICU ===")
    print("Cargando datos...")
    try:
        plot_cost_evolution()
        print("=== ANÁLISIS COMPLETADO ===")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
