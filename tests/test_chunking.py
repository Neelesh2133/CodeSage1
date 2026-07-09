import random
import pytest
from app.chunking import chunk_units, MAX_CHUNK_CHARS

def test_chunk_units_empty_input():
    """Verify that empty input returns an empty list of chunks."""
    assert chunk_units([]) == []

def test_chunk_units_single_unit_smaller_than_limit():
    """Verify that a single unit smaller than the limit is placed in a single chunk intact."""
    content = "print('hello world')"
    result = chunk_units([("test.py", content)])
    assert result == [[("test.py", content)]]

def test_chunk_units_single_unit_larger_than_limit():
    """Verify that a single unit larger than the limit is split into labeled sub-parts."""
    # Create content that is larger than MAX_CHUNK_CHARS
    # MAX_CHUNK_CHARS is 32000, so 40000 characters will exceed it
    content = "a\n" * 20000  # 40000 characters
    result = chunk_units([("large_file.py", content)])
    
    # It must be split into at least 2 chunks (each chunk containing one part of the file)
    # Wait, because it is a single file split into parts, let's see how chunk_units handles it:
    # 1. _split_large_unit splits it into "large_file.py (part 1)" and "large_file.py (part 2)"
    # 2. Since each part's length is under MAX_CHUNK_CHARS, they are placed in separate chunks (or the same chunk if they fit, but here part 1 is already close to MAX_CHUNK_CHARS, so they will be in separate chunks).
    assert len(result) >= 2
    
    # Reconstruct the parts and verify they match the original content
    reconstructed = ""
    part_labels = []
    for chunk in result:
        for label, text in chunk:
            part_labels.append(label)
            reconstructed += text
            
    assert reconstructed == content
    assert "large_file.py (part 1)" in part_labels
    assert "large_file.py (part 2)" in part_labels

def test_chunk_units_many_small_units_exceed_limit():
    """Verify that many small units exceeding the limit are grouped into multiple chunks."""
    # Generate 40 small files of 1000 characters each
    # Total characters: 40,000 (> 32,000 MAX_CHUNK_CHARS)
    units = [(f"file_{i}.py", "a" * 1000) for i in range(40)]
    
    result = chunk_units(units)
    
    # Should be grouped into exactly 2 chunks
    assert len(result) == 2
    
    # No chunk should exceed MAX_CHUNK_CHARS
    for idx, chunk in enumerate(result):
        chunk_len = sum(len(text) for _, text in chunk)
        assert chunk_len <= MAX_CHUNK_CHARS, f"Chunk {idx} exceeds MAX_CHUNK_CHARS: {chunk_len}"

def test_chunk_units_limits_and_preservation():
    """Fuzz/randomized test covering 25 files of varying sizes to verify limits & preservation."""
    random.seed(42)  # For reproducibility
    fake_units = []
    original_contents = {}
    
    # We will vary sizes from 100 chars to 80,000 chars
    for i in range(25):
        filename = f"file_{i}.py"
        # Varying sizes: large (40000-80000), medium (5000-15000), small (100-1000)
        if i % 5 == 0:
            size = random.randint(40000, 80000)
        elif i % 2 == 0:
            size = random.randint(5000, 15000)
        else:
            size = random.randint(100, 1000)
            
        content = f"# Start of file {filename}\n"
        content += "".join(random.choice("abcdefghijklmnopqrstuvwxyz \n") for _ in range(size))
        content += f"\n# End of file {filename}"
        
        fake_units.append((filename, content))
        original_contents[filename] = content
        
    # Run the chunker
    chunks = chunk_units(fake_units)
    
    # Assertions:
    assert len(chunks) > 0
    
    # Track reconstructed content per original filename
    reconstructed_contents = {filename: [] for filename, _ in fake_units}
    
    for idx, chunk in enumerate(chunks):
        # Sum of text lengths in each chunk must not exceed MAX_CHUNK_CHARS
        chunk_chars_sum = sum(len(text) for _, text in chunk)
        assert chunk_chars_sum <= MAX_CHUNK_CHARS, f"Chunk {idx} exceeds MAX_CHUNK_CHARS: {chunk_chars_sum}"
        
        for label, text in chunk:
            # Extract the original filename from the label (could be e.g. "file_0.py (part 1)")
            orig_filename = label.split(" (part")[0]
            assert orig_filename in reconstructed_contents, f"Unexpected filename key in chunk label: {label}"
            reconstructed_contents[orig_filename].append(text)
            
    # Assert that all original content is preserved exactly across chunks
    for filename, original_content in fake_units:
        reconstructed = "".join(reconstructed_contents[filename])
        assert reconstructed == original_content, f"Content mismatch for {filename}!"
