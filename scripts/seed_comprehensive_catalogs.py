#!/usr/bin/env python3
"""
Comprehensive Power Plant HSE Catalogs Seeding Script
Creates realistic hazards and controls for power plant operations
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db
from app.models import Hazard, ControlMeasure

def seed_comprehensive_hazards():
    """Seed comprehensive power plant hazards with descriptions and parameters"""
    
    hazards_data = [
        # Electrical Hazards
        {
            "name": "High Voltage Electrical Shock",
            "category": "Electrical",
            "description": "Risk of electrical shock from high voltage equipment (>1000V) including transformers, switchgear, and transmission lines. Can cause severe burns, cardiac arrest, or death.",
            "default_likelihood": 3,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Voltage Level",
            "parameter_unit": "kV"
        },
        {
            "name": "Low Voltage Electrical Shock",
            "category": "Electrical",
            "description": "Risk of electrical shock from low voltage equipment (<1000V) including control panels, lighting circuits, and portable tools. Can cause burns and muscle contractions.",
            "default_likelihood": 2,
            "default_severity": 3,
            "requires_parameter": True,
            "parameter_label": "Voltage Level",
            "parameter_unit": "V"
        },
        {
            "name": "Arc Flash/Arc Blast",
            "category": "Electrical",
            "description": "Risk of arc flash explosion when working on energized electrical equipment. Can cause severe burns, blindness, and hearing damage from intense heat and pressure wave.",
            "default_likelihood": 2,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Arc Flash Boundary",
            "parameter_unit": "feet"
        },
        {
            "name": "Static Electricity",
            "category": "Electrical",
            "description": "Risk of static discharge igniting flammable vapors or causing equipment damage, particularly in fuel handling and chemical storage areas.",
            "default_likelihood": 3,
            "default_severity": 4,
            "requires_parameter": False
        },
        
        # Mechanical Hazards
        {
            "name": "Rotating Machinery Entanglement",
            "category": "Mechanical",
            "description": "Risk of clothing, hair, or body parts being caught in rotating equipment such as turbines, pumps, fans, and conveyors. Can cause severe crushing injuries or death.",
            "default_likelihood": 2,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Rotation Speed",
            "parameter_unit": "RPM"
        },
        {
            "name": "High Pressure Steam Release",
            "category": "Mechanical",
            "description": "Risk of severe burns from high pressure steam leaks or releases from boilers, steam lines, and turbines. Can cause third-degree burns and respiratory damage.",
            "default_likelihood": 3,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Steam Pressure",
            "parameter_unit": "psi"
        },
        {
            "name": "Compressed Air Release",
            "category": "Mechanical",
            "description": "Risk of injury from high pressure compressed air systems used for instrumentation and pneumatic tools. Can cause eye injury or air embolism.",
            "default_likelihood": 2,
            "default_severity": 3,
            "requires_parameter": True,
            "parameter_label": "Air Pressure",
            "parameter_unit": "psi"
        },
        {
            "name": "Heavy Equipment Operation",
            "category": "Mechanical",
            "description": "Risk of crushing, striking, or run-over injuries from mobile equipment including cranes, forklifts, and maintenance vehicles operating in plant areas.",
            "default_likelihood": 3,
            "default_severity": 4,
            "requires_parameter": True,
            "parameter_label": "Equipment Weight",
            "parameter_unit": "tons"
        },
        
        # Chemical Hazards
        {
            "name": "Toxic Gas Exposure",
            "category": "Chemical",
            "description": "Risk of poisoning from toxic gases such as hydrogen sulfide, carbon monoxide, or chlorine used in water treatment. Can cause respiratory failure or death.",
            "default_likelihood": 2,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Gas Concentration",
            "parameter_unit": "ppm"
        },
        {
            "name": "Corrosive Chemical Burns",
            "category": "Chemical",
            "description": "Risk of chemical burns from acids, caustics, and cleaning chemicals used in water treatment and equipment maintenance. Can cause severe skin and eye damage.",
            "default_likelihood": 3,
            "default_severity": 4,
            "requires_parameter": True,
            "parameter_label": "Chemical pH",
            "parameter_unit": "pH"
        },
        {
            "name": "Fuel Oil Spill/Fire",
            "category": "Chemical",
            "description": "Risk of fire or explosion from fuel oil leaks in storage tanks, supply lines, or burner systems. Can cause severe burns and facility damage.",
            "default_likelihood": 2,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Fuel Volume",
            "parameter_unit": "gallons"
        },
        {
            "name": "Asbestos Exposure",
            "category": "Chemical",
            "description": "Risk of lung disease from disturbing asbestos-containing materials in older plant insulation, gaskets, and fireproofing during maintenance activities.",
            "default_likelihood": 3,
            "default_severity": 5,
            "requires_parameter": False
        },
        
        # Physical Hazards
        {
            "name": "Working at Height",
            "category": "Physical",
            "description": "Risk of falls from elevated work platforms, ladders, scaffolding, or structures when performing maintenance on boilers, stacks, or transmission equipment.",
            "default_likelihood": 3,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Working Height",
            "parameter_unit": "feet"
        },
        {
            "name": "Confined Space Entry",
            "category": "Physical",
            "description": "Risk of asphyxiation, toxic exposure, or entrapment in confined spaces such as tanks, vessels, manholes, and underground vaults.",
            "default_likelihood": 2,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Space Volume",
            "parameter_unit": "cubic feet"
        },
        {
            "name": "Extreme Heat Exposure",
            "category": "Physical",
            "description": "Risk of heat stress, heat stroke, or burns from working near boilers, furnaces, steam lines, or in hot weather conditions.",
            "default_likelihood": 4,
            "default_severity": 3,
            "requires_parameter": True,
            "parameter_label": "Temperature",
            "parameter_unit": "°F"
        },
        {
            "name": "Noise Exposure",
            "category": "Physical",
            "description": "Risk of hearing loss from prolonged exposure to high noise levels from turbines, generators, pumps, and other rotating equipment.",
            "default_likelihood": 4,
            "default_severity": 3,
            "requires_parameter": True,
            "parameter_label": "Noise Level",
            "parameter_unit": "dB"
        },
        {
            "name": "Manual Handling Injury",
            "category": "Physical",
            "description": "Risk of back injury, muscle strain, or crushing from lifting, carrying, or moving heavy equipment, tools, or materials during maintenance.",
            "default_likelihood": 4,
            "default_severity": 3,
            "requires_parameter": True,
            "parameter_label": "Load Weight",
            "parameter_unit": "lbs"
        },
        
        # Radiation Hazards
        {
            "name": "Ionizing Radiation Exposure",
            "category": "Radiation",
            "description": "Risk of radiation exposure from nuclear fuel, radioactive sources used in instrumentation, or contaminated materials in nuclear facilities.",
            "default_likelihood": 1,
            "default_severity": 5,
            "requires_parameter": True,
            "parameter_label": "Radiation Level",
            "parameter_unit": "mrem/hr"
        },
        {
            "name": "Non-Ionizing Radiation",
            "category": "Radiation",
            "description": "Risk of burns or eye damage from intense infrared radiation from furnaces, welding operations, or high-intensity lighting systems.",
            "default_likelihood": 3,
            "default_severity": 3,
            "requires_parameter": False
        },
        
        # Environmental Hazards
        {
            "name": "Slip, Trip, Fall on Same Level",
            "category": "Environmental",
            "description": "Risk of injury from slipping on wet surfaces, tripping over obstacles, or falling on uneven surfaces in plant walkways and work areas.",
            "default_likelihood": 4,
            "default_severity": 2,
            "requires_parameter": False
        },
        {
            "name": "Severe Weather Exposure",
            "category": "Environmental",
            "description": "Risk of injury from lightning, high winds, ice, or extreme temperatures when working on outdoor equipment or transmission lines.",
            "default_likelihood": 3,
            "default_severity": 4,
            "requires_parameter": True,
            "parameter_label": "Wind Speed",
            "parameter_unit": "mph"
        }
    ]
    
    print("Seeding comprehensive hazards...")
    for hazard_data in hazards_data:
        existing = Hazard.query.filter_by(name=hazard_data["name"]).first()
        if not existing:
            hazard = Hazard(**hazard_data)
            db.session.add(hazard)
            print(f"  Added: {hazard_data['name']}")
        else:
            print(f"  Exists: {hazard_data['name']}")

def seed_comprehensive_controls():
    """Seed comprehensive power plant controls with proper hierarchy categories"""
    
    controls_data = [
        # ELIMINATION - Most Effective
        {
            "name": "Remote Operation System",
            "category": "Elimination",
            "description": "Implement remote control systems to eliminate human presence in hazardous areas during normal operations. Includes SCADA systems and automated controls.",
            "effectiveness": 5
        },
        {
            "name": "Equipment Redesign",
            "category": "Elimination",
            "description": "Redesign equipment to eliminate hazardous energy sources, toxic materials, or dangerous mechanical components from the work environment.",
            "effectiveness": 5
        },
        {
            "name": "Process Substitution",
            "category": "Elimination",
            "description": "Replace hazardous processes with inherently safer alternatives that eliminate the need for human exposure to dangerous conditions.",
            "effectiveness": 5
        },
        
        # SUBSTITUTION - Very Effective
        {
            "name": "Less Hazardous Chemical Substitution",
            "category": "Substitution",
            "description": "Replace toxic or corrosive chemicals with less hazardous alternatives in water treatment, cleaning, and maintenance operations.",
            "effectiveness": 4
        },
        {
            "name": "Lower Voltage Equipment",
            "category": "Substitution",
            "description": "Use lower voltage equipment where possible to reduce electrical shock and arc flash risks in control and instrumentation systems.",
            "effectiveness": 4
        },
        {
            "name": "Mechanical Tools vs Manual",
            "category": "Substitution",
            "description": "Replace manual lifting and handling with mechanical aids such as hoists, conveyors, and lifting devices to reduce ergonomic risks.",
            "effectiveness": 4
        },
        
        # ENGINEERING CONTROLS - Moderately Effective
        {
            "name": "Lockout/Tagout (LOTO) System",
            "category": "Engineering Controls",
            "description": "Comprehensive energy isolation system with locks, tags, and verification procedures to prevent unexpected equipment startup during maintenance.",
            "effectiveness": 4
        },
        {
            "name": "Machine Guarding",
            "category": "Engineering Controls",
            "description": "Physical barriers, interlocks, and safety devices to prevent contact with rotating machinery, pinch points, and other mechanical hazards.",
            "effectiveness": 4
        },
        {
            "name": "Ventilation Systems",
            "category": "Engineering Controls",
            "description": "Local exhaust ventilation and general dilution systems to control airborne contaminants, heat, and toxic gases in work areas.",
            "effectiveness": 4
        },
        {
            "name": "Fall Protection Systems",
            "category": "Engineering Controls",
            "description": "Permanent fall protection including guardrails, safety nets, and anchor points for working at heights on platforms and structures.",
            "effectiveness": 4
        },
        {
            "name": "Emergency Shutdown Systems",
            "category": "Engineering Controls",
            "description": "Automatic and manual emergency shutdown systems to quickly isolate hazardous energy and materials during emergency conditions.",
            "effectiveness": 4
        },
        {
            "name": "Gas Detection Systems",
            "category": "Engineering Controls",
            "description": "Fixed and portable gas monitoring systems with alarms to detect toxic, flammable, or oxygen-deficient atmospheres.",
            "effectiveness": 4
        },
        {
            "name": "Fire Suppression Systems",
            "category": "Engineering Controls",
            "description": "Automatic sprinkler, deluge, foam, and gaseous fire suppression systems to control fires involving electrical equipment and flammable liquids.",
            "effectiveness": 4
        },
        {
            "name": "Noise Control Engineering",
            "category": "Engineering Controls",
            "description": "Sound enclosures, vibration dampening, and acoustic barriers to reduce noise exposure from turbines, generators, and pumps.",
            "effectiveness": 3
        },
        {
            "name": "Electrical Safety Systems",
            "category": "Engineering Controls",
            "description": "Arc flash protection, ground fault circuit interrupters (GFCI), and electrical safety interlocks to prevent electrical injuries.",
            "effectiveness": 4
        },
        {
            "name": "Pressure Relief Systems",
            "category": "Engineering Controls",
            "description": "Safety valves, rupture discs, and pressure relief systems to prevent over-pressurization of boilers, vessels, and piping systems.",
            "effectiveness": 4
        },
        
        # ADMINISTRATIVE CONTROLS - Less Effective
        {
            "name": "Hot Work Permit System",
            "category": "Administrative Controls",
            "description": "Formal permit system for welding, cutting, and other hot work operations with fire watch requirements and area preparation procedures.",
            "effectiveness": 3,
            "reference": "SOP-HW-001"
        },
        {
            "name": "Confined Space Entry Permit",
            "category": "Administrative Controls",
            "description": "Comprehensive permit system for confined space entry including atmospheric testing, ventilation, and rescue procedures.",
            "effectiveness": 3,
            "reference": "PERMIT-CS-002"
        },
        {
            "name": "Electrical Work Permit",
            "category": "Administrative Controls",
            "description": "Permit system for electrical work including arc flash analysis, PPE requirements, and qualified person verification.",
            "effectiveness": 3,
            "reference": "PERMIT-EL-003"
        },
        {
            "name": "Job Safety Analysis (JSA)",
            "category": "Administrative Controls",
            "description": "Systematic analysis of job tasks to identify hazards and establish safe work procedures before beginning maintenance or operations.",
            "effectiveness": 3
        },
        {
            "name": "Safety Training Programs",
            "category": "Administrative Controls",
            "description": "Comprehensive safety training including initial orientation, job-specific training, and annual refresher courses for all personnel.",
            "effectiveness": 3
        },
        {
            "name": "Competency-Based Training",
            "category": "Administrative Controls",
            "description": "Skills-based training programs with competency assessments to ensure workers can safely perform specific tasks before authorization.",
            "effectiveness": 3
        },
        {
            "name": "Equipment-Specific Training",
            "category": "Administrative Controls",
            "description": "Specialized training on operation and maintenance of specific power plant equipment including turbines, boilers, and electrical systems.",
            "effectiveness": 3
        },
        {
            "name": "Emergency Response Training",
            "category": "Administrative Controls",
            "description": "Regular training and drills for emergency scenarios including fire response, chemical spills, medical emergencies, and evacuation procedures.",
            "effectiveness": 3
        },
        {
            "name": "Electrical Safety Training",
            "category": "Administrative Controls",
            "description": "Specialized training for qualified electrical workers including arc flash awareness, LOTO procedures, and electrical PPE requirements.",
            "effectiveness": 3
        },
        {
            "name": "Confined Space Training",
            "category": "Administrative Controls",
            "description": "Training for entrants, attendants, and supervisors on confined space hazards, entry procedures, and rescue operations.",
            "effectiveness": 3
        },
        {
            "name": "Fall Protection Training",
            "category": "Administrative Controls",
            "description": "Training on proper use of fall protection equipment, inspection procedures, and rescue techniques for work at heights.",
            "effectiveness": 3
        },
        {
            "name": "Hazard Recognition Training",
            "category": "Administrative Controls",
            "description": "Training workers to identify and assess workplace hazards, near-miss reporting, and hazard communication procedures.",
            "effectiveness": 3
        },
        {
            "name": "Refresher Training Program",
            "category": "Administrative Controls",
            "description": "Periodic refresher training to maintain competency and update workers on new procedures, regulations, and lessons learned.",
            "effectiveness": 2
        },
        {
            "name": "New Employee Orientation",
            "category": "Administrative Controls",
            "description": "Comprehensive safety orientation for new employees covering plant hazards, emergency procedures, and safety culture expectations.",
            "effectiveness": 3
        },
        {
            "name": "Standard Operating Procedures",
            "category": "Administrative Controls",
            "description": "Detailed written procedures for routine operations, maintenance, and emergency response to ensure consistent safe practices.",
            "effectiveness": 3,
            "reference": "SOP-OPS-100 Series"
        },
        {
            "name": "Safety Inspections",
            "category": "Administrative Controls",
            "description": "Regular safety inspections of equipment, work areas, and safety systems to identify and correct hazardous conditions.",
            "effectiveness": 3
        },
        {
            "name": "Emergency Response Procedures",
            "category": "Administrative Controls",
            "description": "Written emergency procedures for fire, chemical spills, medical emergencies, and severe weather with regular drills and training.",
            "effectiveness": 3
        },
        {
            "name": "Contractor Safety Management",
            "category": "Administrative Controls",
            "description": "Safety requirements and oversight for contractors including qualification verification, orientation, and work supervision.",
            "effectiveness": 3
        },
        {
            "name": "Incident Investigation System",
            "category": "Administrative Controls",
            "description": "Systematic investigation of accidents, near-misses, and unsafe conditions to identify root causes and prevent recurrence.",
            "effectiveness": 2
        },
        {
            "name": "Safety Communication Program",
            "category": "Administrative Controls",
            "description": "Regular safety meetings, toolbox talks, and safety bulletins to communicate hazards, procedures, and lessons learned.",
            "effectiveness": 2
        },
        {
            "name": "Work Scheduling Controls",
            "category": "Administrative Controls",
            "description": "Scheduling work during optimal conditions, limiting overtime, and ensuring adequate rest periods to prevent fatigue-related errors.",
            "effectiveness": 2
        },
        {
            "name": "Behavioral Safety Program",
            "category": "Administrative Controls",
            "description": "Peer observation and feedback program to reinforce safe behaviors and identify unsafe acts before they result in injuries.",
            "effectiveness": 2
        },
        
        # PERSONAL PROTECTIVE EQUIPMENT - Least Effective
        {
            "name": "Arc Flash PPE Suit",
            "category": "Personal Protective Equipment",
            "description": "Complete arc-rated protective clothing system including suit, hood, gloves, and boots rated for specific arc flash energy levels.",
            "effectiveness": 3,
            "reference": "NFPA 70E Category 4"
        },
        {
            "name": "Self-Contained Breathing Apparatus",
            "category": "Personal Protective Equipment",
            "description": "SCBA systems for entry into oxygen-deficient or toxic atmospheres during emergency response and confined space work.",
            "effectiveness": 3
        },
        {
            "name": "Chemical Resistant Clothing",
            "category": "Personal Protective Equipment",
            "description": "Chemical protective suits, aprons, and gloves rated for specific chemicals used in water treatment and maintenance operations.",
            "effectiveness": 3
        },
        {
            "name": "Fall Protection Harness",
            "category": "Personal Protective Equipment",
            "description": "Full-body safety harnesses with shock-absorbing lanyards and self-retracting lifelines for work at heights above 6 feet.",
            "effectiveness": 3
        },
        {
            "name": "Hard Hat with Electrical Rating",
            "category": "Personal Protective Equipment",
            "description": "Class E hard hats rated for electrical work up to 20,000 volts with chin straps for work at heights or in windy conditions.",
            "effectiveness": 2
        },
        {
            "name": "Safety Glasses with Side Shields",
            "category": "Personal Protective Equipment",
            "description": "Impact-resistant safety glasses with side protection for general plant work and chemical splash protection.",
            "effectiveness": 2
        },
        {
            "name": "Hearing Protection",
            "category": "Personal Protective Equipment",
            "description": "Earplugs and earmuffs rated for specific noise levels with communication capabilities for high-noise work areas.",
            "effectiveness": 2
        },
        {
            "name": "Insulated Electrical Gloves",
            "category": "Personal Protective Equipment",
            "description": "Rubber insulating gloves with leather protectors rated for specific voltage levels for electrical work.",
            "effectiveness": 3
        },
        {
            "name": "Steel-Toed Safety Boots",
            "category": "Personal Protective Equipment",
            "description": "Safety footwear with steel toes, puncture-resistant soles, and electrical hazard protection for general plant work.",
            "effectiveness": 2
        },
        {
            "name": "High-Visibility Clothing",
            "category": "Personal Protective Equipment",
            "description": "Reflective vests and clothing for visibility when working around mobile equipment and in outdoor areas.",
            "effectiveness": 2
        },
        {
            "name": "Cut-Resistant Gloves",
            "category": "Personal Protective Equipment",
            "description": "Cut-resistant gloves rated for handling sharp materials and tools during maintenance operations.",
            "effectiveness": 2
        },
        {
            "name": "Respirator (Half-Face)",
            "category": "Personal Protective Equipment",
            "description": "Half-face respirators with appropriate cartridges for protection against specific airborne contaminants and dusts.",
            "effectiveness": 2
        }
    ]
    
    print("Seeding comprehensive controls...")
    for control_data in controls_data:
        existing = ControlMeasure.query.filter_by(name=control_data["name"]).first()
        if not existing:
            control = ControlMeasure(**control_data)
            db.session.add(control)
            print(f"  Added: {control_data['name']} ({control_data['category']})")
        else:
            print(f"  Exists: {control_data['name']}")

def main():
    """Main seeding function"""
    app = create_app()
    
    with app.app_context():
        print("Starting comprehensive catalog seeding...")
        
        # Seed hazards and controls
        seed_comprehensive_hazards()
        seed_comprehensive_controls()
        
        # Commit all changes
        try:
            db.session.commit()
            print("\nCOMPREHENSIVE CATALOGS SEEDED SUCCESSFULLY!")
            
            # Print summary
            hazard_count = Hazard.query.count()
            control_count = ControlMeasure.query.count()
            print(f"\nSummary:")
            print(f"  Total Hazards: {hazard_count}")
            print(f"  Total Controls: {control_count}")
            
            # Print controls by category
            print(f"\nControls by Category:")
            for category in ["Elimination", "Substitution", "Engineering Controls", "Administrative Controls", "Personal Protective Equipment"]:
                count = ControlMeasure.query.filter_by(category=category).count()
                print(f"  {category}: {count}")
                
        except Exception as e:
            db.session.rollback()
            print(f"ERROR seeding catalogs: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
