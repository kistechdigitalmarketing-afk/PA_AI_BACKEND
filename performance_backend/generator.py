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
        impersonal_words = ["staff member", "the team", "the manager", "the employee", "they ", "he ", "she "]
        if any(word in output_lower for word in impersonal_words):
            return fallback
        
        # Check 5: Output just states the score (not coaching)
        if "scored" in output_lower or "score" in output_lower:
            return fallback
        
        # Check 6: Output is too generic (contains common filler phrases)
        generic_phrases = [
            "overall performance",
            "solid performance", 
            "good performance",
            "great contribution",
            "very good",
            "had been",
            "the coach",
            "well done",
            "keep up",
            "great job",
            "good job",
            "nice work",
            "made a",
            "has made",
            "have made"
        ]
        if any(phrase in output_lower for phrase in generic_phrases):
            return fallback
        
        # Check 7: Must contain actionable/coaching language
        coaching_indicators = ["focus", "try", "consider", "aim", "work on", "improve", "build", "develop", "prioritize", "start", "continue", "maintain"]
        if not any(word in output_lower for word in coaching_indicators):
            return fallback
        
        return output_text
    
    except Exception as e:
        # Print error and return fallback
        print(f"[ERROR] Error in generate_flan_sentence: {str(e)}")
        return fallback
