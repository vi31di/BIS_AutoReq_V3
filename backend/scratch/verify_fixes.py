import asyncio
import json
from api.db import DBConnection, init_db_connection
from api.resolve.resolver import resolve_lookup, get_dropdown_options

async def main():
    await init_db_connection()
    async with DBConnection() as db:
        await db.execute("DELETE FROM resolution_cache")
        print("================ VERIFYING FIX 1: Ageing Test ================")
        # Test Case 1: Insulation, Type A, Before Ageing
        res = await resolve_lookup(db, {
            "test_name": "Ageing in air oven",
            "component": "Insulation",
            "category": "Type A",
            "timing": "before"
        })
        print("Insulation Type A Before:", res["value"])
        assert "Min: 12.5" in res["value"] and "Min: 150%" in res["value"]
        
        # Test Case 2: Insulation, Type A, After Ageing
        res = await resolve_lookup(db, {
            "test_name": "Ageing in air oven",
            "component": "Insulation",
            "category": "Type A",
            "timing": "after"
        })
        print("Insulation Type A After:", res["value"])
        assert "Variation Max: ±20%" in res["value"]
        
        # Test Case 3: Sheath, ST1, After Ageing
        res = await resolve_lookup(db, {
            "test_name": "Ageing in air oven",
            "component": "Sheath",
            "category": "ST1",
            "timing": "after"
        })
        print("Sheath ST1 After:", res["value"])
        assert "Variation Max: ±20%" in res["value"]

        print("\n================ VERIFYING FIX 1: Loss of Mass Test ================")
        # Test Case 4: Insulation, Type A, Before
        res = await resolve_lookup(db, {
            "test_name": "Loss of mass test",
            "component": "Insulation",
            "category": "Type A",
            "timing": "before"
        })
        print("Insulation Type A Before:", res["value"])
        assert "N/A" in res["value"]
        
        # Test Case 5: Insulation, Type A, After
        res = await resolve_lookup(db, {
            "test_name": "Loss of mass test",
            "component": "Insulation",
            "category": "Type A",
            "timing": "after"
        })
        print("Insulation Type A After:", res["value"])
        assert "2 mg/cm²" in res["value"]

        # Test Case 6: Insulation, Type C, After
        res = await resolve_lookup(db, {
            "test_name": "Loss of mass test",
            "component": "Insulation",
            "category": "Type C",
            "timing": "after"
        })
        print("Insulation Type C After:", res["value"])
        assert "N/A" in res["value"]

        print("\n================ VERIFYING FIX 2: Shrinkage Test ================")
        # Test Case 8: Insulation Type A
        res = await resolve_lookup(db, {
            "test_name": "Shrinkage test",
            "component": "Insulation",
            "category": "Type A"
        })
        print("Insulation Shrinkage:", res["value"])
        assert "Max Shrinkage: 4%" in res["value"]
        
        # Test Case 9: Sheath ST1
        res = await resolve_lookup(db, {
            "test_name": "Shrinkage test",
            "component": "Sheath",
            "category": "ST1"
        })
        print("Sheath ST1 Shrinkage:", res["value"])
        assert "Max Shrinkage: 4%" in res["value"]

        print("\n================ VERIFYING FIX 4: Thickness Test ================")
        # Test Case 10: Unsheathed Single-Core, Class 2, Size 1.5
        res = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "class": "Class 2",
            "size_mm2": 1.5,
            "construction": "unsheathed_single_core"
        })
        print("Unsheathed Single-Core rigid 1.5:", res["value"])
        assert "0.7 mm" in res["value"]

        # Test Case 11: Sheathed Multi-Core, Class 5, Size 1.5
        res = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "class": "Class 5",
            "size_mm2": 1.5,
            "construction": "sheathed_multi_core"
        })
        print("Sheathed Multi-Core 1.5:", res["value"])
        assert "0.6 mm" in res["value"]

        # Test Case 12: Sheathed Multi-Core Sheath Thickness, Size 1.5
        res = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Sheath",
            "size_mm2": 1.5,
            "construction": "sheathed_multi_core"
        })
        print("Sheathed Multi-Core Sheath Thickness 1.5:", res["value"])
        assert "0.8 mm" in res["value"] or "0.9 mm" in res["value"]

        print("\n================ VERIFYING FIX 5: Insulation Resistance ================")
        # Test Case 13: Insulation Type A
        res = await resolve_lookup(db, {
            "test_name": "Insulation resistance test",
            "category": "Type A"
        })
        print("Type A IR Constant:", res["value"])
        assert "36.7 MΩ·km" in res["value"] and "0.037 MΩ·km" in res["value"]

        # Test Case 14: Insulation Type B
        res = await resolve_lookup(db, {
            "test_name": "Insulation resistance test",
            "category": "Type B"
        })
        print("Type B IR Constant:", res["value"])
        assert "36.7 MΩ·km" in res["value"] and "0.37 MΩ·km" in res["value"]

        print("\n================ VERIFYING NEW MATRIX SIMPLIFICATIONS ================")
        # Test Case 16: Hot deformation Insulation Type A
        res = await resolve_lookup(db, {
            "test_name": "Hot deformation test",
            "component": "Insulation",
            "category": "Type A"
        })
        print("Hot Deformation Insulation A:", res["value"])
        assert "80°C" in res["value"] and "50%" in res["value"]
        assert len(res["resolution_path"]) >= 4
        assert res["resolution_path"][0]["address"] == "IS694-2010"
        assert "IS5831-1984" in res["resolution_path"][2]["address"]

        # Test Case 16b: Hot deformation Sheath ST2
        res = await resolve_lookup(db, {
            "test_name": "Hot deformation test",
            "component": "Sheath",
            "category": "ST2"
        })
        print("Hot Deformation Sheath ST2:", res["value"])
        assert "80°C" in res["value"] and "50%" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 17: Heat shock Sheath ST1
        res = await resolve_lookup(db, {
            "test_name": "Heat shock test",
            "component": "Sheath",
            "category": "ST1"
        })
        print("Heat Shock Sheath ST1:", res["value"])
        assert "150°C" in res["value"] and "No signs of cracks or scales" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 18: Cold bend Insulation Type C
        res = await resolve_lookup(db, {
            "test_name": "Cold bend test",
            "component": "Insulation",
            "category": "Type C"
        })
        print("Cold Bend Insulation C:", res["value"])
        assert "-15°C" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 18b: Cold bend Sheath ST2
        res = await resolve_lookup(db, {
            "test_name": "Cold bend test",
            "component": "Sheath",
            "category": "ST2"
        })
        print("Cold Bend Sheath ST2:", res["value"])
        assert "-15°C" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 19: Thermal stability Insulation Type C
        res = await resolve_lookup(db, {
            "test_name": "Thermal stability",
            "component": "Insulation",
            "category": "Type C"
        })
        print("Thermal Stability Insulation C:", res["value"])
        assert "100 minutes" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 19b: Thermal stability Sheath ST1
        res = await resolve_lookup(db, {
            "test_name": "Thermal stability",
            "component": "Sheath",
            "category": "ST1"
        })
        print("Thermal Stability Sheath ST1:", res["value"])
        assert "40 minutes" in res["value"]

        print("\n================ VERIFYING ANNEALING AND HIGH VOLTAGE FIXES ================")
        # Test Case 20: Annealing test, Copper, 0.15 mm
        res = await resolve_lookup(db, {
            "test_name": "Annealing test (for copper)",
            "material": "Copper",
            "wire_diameter": 0.15
        })
        print("Annealing Copper 0.15mm:", res["value"])
        assert "0.6%" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 21: Annealing test, Copper, 0.30 mm
        res = await resolve_lookup(db, {
            "test_name": "Annealing test (for copper)",
            "material": "Copper",
            "wire_diameter": 0.30
        })
        print("Annealing Copper 0.30mm:", res["value"])
        assert "13.5%" in res["value"]

        # Test Case 24: Annealing test, Aluminium
        res = await resolve_lookup(db, {
            "test_name": "Annealing test (for copper)",
            "material": "Aluminium"
        })
        print("Annealing Aluminium:", res["value"])
        assert "25 percent" in res["value"] and "12 percent" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 25: HV test, Single-core, Water immersion
        res = await resolve_lookup(db, {
            "test_name": "High voltage test",
            "core_type": "single_core",
            "hv_variant": "water_immersion"
        })
        print("HV Single-core Water Immersion:", res["value"])
        assert "6 kV" in res["value"] and "240 h" in res["value"] and "60±3°C" in res["value"]
        assert len(res["resolution_path"]) >= 2

        # Test Case 26: HV test, Single-core, Room temperature
        res = await resolve_lookup(db, {
            "test_name": "High voltage test",
            "core_type": "single_core",
            "hv_variant": "room_temperature"
        })
        print("HV Single-core Room Temp:", res["value"])
        assert "7.2 kV" in res["value"] and "immersed in water for 1 h" in res["value"]

        # Test Case 27: HV test, Multi-core, Room temperature
        res = await resolve_lookup(db, {
            "test_name": "High voltage test",
            "core_type": "multi_core",
            "hv_variant": "room_temperature"
        })
        print("HV Multi-core Room Temp:", res["value"])
        assert "7.2 kV" in res["value"] and "Ambient" in res["value"] and "immersed" not in res["value"]

        print("\n================ VERIFYING SPLIT TENSILE TESTS ================")
        # Test Case 28: Conductor Tensile, Aluminium Grade 0
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Conductor",
            "material": "Aluminium",
            "conductor_grade": "Grade 0"
        })
        print("Tensile Aluminium Grade 0:", res["value"])
        assert "100 N/mm²" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 29: Conductor Tensile, Aluminium Grade H2
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Conductor",
            "material": "Aluminium",
            "conductor_grade": "Grade H2"
        })
        print("Tensile Aluminium Grade H2:", res["value"])
        assert "150 N/mm²" in res["value"]

        # Test Case 30: Conductor Tensile, Copper (N/A)
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Conductor",
            "material": "Copper"
        })
        print("Tensile Copper:", res["value"])
        assert "N/A" in res["value"]

        # Test Case 31: Insulation Tensile Type A
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Insulation",
            "category": "Type A"
        })
        print("Tensile Insulation Type A:", res["value"])
        assert "12.5 N/mm²" in res["value"] and "150%" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 32: Insulation Tensile Type C
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Insulation",
            "category": "Type C"
        })
        print("Tensile Insulation Type C:", res["value"])
        assert "12.5 N/mm²" in res["value"] and "125%" in res["value"]

        # Test Case 33: Sheath Tensile ST1
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Sheath",
            "category": "ST1"
        })
        print("Tensile Sheath ST1:", res["value"])
        assert "12.5 N/mm²" in res["value"] and "150%" in res["value"]
        assert len(res["resolution_path"]) >= 4

        # Test Case 34: Conductor Resistance formatting and units
        res = await resolve_lookup(db, {
            "test_name": "Conductor resistance test",
            "is_number": "IS 694",
            "class": "Class 5",
            "size_mm2": 2.5,
            "material": "Plain Copper",
            "category": "Cables for indoor installation"
        })
        print("Conductor Resistance format:", res["value"])
        assert "Max. Conductor Resistance:" in res["value"]
        assert "Ω/km" in res["value"]

        # Test Case 35: Conductor Tensile, Aluminium Grade 0 (with material param)
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Conductor",
            "material": "Aluminium",
            "conductor_grade": "Grade 0"
        })
        print("Conductor Tensile Aluminium Grade 0:", res["value"])
        assert "Grade 0" in res["value"]

        # Test Case 36: Type D Insulation Ageing
        res = await resolve_lookup(db, {
            "test_name": "Ageing in air oven",
            "component": "Insulation",
            "category": "Type D",
            "timing": "after"
        })
        print("Type D Insulation Ageing:", res["value"])
        assert "10.0" in res["value"] or "10" in res["value"]

        # Test Case 37: ST3 Sheath Ageing
        res = await resolve_lookup(db, {
            "test_name": "Ageing in air oven",
            "component": "Sheath",
            "category": "ST3",
            "timing": "after"
        })
        print("ST3 Sheath Ageing:", res["value"])
        assert "10.0" in res["value"] and "150%" in res["value"]

        # Test Case 38: Type D Insulation Hot Deformation
        res = await resolve_lookup(db, {
            "test_name": "Hot deformation test",
            "component": "Insulation",
            "category": "Type D"
        })
        print("Type D Hot Deformation:", res["value"])
        assert "80°C" in res["value"]

        # Test Case 39: ST3 Sheath Hot Deformation
        res = await resolve_lookup(db, {
            "test_name": "Hot deformation test",
            "component": "Sheath",
            "category": "ST3"
        })
        print("ST3 Hot Deformation:", res["value"])
        assert "70°C" in res["value"]

        # Test Case 40: Type D Insulation Thermal Stability
        res = await resolve_lookup(db, {
            "test_name": "Thermal stability",
            "component": "Insulation",
            "category": "Type D"
        })
        print("Type D Thermal Stability:", res["value"])
        assert "80 minutes" in res["value"]

        # Test Case 41: ST3 Sheath Thermal Stability
        res = await resolve_lookup(db, {
            "test_name": "Thermal stability",
            "component": "Sheath",
            "category": "ST3"
        })
        print("ST3 Thermal Stability:", res["value"])
        assert "40 minutes" in res["value"]

        # Test Case 42: Type D Insulation unaged tensile
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Insulation",
            "category": "Type D"
        })
        print("Type D unaged tensile:", res["value"])
        assert "10.0 N/mm²" in res["value"] and "150%" in res["value"]

        # Test Case 43: Conductor Tensile Aluminium Grade H4
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Conductor",
            "material": "Aluminium",
            "conductor_grade": "Grade H4"
        })
        print("Conductor Tensile Aluminium Grade H4:", res["value"])
        assert "Grade H4" in res["value"]

        # Test Case 44: Cold bend test (for diameter <= 12.5 mm) with None payload variables (type-safety)
        res = await resolve_lookup(db, {
            "test_name": "Cold bend test (for diameter <= 12.5 mm)",
            "is_number": None,
            "class": None,
            "size_mm2": None,
            "material": None,
            "category": "Type A",
            "hv_method": None,
            "cable_diameter": None,
            "component": "Insulation",
            "timing": None,
            "construction": None,
            "core_type": None,
            "hv_variant": None,
            "cores_count": None,
            "sheathing_status": None,
            "conductor_grade": None,
            "wire_diameter": None
        })
        print("Cold Bend type-safety check:", res["value"])
        assert "-15°C" in res["value"]

        # Test Case 45: Cold Impact test insulation Type B (no longer N/A, -5°C)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Insulation",
            "category": "Type B"
        })
        print("Cold Impact Insulation Type B:", res["value"])
        assert "-5°C" in res["value"]

        # Test Case 46: Cold Impact test insulation Type C (no longer N/A, -5°C)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Insulation",
            "category": "Type C"
        })
        print("Cold Impact Insulation Type C:", res["value"])
        assert "-5°C" in res["value"]

        # Test Case 47: Cold Impact test insulation Type D (-15°C check)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Insulation",
            "category": "Type D"
        })
        print("Cold Impact Insulation Type D:", res["value"])
        assert "-15°C" in res["value"]

        # Test Case 48: Flex test
        res = await resolve_lookup(db, {
            "test_name": "Flex test"
        })
        print("Flex test resolution:", res["value"])
        assert "Clause 10.10" in res["value"] and "Under consideration" in res["value"]

        # Test Case 49: Persulphate test on Plain Copper (N/A check)
        res = await resolve_lookup(db, {
            "test_name": "Persulphate test",
            "material": "Plain Copper"
        })
        print("Persulphate Plain Copper:", res["value"])
        assert "N/A" in res["value"]

        # Test Case 50: Persulphate test on Tinned Copper (Tin Continuity check)
        res = await resolve_lookup(db, {
            "test_name": "Persulphate test",
            "material": "Tinned Copper"
        })
        print("Persulphate Tinned Copper:", res["value"])
        assert "tin coating shall be continuous" in res["value"]

        # Test Case 51: Insulation Resistance test on Sheath (N/A check)
        res = await resolve_lookup(db, {
            "test_name": "Insulation resistance test",
            "component": "Sheath",
            "category": "ST1"
        })
        print("Insulation Resistance Sheath:", res["value"])
        assert "N/A" in res["value"]

        # Test Case 52: Insulation Resistance test on Type D Insulation
        res = await resolve_lookup(db, {
            "test_name": "Insulation resistance test",
            "component": "Insulation",
            "category": "Type D"
        })
        print("Insulation Resistance Type D Insulation:", res["value"])
        assert "3.67 MΩ·km" in res["value"]

        # Test Case 53: High Voltage test prefix check
        res = await resolve_lookup(db, {
            "test_name": "High voltage test",
            "core_type": "single_core",
            "hv_variant": "water_immersion"
        })
        print("High Voltage test output prefix check:", res["value"])
        assert "Min. Test Voltage:" in res["value"]

        # Test Case 54: Spark test prefix check
        res = await resolve_lookup(db, {
            "test_name": "Spark test",
            "size_mm2": 1.5
        })
        print("Spark test output prefix check:", res["value"])
        assert "Min. Spark Test Voltage:" in res["value"]

        # Test Case 55: Thickness test prefix check
        res = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "class": "Class 5",
            "size_mm2": 1.5,
            "construction": "sheathed_multi_core"
        })
        print("Thickness test output prefix check:", res["value"])
        assert "Min. Nominal Insulation Thickness:" in res["value"]

        # Test Case 56: Dropdown options dynamic retrieval check
        opts = await get_dropdown_options(db)
        print("Dropdown test types count:", len(opts["test_types"]))
        assert len(opts["test_types"]) >= 22
        assert "Ageing in air oven" in opts["test_types"]

        # Test Case 57: Cold impact sheath ST1 (-5°C)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Sheath",
            "category": "ST1"
        })
        print("Cold Impact Sheath ST1:", res["value"])
        assert "-5°C" in res["value"]

        # Test Case 58: Cold impact sheath ST2 (-5°C)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Sheath",
            "category": "ST2"
        })
        print("Cold Impact Sheath ST2:", res["value"])
        assert "-5°C" in res["value"]

        # Test Case 59: Cold impact sheath ST3 (-5°C)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Sheath",
            "category": "ST3"
        })
        print("Cold Impact Sheath ST3:", res["value"])
        assert "-5°C" in res["value"]

        # Test Case 60: Cold impact insulation Type B (no more N/A, returns -5°C)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Insulation",
            "category": "Type B"
        })
        print("Cold Impact Insulation Type B:", res["value"])
        assert "-5°C" in res["value"]

        # Test Case 61: Cold impact insulation Type D (-15°C)
        res = await resolve_lookup(db, {
            "test_name": "Cold impact test (for diameter > 12.5 mm)",
            "component": "Insulation",
            "category": "Type D"
        })
        print("Cold Impact Insulation Type D:", res["value"])
        assert "-15°C" in res["value"]

        # Test Case 62: Sheath Tensile ST3 (10.0 N/mm² & 150%)
        res = await resolve_lookup(db, {
            "test_name": "Tensile strength and elongation at break",
            "component": "Sheath",
            "category": "ST3"
        })
        print("Sheath Tensile ST3:", res["value"])
        assert "10.0 N/mm²" in res["value"] and "150%" in res["value"] and "Variation Max: ±20%" in res["value"]

        # Test Case 63: Insulation Resistance Type B (36.7 and 0.37)
        res = await resolve_lookup(db, {
            "test_name": "Insulation resistance test",
            "component": "Insulation",
            "category": "Type B"
        })
        print("Insulation Resistance Type B:", res["value"])
        assert "36.7 MΩ·km" in res["value"] and "0.37 MΩ·km" in res["value"]

        # Test Case 64: Insulation Resistance Type C (36.7 and 0.037)
        res = await resolve_lookup(db, {
            "test_name": "Insulation resistance test",
            "component": "Insulation",
            "category": "Type C"
        })
        print("Insulation Resistance Type C:", res["value"])
        assert "36.7 MΩ·km" in res["value"] and "0.037 MΩ·km" in res["value"]

        # Test Case 65: Hot Deformation limits (Type D insulation: 65%; ST2 sheath: 80°C; ST3 sheath: 70°C and 65%)
        res_d = await resolve_lookup(db, {
            "test_name": "Hot deformation test",
            "component": "Insulation",
            "category": "Type D"
        })
        res_st2 = await resolve_lookup(db, {
            "test_name": "Hot deformation test",
            "component": "Sheath",
            "category": "ST2"
        })
        res_st3 = await resolve_lookup(db, {
            "test_name": "Hot deformation test",
            "component": "Sheath",
            "category": "ST3"
        })
        print("Hot Deformation Type D Insulation:", res_d["value"])
        print("Hot Deformation Sheath ST2:", res_st2["value"])
        print("Hot Deformation Sheath ST3:", res_st3["value"])
        assert "65%" in res_d["value"]
        assert "80°C" in res_st2["value"]
        assert "70°C" in res_st3["value"] and "65%" in res_st3["value"]

        # Test Case 66: Smoke Density Rating check (60% Max.)
        res = await resolve_lookup(db, {
            "test_name": "Test for smoke density rating",
            "category": "FR-LSH"
        })
        print("Smoke Density FR-LSH:", res["value"])
        assert "60% (Max.)" in res["value"]

        # Test Case 67: Shrinkage test Type D Insulation (6%)
        res = await resolve_lookup(db, {
            "test_name": "Shrinkage test",
            "component": "Insulation",
            "category": "Type D"
        })
        print("Shrinkage Type D Insulation:", res["value"])
        assert "Max Shrinkage: 6%" in res["value"]

        # Test Case 68: Shrinkage test ST3 Sheath (6%)
        res = await resolve_lookup(db, {
            "test_name": "Shrinkage test",
            "component": "Sheath",
            "category": "ST3"
        })
        print("Shrinkage ST3 Sheath:", res["value"])
        assert "Max Shrinkage: 6%" in res["value"]

        # Test Case 69: Oxygen Index test units (Min. 29%)
        res = await resolve_lookup(db, {
            "test_name": "Oxygen index test",
            "category": "FR"
        })
        print("Oxygen Index FR:", res["value"])
        assert "Min. 29%" in res["value"]

        # Test Case 70: Thermal Stability ST2 Sheath (80 min)
        res = await resolve_lookup(db, {
            "test_name": "Thermal stability",
            "component": "Sheath",
            "category": "ST2"
        })
        print("Thermal Stability ST2 Sheath:", res["value"])
        assert "80 minutes" in res["value"]

        # Test Case 71: Thermal Stability Type C Insulation (100 min)
        res = await resolve_lookup(db, {
            "test_name": "Thermal stability",
            "component": "Insulation",
            "category": "Type C"
        })
        print("Thermal Stability Type C Insulation:", res["value"])
        assert "100 minutes" in res["value"]

        # Test Case 72: Rigid Unsheathed Insulation Thickness (150 -> 1.8, 300 -> 2.4, 630 -> 3.0)
        res_150_ru = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "unsheathed",
            "class": "Class 2",
            "size_mm2": 150.0
        })
        res_300_ru = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "unsheathed",
            "class": "Class 2",
            "size_mm2": 300.0
        })
        res_630_ru = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "unsheathed",
            "class": "Class 2",
            "size_mm2": 630.0
        })
        print("Rigid Unsheathed Thickness (150 mm²):", res_150_ru["value"])
        print("Rigid Unsheathed Thickness (300 mm²):", res_300_ru["value"])
        print("Rigid Unsheathed Thickness (630 mm²):", res_630_ru["value"])
        assert "1.8 mm" in res_150_ru["value"]
        assert "2.4 mm" in res_300_ru["value"]
        assert "3.0 mm" in res_630_ru["value"]

        # Test Case 73: Flexible Unsheathed Insulation Thickness (150 -> 1.8, 300 -> 2.4)
        res_150_fu = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "unsheathed",
            "class": "Class 5",
            "size_mm2": 150.0
        })
        res_300_fu = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "unsheathed",
            "class": "Class 5",
            "size_mm2": 300.0
        })
        print("Flexible Unsheathed Thickness (150 mm²):", res_150_fu["value"])
        print("Flexible Unsheathed Thickness (300 mm²):", res_300_fu["value"])
        assert "1.8 mm" in res_150_fu["value"]
        assert "2.4 mm" in res_300_fu["value"]

        # Test Case 74: Flexible Sheathed Insulation Thickness (150 -> 1.8, 300 -> 2.4)
        res_150_fs = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "sheathed",
            "class": "Class 5",
            "size_mm2": 150.0
        })
        res_300_fs = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "sheathed",
            "class": "Class 5",
            "size_mm2": 300.0
        })
        print("Flexible Sheathed Thickness (150 mm²):", res_150_fs["value"])
        print("Flexible Sheathed Thickness (300 mm²):", res_300_fs["value"])
        assert "1.8 mm" in res_150_fs["value"]
        assert "2.4 mm" in res_300_fs["value"]

        # Test Case 75: Rigid Sheathed Insulation Thickness (95 -> 1.6)
        res_95_rs = await resolve_lookup(db, {
            "test_name": "Thickness of insulation/sheath",
            "component": "Insulation",
            "sheathing_status": "sheathed",
            "class": "Class 2",
            "size_mm2": 95.0
        })
        print("Rigid Sheathed Thickness (95 mm²):", res_95_rs["value"])
        assert "1.6 mm" in res_95_rs["value"]

        print("\nALL FIXES & SIMPLIFICATIONS SUCCESSFULLY VERIFIED!")

if __name__ == "__main__":
    asyncio.run(main())
