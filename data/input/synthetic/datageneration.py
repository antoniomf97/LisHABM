"""Functions to generate synthetic data.

"""

from engine.core.agents import Constructor, House, Household, Region, Person, Contracts, Loan
from engine.io.scenario import Scenario
import numpy as np
from uuid import uuid4
import random
import yaml
import json
import pickle
from pathlib import Path
from typing import Literal
import argparse
from pathlib import Path
import sys


# 2. The Dynamic Distribution Helper
def draw_from_dist(dist_config: dict, rng: np.random.Generator) -> float | int:
    """Reads the 'type' from the config and returns a value from the correct distribution."""
    dist_type = dist_config.get("type", "constant")
    
    if dist_type == "constant":
        return dist_config.get("value", 0.0)
        
    elif dist_type == "uniform":
        return rng.uniform(dist_config["min"], dist_config["max"])
        
    elif dist_type == "normal":
        return rng.normal(dist_config["mean"], dist_config["std_dev"])
        
    elif dist_type == "lognormal":
        # numpy's lognormal expects the mean of the underlying normal distribution.
        # Taking np.log() allows the user to write intuitive target means in the YAML.
        target_mean = dist_config["mean"]
        return rng.lognormal(mean=np.log(target_mean), sigma=dist_config["sigma"])
        
    elif dist_type == "poisson":
        return rng.poisson(dist_config["lambda"])
        
    else:
        raise ValueError(f"Unsupported distribution type: '{dist_type}'")



def generate_constructors(const_config: dict, rng: np.random.Generator) -> list[Constructor]:
    constructors = []
    
    for _ in range(const_config["count"]):
        # Dynamically draw values based purely on the config dictionaries
        capital = draw_from_dist(const_config["capital_distribution"], rng)
        size = draw_from_dist(const_config["size_distribution"], rng)
        
        constructors.append(
            Constructor(
                id=uuid4(),
                capital=round(capital, 2), # Rounding for cleaner financial data
                size=round(size, 2)
            )
        )
        
    return constructors

def generate_regions(geo_config: dict, rng: np.random.Generator) -> list[Region]:
    region_data = geo_config["regions"]
    
    # Pass 1: Create all Region objects without their neighbors yet
    # We store them in a dictionary for easy O(1) lookup by name
    region_map: dict[str, Region] = {}
    
    for name in region_data.keys():
        region_map[name] = Region(
            id=uuid4(),
            name=name,
            neighborhood=[] # Will populate in Pass 2
        )
        
    # Pass 2: Link the neighborhoods
    for name, neighbor_names in region_data.items():
        current_region = region_map[name]
        
        for neighbor_name in neighbor_names:
            # Look up the actual Region object for the neighbor
            if neighbor_name in region_map:
                neighbor_region = region_map[neighbor_name]
                current_region.neighborhood.append(neighbor_region)
            else:
                # Optional: Handle typos in the YAML file safely
                print(f"Warning: Neighbor '{neighbor_name}' not found for '{name}'")
                
    # Return the list of fully linked Region objects
    return list(region_map.values())
        

