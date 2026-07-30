import sqlite3

def run_empirical_test():
    print("======================================================================")
    print("EMPIRICAL TEST: CAN THICKNESS BE RESOLVED WITH ONLY CLASS AND SIZE?")
    print("======================================================================")
    
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    # We will query Table 11, Table 12, Table 13, Table 15 for Class 2 / 5 and Size 1.5 / 2.5
    queries = [
        {
            "class": "Class 2",
            "size": 1.5,
            "table_address": "IS694-2010_T11",
            "desc": "Unsheathed cables (Class 1 or 2)"
        },
        {
            "class": "Class 2",
            "size": 1.5,
            "table_address": "IS694-2010_T13",
            "desc": "Sheathed cables (Class 1 or 2)"
        },
        {
            "class": "Class 5",
            "size": 1.5,
            "table_address": "IS694-2010_T12",
            "desc": "Unsheathed flexible cables (Class 5)"
        },
        {
            "class": "Class 5",
            "size": 1.5,
            "table_address": "IS694-2010_T15",
            "desc": "Sheathed flexible cables (Class 5)"
        }
    ]
    
    for q in queries:
        cursor.execute(
            "SELECT cell_address, row_label, col_label, value FROM table_cells WHERE table_address = ? AND value LIKE '%1.5%'",
            (q["table_address"],)
        )
        rows = cursor.fetchall()
        print(f"\n--- {q['desc']} ({q['table_address']}) ---")
        if not rows:
            print("No matching rows for size 1.5")
            continue
            
        # Let's find cells in the same row representing insulation thickness
        for r in rows:
            cell_addr = r[0]
            row_idx = cell_addr.split('_R')[1].split('_C')[0]
            cursor.execute(
                "SELECT col_label, value FROM table_cells WHERE table_address = ? AND cell_address LIKE ?",
                (q["table_address"], f"%_R{row_idx}_%")
            )
            cells = cursor.fetchall()
            print(f"Row {row_idx}:")
            for c in cells:
                col_lbl = c[0]
                val = c[1]
                if "Thickness of Insulation" in col_lbl or "Nominal Thickness of Insulation" in col_lbl or "Thickness" in col_lbl:
                    print(f"  Col: '{col_lbl}' -> Value: '{val}'")
                    
    conn.close()

if __name__ == "__main__":
    run_empirical_test()
