import os
import re
import json
import sqlite3

def resolve_target_address(text):
    """
    Resolves reference texts (e.g., 'IS 8130') to a canonical document_address.
    """
    if not text:
        return None
    normalized = re.sub(r"\s+", "", text).upper()
    if "IS8130" in normalized:
        return "IS8130-1984"
    elif "IS5831" in normalized:
        return "IS5831-1984"
    elif "IS694" in normalized:
        return "IS694-2010"
    return None

def extract_facets(caption_text):
    """
    Deterministic rule-based extractor to pull class, material, and type facets from table captions.
    """
    if not caption_text:
        return {}
    facets = {}
    text_lower = caption_text.lower()
    
    if "copper" in text_lower:
        facets["material"] = "copper"
    elif "aluminium" in text_lower:
        facets["material"] = "aluminium"
        
    for class_num in ["1", "2", "5", "6"]:
        if f"class {class_num}" in text_lower:
            facets["class"] = int(class_num)
            
    for type_letter in ["A", "B", "C", "D"]:
        if f"type {type_letter.lower()}" in text_lower:
            facets["type"] = type_letter.upper()
            
    return facets

def classify_table_type(cells):
    """
    Classifies table_type into reference_index, matrix, or relational based on column headers.
    """
    headers_text = " ".join([c.get("text", "") for c in cells if c.get("column_header")]).lower()
    
    ref_keywords = ["ref to is", "is no", "part no", "clause", "referred standard"]
    if any(kw in headers_text for kw in ref_keywords):
        return "reference_index"
        
    matrix_keywords = ["type a", "type b", "type c", "grade", "class"]
    if any(kw in headers_text for kw in matrix_keywords):
        return "matrix"
        
    return "relational"

def process_table_cells(cells):
    """
    Groups column and row headers to populate col_label and row_label for every cell.
    """
    col_headers = {}
    row_headers = {}
    
    # First pass: identify column and row header cells
    for cell in cells:
        r_start = cell.get("start_row_offset_idx", 0)
        r_end = cell.get("end_row_offset_idx", r_start + 1)
        c_start = cell.get("start_col_offset_idx", 0)
        c_end = cell.get("end_col_offset_idx", c_start + 1)
        text = cell.get("text", "").strip()
        
        if cell.get("column_header"):
            for col in range(c_start, c_end):
                col_headers.setdefault(col, []).append((r_start, text))
        elif cell.get("row_header"):
            for row in range(r_start, r_end):
                row_headers.setdefault(row, []).append((c_start, text))
                
    # Fallback: if no row headers found, treat column 0 as row headers
    if not row_headers:
        for cell in cells:
            if cell.get("start_col_offset_idx") == 0 and not cell.get("column_header"):
                r_start = cell.get("start_row_offset_idx", 0)
                r_end = cell.get("end_row_offset_idx", r_start + 1)
                text = cell.get("text", "").strip()
                for row in range(r_start, r_end):
                    row_headers.setdefault(row, []).append((0, text))
                    
    # Second pass: compute col_label and row_label for every cell
    processed_cells = []
    for cell in cells:
        r_start = cell.get("start_row_offset_idx", 0)
        c_start = cell.get("start_col_offset_idx", 0)
        
        col_list = col_headers.get(c_start, [])
        col_list.sort(key=lambda x: x[0])
        col_label = " > ".join([t for _, t in col_list if t])
        
        row_list = row_headers.get(r_start, [])
        row_list.sort(key=lambda x: x[0])
        row_label = " > ".join([t for _, t in row_list if t])
        
        processed_cells.append({
            "cell": cell,
            "col_label": col_label,
            "row_label": row_label
        })
    return processed_cells