def generate_houses(house_config: dict, regions: list[Region], constructors: list[Constructor], rng: np.random.Generator) -> list[House]:
    houses = []
    total_count = house_config["total_count"]
    
    # 1. Distribute Housing Count Across Regions
    region_names = [r.name for r in regions]
    weights = []
    dist_config = house_config["regional_distribution"]
    
    # Extract weights and fallback to default if not specified
    for name in region_names:
        weights.append(dist_config.get(name, dist_config.get("default_weight", 1.0)))
        
    # Normalize weights to probabilities that sum exactly to 1.0
    probabilities = np.array(weights) / sum(weights)
    
    # Multinomial draws the exact total_count distributed by our probabilities
    counts_per_region = rng.multinomial(total_count, probabilities)
    
    # Zip regions with their assigned housing count
    region_allocations = list(zip(regions, counts_per_region))
    
    # Setup Typology choices
    typologies = list(house_config["typology_weights"].keys())
    typology_probs = list(house_config["typology_weights"].values())
    
    # 2. Generate the Houses Region by Region
    for region, count in region_allocations:
        # Find the correct price config for this region (or fallback to default)
        price_configs = house_config["regional_sqm_price"]
        region_price_config = price_configs.get(region.name, price_configs.get("default_price"))
        
        for _ in range(count):
            typology = rng.choice(typologies, p=typology_probs)
            owner = rng.choice(constructors)
            
            # Draw from flexible distributions
            age = draw_from_dist(house_config["age_distribution"], rng)
            quality = draw_from_dist(house_config["quality_distribution"], rng)
            quality = max(1.0, min(5.0, quality)) # Clamp between 1 and 5
            
            # Draw base sqm price specifically for this region
            base_sqm_price = draw_from_dist(region_price_config, rng)
            
            # Base Areas (correlated to typology)
            base_areas = {"T0": 40, "T1": 60, "T2": 85, "T3": 110, "T4": 140, "T5": 170, "T6+": 220}
            living_area = rng.normal(base_areas[typology], scale=10.0) 
            total_area = living_area * rng.uniform(1.1, 1.3)
            
            # Calculate final evaluation price based on region pricing + quality + age
            quality_multiplier = quality / 3.0
            age_discount = max(0.5, 1 - (age * 0.01)) # Max 50% discount for old houses
            eval_price = total_area * base_sqm_price * quality_multiplier * age_discount
            
            houses.append(
                House(
                    id=uuid4(),
                    age=int(age),
                    evaluation_price=round(eval_price, 2),
                    selling_price=round(eval_price * 1.05, 2), # Default asking price 5% above eval
                    total_area=round(total_area, 2),
                    living_area=round(living_area, 2),
                    forSale=True,
                    forRent=False,
                    owner=owner,
                    quality=round(quality, 2),
                    typology=typology,
                    size=round(living_area / 30.0, 2),
                    location=region
                )
            )
            
    return houses

def generate_households(hh_config: dict, regions: list[Region], rng: np.random.Generator) -> list[Household]:
    households = []
    total_count = hh_config["total_count"]
    
    # Normalize weights just in case they don't equal exactly 1.0
    weights = [arch["weight"] for arch in hh_config["archetypes"]]
    probs = np.array(weights) / sum(weights)
    
    # Calculate exactly how many of each archetype to build
    arch_counts = rng.multinomial(total_count, probs)
    
    for archetype, count in zip(hh_config["archetypes"], arch_counts):
        for _ in range(count):
            members = []
            
            # --- Generate Adults ---
            for _ in range(archetype["adults"]):
                age = int(rng.uniform(archetype["adult_age_range"][0], archetype["adult_age_range"][1]))
                
                edu_keys = list(archetype["education_weights"].keys())
                edu_probs = list(archetype["education_weights"].values())
                education = rng.choice(edu_keys, p=edu_probs)
                
                # Use our flexible distribution helper for income!
                income = draw_from_dist(archetype["base_income"], rng)
                income *= (1 + (education * 0.15)) # Education multiplier
                
                adult = Person(
                    id=uuid4(),
                    age=age,
                    income=round(income, 2),
                    capital=round(income * rng.uniform(0.5, 3.0), 2),
                    education=int(education),
                    nationality="Local"
                )
                members.append(adult)
                
            # --- Generate Children ---
            # draw_from_dist effortlessly handles 'constant', 'poisson', or 'uniform'
            num_children = int(draw_from_dist(archetype["children"], rng))
                
            for _ in range(num_children):
                child = Person(
                    id=uuid4(),
                    age=int(rng.uniform(0, 18)),
                    income=0.0,
                    capital=0.0,
                    education=1,
                    nationality="Local"
                )
                members.append(child)
            
            # --- Assemble Household ---
            total_income = sum(m.income for m in members)
            total_capital = sum(m.capital for m in members)
            
            household = Household(
                id=uuid4(),
                members=members,
                rent=0.0,
                income=round(total_income, 2),
                capital=round(total_capital, 2),
                preference=rng.choice(regions),
                # These start empty/None. The Assignment step will fill them!
                living_house=None, # **Make sure this is Optional[House] in Pydantic**
                houses=[],
                contracts=[],
                mortgages=[]
            )
            households.append(household)
            
    return households


