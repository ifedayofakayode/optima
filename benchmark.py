import timeit
import hashlib
from core.pdf_reader import extract_text_from_pdf
from core.safety import looks_like_injection

# Benchmark 1: PDF Text Extraction
def benchmark_pdf_extraction():
    # You'll need a test PDF file for this
    test_pdf_path = "test_resume.pdf"  # Replace with your test file
    
    with open(test_pdf_path, "rb") as f:
        file = f.read()
    
    # Create a mock file object
    class MockFile:
        def __init__(self, content):
            self.content = content
        def read(self):
            return self.content
    
    mock_file = MockFile(file)
    
    # Time the extraction
    time_taken = timeit.timeit(
        lambda: extract_text_from_pdf(mock_file),
        number=1
    )
    
    print(f"PDF extraction took: {time_taken:.3f} seconds")

# Benchmark 2: Cache Key Generation
def benchmark_cache_key():
    # Simulate a large resume and job description
    large_resume = "Sample text " * 100000  # ~1.3MB
    jd_input = "Job description " * 1000   # ~18KB
    
    # Old method
    def old_method():
        return hashlib.sha256((large_resume + "||" + jd_input).encode()).hexdigest()
    
    # New method
    def new_method():
        resume_hash = hashlib.sha256(large_resume.encode()).hexdigest()
        jd_hash = hashlib.sha256(jd_input.encode()).hexdigest()
        return hashlib.sha256(f"{resume_hash}||{jd_hash}".encode()).hexdigest()
    
    old_time = timeit.timeit(old_method, number=10)
    new_time = timeit.timeit(new_method, number=10)
    
    print(f"Old cache key method: {old_time:.3f} seconds (10 runs)")
    print(f"New cache key method: {new_time:.3f} seconds (10 runs)")
    print(f"Improvement: {((old_time - new_time) / old_time * 100):.1f}% faster")

# Benchmark 3: Prompt Injection Detection
def benchmark_injection_detection():
    # Simulate a large text
    large_text = "This is a resume. " * 10000
    
    time_taken = timeit.timeit(
        lambda: looks_like_injection(large_text),
        number=100
    )
    
    print(f"Injection detection took: {time_taken:.3f} seconds (100 runs)")

if __name__ == "__main__":
    print("=== Performance Benchmarks ===\n")
    
    print("Benchmark 1: PDF Extraction")
    benchmark_pdf_extraction()
    print()
    
    print("Benchmark 2: Cache Key Generation")
    benchmark_cache_key()
    print()
    
    print("Benchmark 3: Injection Detection")
    benchmark_injection_detection()