import timeit
import sys
import loguru
from plsql_analyzer.utils.code_cleaner import clean_code_and_map_literals

# Configure logger to be silent
logger = loguru.logger
logger.remove()
# Add a sink that discards everything
logger.add(lambda msg: None, level="CRITICAL")

def benchmark():
    # Construct a large PL/SQL string
    # Include patterns that trigger the inefficiency:
    # - comments (inline --)
    # - comments (block /* */)
    # - literals
    # - normal code

    base_block = """
    /* This is a block comment
       spanning multiple lines */
    PROCEDURE test_proc(p_val IN VARCHAR2) IS
      v_temp VARCHAR2(100);
    BEGIN
      -- This is an inline comment
      v_temp := 'Some literal string';
      v_temp := 'Another ' || 'concatenation';
      IF v_temp LIKE '%foo%' THEN
         dbms_output.put_line('Found it');
      END IF;
    END;
    """

    # Repeat it many times to get a measurable duration
    # 2000 iterations creates a decently large file (~500KB)
    code = base_block * 2000

    print(f"Benchmarking with code length: {len(code)} chars")

    # Run once to warm up
    clean_code_and_map_literals(code, logger)

    # Measure
    iterations = 20
    start_time = timeit.default_timer()
    for _ in range(iterations):
        clean_code_and_map_literals(code, logger)
    end_time = timeit.default_timer()

    total_time = end_time - start_time
    avg_time = total_time / iterations

    print(f"Total time for {iterations} iterations: {total_time:.4f} s")
    print(f"Average time per iteration: {avg_time:.4f} s")

if __name__ == "__main__":
    benchmark()
