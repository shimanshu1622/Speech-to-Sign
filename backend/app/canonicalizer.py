import os
import re
from typing import List, Set, Dict
from difflib import get_close_matches

class ASLLVDCanonicalizer:
    def __init__(self, words_dir: str):
        self.exact_glosses: Set[str] = set()
        
        # Maps base English word -> List of actual ASLLVD glosses
        # Example: "WORK" -> ["WORK-1", "WORK-2", "WORK-3"]
        self.base_to_gloss: Dict[str, List[str]] = {}
        
        self._load_and_index_asllvd(words_dir)

    def _load_and_index_asllvd(self, words_dir: str):
        # Expanded to catch Classifiers (CL:), Locatives, Arcs, and variants
        prefixes_to_strip = r"^(NS-|FS-|IX-[a-zA-Z0-9]+-|IX-|POSS-[a-zA-Z0-9]+-|POSS-|CL:[a-zA-Z0-9]+-|#)"
        
        for fname in os.listdir(words_dir):
            if not fname.lower().endswith((".mp4", ".mov", ".mkv")):
                continue
                
            raw_gloss = os.path.splitext(fname)[0].upper()
            self.exact_glosses.add(raw_gloss)
            
            # Clean prefixes
            clean_base = re.sub(prefixes_to_strip, "", raw_gloss)
            # Clean trailing variant numbers (e.g., "-1", "-2")
            clean_base = re.sub(r"-\d+$", "", clean_base) 
            
            if clean_base:
                self.base_to_gloss.setdefault(clean_base, []).append(raw_gloss)

    def canonicalize(self, tokens: List[str]) -> List[str]:
        out: List[str] = []
        i = 0
        
        while i < len(tokens):
            t = tokens[i].strip().upper()
            if not t:
                i += 1
                continue

            # 1. Bigram Lookahead (Multi-word gloss detection)
            if i + 1 < len(tokens):
                next_t = tokens[i+1].strip().upper()
                combined = f"{t}-{next_t}"
                
                # Check if the combined word exists in exact glosses or base index
                if combined in self.exact_glosses:
                    out.append(combined)
                    i += 2
                    continue
                elif combined in self.base_to_gloss:
                    out.append(self.base_to_gloss[combined][0]) # Pick first variant
                    i += 2
                    continue

            # 2. Exact Match Check
            if t in self.exact_glosses:
                out.append(t)
                i += 1
                continue

            # 3. Base Word Check
            if t in self.base_to_gloss:
                out.append(self.base_to_gloss[t][0]) # Pick first variant
                i += 1
                continue

            # 4. Typo Correction on Base Words
            match = self._closest_base_match(t)
            if match:
                out.append(self.base_to_gloss[match][0])
                i += 1
                continue

            # 5. Dataset-Aware Fingerspelling Fallback
            out.extend(self._fingerspell_word(t))
            i += 1

        return out

    def _closest_base_match(self, token: str) -> str | None:
        matches = get_close_matches(
            token,
            self.base_to_gloss.keys(),
            n=1,
            cutoff=0.85 
        )
        return matches[0] if matches else None

    def _fingerspell_word(self, word: str) -> List[str]:
        spelled = []
        for char in word:
            if char.isalpha():
                # Check if the character exists as a base in the dataset
                if char in self.base_to_gloss:
                    spelled.append(self.base_to_gloss[char][0])
                # If the letter genuinely doesn't exist in the dataset, skip it 
                # (prevents crashing during the stitching phase)
        return spelled