from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Global variables for model
tokenizer = None
model = None

def load_model():
    """Load model and tokenizer ONCE. Call this during startup."""
    global tokenizer, model
    if tokenizer is None or model is None:
        print("[INFO] Loading FLAN-T5 Base model (this takes ~60 seconds)...")
        model_name = "google/flan-t5-base"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        print("[OK] FLAN-T5 Base model loaded successfully")
    return tokenizer, model

def generate_flan_sentence(prompt: str, fallback: str) -> str:
    """
    Generate a sentence using FLAN-T5 model with quality checks.
    
    Parameters:
        prompt: Input prompt for the model
        fallback: String to return if generation fails quality checks
    
    Returns:
        Generated text or fallback string
    """
    global tokenizer, model
    
    # Ensure model is loaded
    if tokenizer is None or model is None:
        load_model()
    
    try:
        # Truncate input to max 180 tokens
        inputs = tokenizer(prompt, return_tensors="pt", max_length=180, truncation=True)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=80,
                temperature=0.7,
                do_sample=True,
                no_repeat_ngram_size=3,
                repetition_penalty=1.3
            )
        
        output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"[DEBUG] AI generated: {output_text[:100]}...")  # Log first 100 chars
        
        # Quality checks - return fallback if any check fails
        output_lower = output_text.lower()
        
        # Check 1: Output is under 40 characters (too short to be useful)
        if len(output_text) < 40:
            return fallback
        
        # Check 2: Output text appears inside the prompt (echo detection)
        if output_lower in prompt.lower():
            return fallback
        
        # Check 3: Output ends with a question mark
        if output_text.strip().endswith("?"):
            return fallback
        
        # Check 4: Contains impersonal references (should address "you" not "they/team/staff")
        # Only reject if it's clearly impersonal (not just containing the word)
        impersonal_phrases = ["the staff member", "the team should", "the manager", "the employee", "they should", "he should", "she should"]
        if any(phrase in output_lower for phrase in impersonal_phrases):
            return fallback
        
        # Check 5: Output is too generic (contains only generic filler phrases without substance)
        # Only reject if it's overly generic - allow some generic phrases if there's substance
        overly_generic_phrases = [
            "well done keep up",
            "great job keep it up",
            "good job continue",
            "nice work keep going"
        ]
        if any(phrase in output_lower for phrase in overly_generic_phrases):
            return fallback
        
        # Check 6: Must be substantive (not just a single generic phrase)
        # Check if output has meaningful content beyond just generic praise
        meaningful_indicators = [
            "focus", "try", "consider", "aim", "work on", "improve", "build", "develop", 
            "prioritize", "start", "continue", "maintain", "adjust", "help", "support",
            "opportunity", "challenge", "situation", "pattern", "effort", "attention",
            "momentum", "foundation", "discipline", "habits", "pace", "energy"
        ]
        if not any(word in output_lower for word in meaningful_indicators):
            print(f"[DEBUG] AI output rejected: missing meaningful indicators")
            return fallback
        
        print(f"[DEBUG] AI output accepted: {output_text}")
        return output_text
    
    except Exception as e:
        # Print error and return fallback
        print(f"[ERROR] Error in generate_flan_sentence: {str(e)}")
        return fallback
