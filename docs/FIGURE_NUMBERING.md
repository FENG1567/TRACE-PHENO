# Current figure numbering

The current publication package contains four main figures, four supplementary figures and one graphical abstract. Existing layouts and source-data filenames are retained where they remain useful; the export stems and manuscript-facing numbers follow this map.

| Previous export/layout | Current publication export |
|---|---|
| `Figure_1_Study_Design` | `Figure_1_Study_Design` (Figure 1) |
| `Figure_2_Construct_and_Reference` | `Supplementary_Figure_1_Construct_and_Reference` (Supplementary Figure 1) |
| `Figure_3_Conditional_Agreement` | `Figure_2_Conditional_Agreement` (Figure 2) |
| `Figure_4_Transportability` | `Figure_3_Transportability` (Figure 3) |
| `Figure_5_Downstream_Consequences` | `Figure_4_Downstream_Consequences` (Figure 4) |
| `Figure_6_Generic_Framework` | `Supplementary_Figure_4_Generic_Framework` (Supplementary Figure 4) |
| `Supplementary_Figure_1_Label_Policy_Sensitivity` | `Supplementary_Figure_2_Label_Policy_Sensitivity` (Supplementary Figure 2) |
| `Supplementary_Figure_2_P3_P4_Rule_Concordance` | `Supplementary_Figure_3_P3_P4_Rule_Concordance` (Supplementary Figure 3) |
| `Graphical_Abstract` | `Graphical_Abstract` |

The current build dispatcher writes the four main figures, four supplementary figures and graphical abstract using the existing Python layouts. Two supplementary title lines now display their current numbers. Their source values, panels and layout styling are unchanged; only those title lines required regenerated exports. All other frozen export files were renamed with their original bytes.

Input filenames such as `Figure_5_Burden.csv` remain stable source-data identifiers used by the builders and result registry; they are not current publication export numbers.
