import sqlite3
import json
import re

def get_cell_for_col(cells_list, cat_lower):
    # Map category inputs to OCR column label patterns
    patterns = [cat_lower]
    if "type a" in cat_lower:
        patterns.extend(["l a", "type a", "type 1", "indoor"])
    elif "type b" in cat_lower:
        patterns.extend(["type of insulation > b", "type b"])
    elif "type c" in cat_lower:
        patterns.extend(["type c", "type 2", "outdoor"])
    elif "type d" in cat_lower:
        patterns.extend(["type d", "type of insulation > d", "type o! insulatlon d"])
    elif "st1" in cat_lower or "st 1" in cat_lower:
        patterns.extend(["st1", "st 1"])
    elif "st2" in cat_lower or "st 2" in cat_lower:
        patterns.extend(["st2", "st 2"])
        
    print("Patterns:", patterns)
    # Try matching column pattern first
    for c in cells_list:
        col_lbl = (c[2] or "").lower()
        last_lbl = col_lbl.split(">")[-1].strip()
        print(f"Cell {c[0]} col_lbl='{col_lbl}' last_lbl='{last_lbl}'")
        if last_lbl in ["test", "unit", "method of test", "si ng.", "sl no."] or "method" in last_lbl:
            print("  Skipped due to last_lbl/method")
            continue
        if any(p in col_lbl for p in patterns):
            print(f"  Matched in Loop 1: {c[0]} with value {c[3]}")
            return c
            
    # Fallback to general category matching conditions
    for c in cells_list:
        col_lbl = (c[2] or "").lower()
        last_lbl = col_lbl.split(">")[-1].strip()
        if last_lbl in ["test", "unit", "method of test", "si ng.", "sl no."] or "method" in last_lbl:
            continue
        if "fr-lsh" in cat_lower and "fr-lsh" in col_lbl:
            print(f"  Matched in Loop 2 (fr-lsh): {c[0]}")
            return c
        elif "fr" in cat_lower and "fr" in col_lbl and "fr-lsh" not in col_lbl:
            print(f"  Matched in Loop 2 (fr): {c[0]}")
            return c
        elif "indoor" in cat_lower and ("indoor" in col_lbl or "type a" in col_lbl or "type d" in col_lbl or "type 1" in col_lbl or "type o! insulatlon d" in col_lbl or "l a" in col_lbl or "type of insulation > b" in col_lbl):
            print(f"  Matched in Loop 2 (indoor): {c[0]}")
            return c
        elif "outdoor" in cat_lower and ("outdoor" in col_lbl or "type c" in col_lbl or "type 2" in col_lbl):
            print(f"  Matched in Loop 2 (outdoor): {c[0]}")
            return c
            
    # General fallback
    for c in cells_list:
        col_lbl = (c[2] or "").lower()
        last_lbl = col_lbl.split(">")[-1].strip()
        if last_lbl in ["test", "unit", "method of test", "si ng.", "sl no."] or "method" in last_lbl:
            continue
        if c[3]:
            print(f"  Matched in Loop 3 (fallback): {c[0]} with value {c[3]}")
            return c
    return None

def trace():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address = 'IS5831-1984_T4' AND cell_address LIKE '%_R5_%'
    """)
    cells = cursor.fetchall()
    get_cell_for_col(cells, "type a")
    conn.close()

if __name__ == "__main__":
    trace()
