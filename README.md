# IS Compliance Lookup System

An automated system for finding exact wire-testing compliance values across
cross-referencing Indian Standards (IS) documents, built for BIS
laboratory use.

---

## What This Is

A wire's compliance value — say, the maximum resistance for a Class 2,
2.5mm² conductor — is rarely stated in one place. IS 694 often just points
to another standard (like IS 8130), which may point further still, before
the actual number appears. Today this is checked by hand: opening several
PDFs and matching tables by eye.

This system automates that chain-following. Given a wire's specs and the
test required, it follows the reference chain across documents automatically
and returns the exact value — along with the full trail it took to get
there, so the answer can always be checked against the source.

**The core rule the system never breaks: the final number always comes from
a direct, verified read of the standard itself — never an AI's guess.** 
the value itself is always a plain, deterministic lookup, fully
traceable back to its source clause and table.

The system also tracks which version of each standard is current. If a
standard is revised, any answer depending on the older version is flagged
for re-verification rather than served as if nothing changed.

---

## Technical Summary

**Design principle**: use AI only where language understanding is
genuinely required; keep every value-producing step deterministic.

| Task | Method | Why |
|---|---|---|
| Input the query | Drop Down Menu Choice Selection | Exact match as IS language for Accuracy |
| Finding the right table/clause | Lexical search (BM25F) | Matches or beats neural search on this kind of controlled-vocabulary document set |
| Retrieving the exact value | Direct database lookup | Published research on AI table-reading (e.g. Google's TAPAS) shows materially lower accuracy on numbers than on text |
| Detecting cross-references | Rule-based pattern matching, AI fallback only for ambiguous cases | Mirrors production regulatory-compliance systems |
| Tracking revisions | Explicit version metadata, checked before any cached answer is trusted | Generic AI retrieval is documented to frequently miss that a reference has been superseded |

**Validation  and Testing**: since the space of standards and test parameters
is finite, the system is tested **exhaustively, not by sampling**:
- Every extracted table cell is checked for type validity, known OCR-error
  patterns, statistical outliers, and (for conductor tables) the physical
  law that resistance must fall as size rises
- Every possible query the system could receive is run and cross-checked
  against an independently built reference calculation
- Fixes target the underlying rule causing a class of errors, not
  individual cases, and every fix is re-verified against the full suite

**Alignment**: the system's audit and failure-logging design directly
supports ISO/IEC 17025's requirement (administered in India via NABL) that
a lab data system maintain a record of failures and corrective actions.

**Current scope**: validated against IS 694, 8130, 5831, and related
cross-referenced standards; each newly added standard goes through the same
audit before being trusted. Uncertain results are flagged for
re-verification rather than returned with false confidence.
