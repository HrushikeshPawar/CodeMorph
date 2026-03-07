import time
import re
from plsql_analyzer.parsing.structural_parser import END_CHECK_REGEX

def benchmark():
    processed_line = "END; IF condition THEN NULL; END IF; LOOP NULL; END LOOP; END;"
    iterations = 1_000_000

    # Baseline: Current implementation
    start_time = time.time()
    for _ in range(iterations):
        if END_CHECK_REGEX.search(processed_line):
            ends_found = len(END_CHECK_REGEX.findall(processed_line))
            count = 0
            for _ in range(ends_found):
                count += 1
    baseline_duration = time.time() - start_time
    print(f"Baseline duration: {baseline_duration:.4f}s")

    # Optimized: Save findall result
    start_time = time.time()
    for _ in range(iterations):
        ends = END_CHECK_REGEX.findall(processed_line)
        if ends:
            ends_found = len(ends)
            count = 0
            for _ in range(ends_found):
                count += 1
    optimized_duration = time.time() - start_time
    print(f"Optimized duration: {optimized_duration:.4f}s")

    improvement = (baseline_duration - optimized_duration) / baseline_duration * 100
    print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    benchmark()
