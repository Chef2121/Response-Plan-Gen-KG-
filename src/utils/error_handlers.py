"""Error handling utilities."""


def custom_parsing_error_handler(error):
    """Custom handler to see what the LLM actually outputs"""
    print("=" * 50)
    print("PARSING ERROR DETECTED!")
    print("Error message:", str(error))
    print("=" * 50)
    
    # Try to extract the actual LLM output from the error
    error_str = str(error)
    if "Could not parse LLM output:" in error_str:
        # Extract the actual output
        start_idx = error_str.find("Could not parse LLM output:") + len("Could not parse LLM output:")
        end_idx = error_str.find("For troubleshooting")
        if end_idx == -1:
            actual_output = error_str[start_idx:].strip()
        else:
            actual_output = error_str[start_idx:end_idx].strip()
        
        print("ACTUAL LLM OUTPUT:")
        print(actual_output)
        print("=" * 50)
        
        # Return a formatted response
        return f"LLM tried to use tool but format was wrong. Raw output: {actual_output}"
    
    return f"Parsing error: {error}"
