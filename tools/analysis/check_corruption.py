
file_path = ".github/workflows/ci.yml"
try:
    with open(file_path, "rb") as f:
        content = f.read()
        if b"\0" in content:
            print(f"Found null bytes in {file_path}")
        else:
            print(f"No null bytes in {file_path}")
            
        # Check for other non-printable chars (excluding newlines, tabs)
        non_printable = [b for b in content if b < 32 and b not in (9, 10, 13)]
        if non_printable:
            print(f"Found {len(non_printable)} non-printable characters: {non_printable[:10]}")
        else:
            print("No non-printable characters found.")
            
except Exception as e:
    print(f"Error checking file: {e}")