def assign_housing_market(households: list[Household], houses: list[House], market_config: dict) -> tuple[list[Household], list[House]]:
    
    # 1. Define Budgets and Sort Households by Wealth
    def get_budget(hh: Household) -> float:
        return hh.capital + (hh.income * 4.5)

    sorted_households = sorted(households, key=get_budget, reverse=True)
    
    # Pre-calculate market caps based on YAML config
    total_hh = len(households)
    num_investors = int(total_hh * market_config["investor_percentage"])
    target_owners = int(total_hh * market_config["target_homeownership_rate"])
    
    available_for_sale = [h for h in houses if h.forSale]
    current_owners = 0

    # ==========================================
    # PHASE 1: THE SALES MARKET (BUYING)
    # ==========================================
    
    for i, hh in enumerate(sorted_households):
        if not available_for_sale:
            break
            
        is_investor = i < num_investors
        properties_to_buy = market_config["max_investment_properties"] + 1 if is_investor else 1
        
        # Stop allowing primary residence purchases if we hit our homeownership target
        # (Investors can still buy, but they won't live in them)
        if not is_investor and current_owners >= target_owners:
            continue 

        for purchase_num in range(properties_to_buy):
            budget = get_budget(hh)
            affordable = [h for h in available_for_sale if h.selling_price <= budget]
            
            if not affordable:
                break # Can't afford any more houses
                
            # Filter by preference for the primary home, otherwise just buy best quality
            is_primary = (hh.living_house is None)
            valid_choices = affordable
            if is_primary:
                valid_choices = [h for h in affordable if h.location.id == hh.preference.id] or affordable
                
            valid_choices.sort(key=lambda x: x.quality, reverse=True)
            chosen_house = valid_choices[0]
            
            # Execute Sale
            available_for_sale.remove(chosen_house)
            chosen_house.forSale = False
            chosen_house.owner = hh
            hh.houses.append(chosen_house)
            
            if is_primary:
                hh.living_house = chosen_house
                current_owners += 1
            else:
                # Investment property -> Put it on the rental market
                chosen_house.forRent = True
                
            # Execute Mortgage (Simplified 20% down)
            downpayment = min(hh.capital, chosen_house.selling_price * 0.20)
            loan_amount = chosen_house.selling_price - downpayment
            hh.capital -= downpayment
            
            if loan_amount > 0:
                mortgage = Loan(
                    id=uuid4(), house=chosen_house, remaining_morgtage=loan_amount,
                    paid_mortgage=downpayment, rent=0.0, interest_rate=0.04,
                    spread=0.015, tax_type="fixed"
                )
                hh.mortgages.append(mortgage)

    # ==========================================
    # PHASE 2: THE RENTAL MARKET
    # ==========================================
    
    # Renters are anyone without a living_house
    renters = [hh for hh in sorted_households if hh.living_house is None]
    
    # Available rentals are investor properties OR unsold constructor properties
    available_for_rent = [h for h in houses if getattr(h, "forRent", False) or isinstance(h.owner, Constructor)]
    
    for hh in renters:
        if not available_for_rent:
            break
            
        # Max monthly rent is X% of annual income / 12
        max_monthly_rent = (hh.income * market_config["max_rent_to_income_ratio"]) / 12.0
        
        # Calculate monthly rent for available houses (Value * Yield / 12)
        yield_rate = market_config["annual_rental_yield"]
        
        affordable_rentals = []
        for h in available_for_rent:
            monthly_rent = (h.evaluation_price * yield_rate) / 12.0
            if monthly_rent <= max_monthly_rent:
                affordable_rentals.append((h, monthly_rent))
                
        if not affordable_rentals:
            continue # Priced out of the rental market
            
        # Sort by quality
        affordable_rentals.sort(key=lambda x: x[0].quality, reverse=True)
        chosen_house, agreed_rent = affordable_rentals[0]
        
        # Execute Lease
        available_for_rent.remove(chosen_house)
        hh.living_house = chosen_house
        hh.rent = agreed_rent
        
        contract = Contracts(
            id=uuid4(),
            house=chosen_house,
            tenant=hh,
            landlord=chosen_house.owner,
            rent=round(agreed_rent, 2),
            duration=12 # MVP: 12 month lease
        )
        hh.contracts.append(contract)
        
    return households, houses