def ingest_document(conn, json_data, metadata):
    """
    Ingests a Docling JSON document into the database schema.
    """
    cursor = conn.cursor()
    
    # 1. Insert into is_documents
    doc_addr = metadata["document_address"]
    cursor.execute("""
        INSERT OR REPLACE INTO is_documents (is_number, revision_label, document_address, valid_from, valid_to, is_current, superseded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        metadata["is_number"],
        metadata["revision_label"],
        doc_addr,
        metadata.get("valid_from"),
        metadata.get("valid_to"),
        metadata.get("is_current", True),
        metadata.get("superseded_by")
    ))
    
    texts = json_data.get("texts", [])
    
    # 2. Insert into clauses_meta and collect prose-based edges
    active_clause = None
    clauses = []
    
    for item in texts:
        label = item.get("label")
        text = item.get("text", "").strip()
        
        if label == "section_header":
            # Attempt to split section number from heading text
            match = re.match(r"^([A-Z]-\d+|\d+(?:\.\d+)*)\s*(.*)$", text)
            if match:
                sec_num, head_text = match.groups()
            else:
                sec_num = ""
                head_text = text
                
            clause_addr = f"{doc_addr}_S{sec_num}" if sec_num else f"{doc_addr}_H{len(clauses)}"
            active_clause = {
                "clause_address": clause_addr,
                "document_address": doc_addr,
                "heading_text": head_text.strip(),
                "section_number": sec_num,
                "body_text": ""
            }
            clauses.append(active_clause)
        elif label == "text":
            if active_clause:
                active_clause["body_text"] += text + "\n"
                
    # Batch insert clauses
    for c in clauses:
        cursor.execute("""
            INSERT OR REPLACE INTO clauses_meta (clause_address, document_address, heading_text, section_number, body_text)
            VALUES (?, ?, ?, ?, ?)
        """, (
            c["clause_address"],
            c["document_address"],
            c["heading_text"],
            c["section_number"],
            c["body_text"].strip()
        ))
        
        # Prose-based reference detection (Mechanism B)
        # Search body text for "IS <number>" pattern
        citations = re.findall(r"IS\s*(\d+)", c["body_text"])
        for cit in set(citations):
            target_addr = resolve_target_address(f"IS {cit}")
            if target_addr:
                cursor.execute("""
                    INSERT INTO edges (source_address, target_address, target_facets, edge_type)
                    VALUES (?, ?, ?, ?)
                """, (
                    c["clause_address"],
                    target_addr,
                    None,
                    "clause_reference"
                ))

    # Helper to resolve caption references
    def resolve_caption(table_item):
        caption_parts = []
        for cap_ref in table_item.get("captions", []):
            ref_str = cap_ref.get("$ref", "")
            if ref_str.startswith("#/texts/"):
                try:
                    idx = int(ref_str.split("/")[-1])
                    caption_parts.append(texts[idx].get("text", "").strip())
                except (ValueError, IndexError):
                    pass
        return " ".join(caption_parts) if caption_parts else None

    # 3. Insert tables_meta, table_cells, and column-based edges (Mechanism A)
    for t_idx, table in enumerate(json_data.get("tables", []), start=1):
        table_addr = f"{doc_addr}_T{t_idx}"
        caption_text = resolve_caption(table)
        
        cells = table.get("data", {}).get("table_cells", [])
        table_type = classify_table_type(cells)
        facets = extract_facets(caption_text)
        
        # Insert table metadata
        cursor.execute("""
            INSERT OR REPLACE INTO tables_meta (table_address, document_address, caption_text, table_type, facets, search_vector)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            table_addr,
            doc_addr,
            caption_text,
            table_type,
            json.dumps(facets),
            None  # search_vector is tsvector in Postgres
        ))
        
        # Process and insert table cells
        processed_cells = process_table_cells(cells)
        for p_cell in processed_cells:
            cell = p_cell["cell"]
            r = cell.get("start_row_offset_idx", 0)
            c = cell.get("start_col_offset_idx", 0)
            cell_addr = f"{table_addr}_R{r}_C{c}"
            
            cursor.execute("""
                INSERT OR REPLACE INTO table_cells (cell_address, table_address, row_label, col_label, value, bbox, confidence, page, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cell_addr,
                table_addr,
                p_cell["row_label"],
                p_cell["col_label"],
                cell.get("text", "").strip(),
                json.dumps(cell.get("bbox", {})),
                cell.get("confidence"),
                cell.get("page_no"),
                "OCR"
            ))
            
            # Column-based reference detection (Mechanism A)
            # If the column label or header indicates a reference, map it
            col_label_lower = p_cell["col_label"].lower()
            if any(kw in col_label_lower for kw in ["ref to is", "is no", "part no", "clause"]):
                val = cell.get("text", "").strip()
                target_addr = resolve_target_address(val)
                if target_addr:
                    cursor.execute("""
                        INSERT INTO edges (source_address, target_address, target_facets, edge_type)
                        VALUES (?, ?, ?, ?)
                    """, (
                        cell_addr,
                        target_addr,
                        None,
                        "column_reference"
                    ))
                    
    conn.commit()
