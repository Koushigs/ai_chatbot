from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "mistralai/Mistral-7B-Instruct-v0.2"

try:
    print("Testing tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=False)
    print("Tokenizer: OK")

    print("Testing model...")
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=False)
    print("Model: OK")

    print("="*40)
    print("Mistral 7B is installed and ready!")
    print("="*40)
except Exception as e:
    print("="*40)
    print("Mistral 7B is NOT installed or not usable.")
    print("Error was:", str(e))
    print("="*40)