def _generate_synthetic(config: dict) -> Scenario:
    """The orchestrator that wires all the pieces together."""
    rng = np.random.default_rng(config["seed"])
    
    constructors = generate_constructors(config["constructors"], rng)
    regions = generate_regions(config["geography"], rng)
    houses = generate_houses(config["houses"], regions, constructors, rng)
    households = generate_households(config["households"], regions, rng)
    
    # Run the Market Initialization
    households, houses = assign_housing_market(households, houses, config["market_initialization"])
    
    return Scenario(
        regions=regions, 
        households=households, 
        houses=houses, 
        constructors=constructors
    )

def build_and_export_scenario(
    yaml_path: str, 
    output_dir: str, 
    scenario_name: str = "initial_scenario", 
    export_format: Literal["json", "pickle"] = "json"
) -> Path:
    """
    Reads the YAML config, generates the Scenario, and exports it to disk.
    """
    # 1. Load the YAML configuration
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    # 2. Generate the Scenario in memory
    print("Generating synthetic data...")
    scenario = _generate_synthetic(config)
    
    # 3. Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 4. Export the data
    if export_format == "json":
        file_path = out_path / f"{scenario_name}.json"
        
        # Pydantic's model_dump_json handles UUIDs, lists, and nested objects automatically
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(scenario.model_dump_json(indent=2))
            
    elif export_format == "pickle":
        file_path = out_path / f"{scenario_name}.pkl"
        
        # Pickle natively serializes exact Python objects in memory
        with open(file_path, 'wb') as f:
            pickle.dump(scenario, f)
            
    else:
        raise ValueError(f"Unsupported export format: {export_format}")

    print(f"Successfully exported scenario to {file_path}")
    return file_path

def main():
    """
    Main execution entry point for the synthetic data generation pipeline.
    """
    parser = argparse.ArgumentParser(description="Generate Synthetic Scenario Data for ABM Simulation")
    
    # Define command-line arguments with sensible defaults
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml", 
        help="Path to the YAML configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--outdir", 
        type=str, 
        default="scenarios", 
        help="Directory to save the generated scenario (default: scenarios)"
    )
    parser.add_argument(
        "--name", 
        type=str, 
        default="config_scenario", 
        help="Name of the output file without extension (default: conf_scenario)"
    )
    parser.add_argument(
        "--format", 
        type=str, 
        choices=["json", "pickle"], 
        default="pickle", 
        help="Export format (default: pickle)"
    )

    args = parser.parse_args()

    print("="*50)
    print("🏗️  SYNTHETIC DATA GENERATION PIPELINE")
    print("="*50)
    print(f"📄 Config File: {args.config}")
    print(f"📁 Output Dir:  {args.outdir}")
    print(f"📦 Format:      {args.format.upper()}")
    print("-" * 50)

    # Ensure the config file actually exists before starting
    if not Path(args.config).exists():
        print(f"❌ Error: Configuration file '{args.config}' not found.")
        print("Please ensure the file exists and the path is correct.")
        sys.exit(1)

    try:
        # Trigger the master export function we built previously
        output_file = build_and_export_scenario(
            yaml_path=args.config,
            output_dir=args.outdir,
            scenario_name=args.name,
            export_format=args.format
        )
        
        print("-" * 50)
        print("✅ Pipeline finished successfully!")
        print(f"🚀 Your scenario is ready for the simulator engine at:\n   -> {output_file.absolute()}")
        
    except Exception as e:
        print(f"\n❌ An error occurred during generation:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    # how to run it:
    #python datageneration.py --config housing_crash_config.yaml --name crash_scenario --format json
    main()