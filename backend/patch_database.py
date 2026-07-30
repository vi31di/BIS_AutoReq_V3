import sqlite3
import json

def patch():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    # 1. Update IS 8130 table metadata
    patches_8130 = {
        "IS8130-1984_T5": ("TABLE 1 SOLID CONDUCTORS FOR SINGLE-CORE AND MULTI-CORE CABLES, CLASS 1", {"class": 1, "material": "copper"}),
        "IS8130-1984_T6": ("STRANDED CONDUCTORS FOR SINGLR-CORI AND MULTI-CORE CABLRS, CLASS 2 ( Clauses 5.2.3, 5.3.3 and 6.3.1)", {"class": 2, "material": "copper"}),
        "IS8130-1984_T7": ("TABLE 3 FLEXIBLE COPPER CONDUCTORS FOR SINGLE-CORE AND MULTI-CORE CABLES, CLASS 5", {"class": 5, "material": "copper"}),
        "IS8130-1984_T8": ("TABLE 4 FLEXIBLE COPPER CONDUCTORS FOR SINGLE-CORE AND MULTI-CORE CABLES, CLASS 6", {"class": 6, "material": "copper"}),
        "IS8130-1984_T9": ("TABLE 5 FLEXIBLE ALUMINIUM CONDUCTORS FOR WELDING CABLES", {"material": "aluminium"}),
        "IS8130-1984_T10": ("TABLE 6 TEMPERATURE CORRECTION FACTORS k, FOR CONDUCTOR RESISTANCE", {})
    }
    
    for t_addr, (caption, facets) in patches_8130.items():
        cursor.execute(
            "UPDATE tables_meta SET caption_text = ?, facets = ? WHERE table_address = ?",
            (caption, json.dumps(facets), t_addr)
        )
        
    # 2. Add missing edges if any
    cursor.execute("INSERT OR IGNORE INTO edges (source_address, target_address, target_facets, edge_type) VALUES (?, ?, ?, ?)",
                   ("IS694-2010_S4.2", "IS8130-1984", None, "clause_reference"))
                   
    conn.commit()
    conn.close()
    print("Database patched successfully!")

if __name__ == "__main__":
    patch()
