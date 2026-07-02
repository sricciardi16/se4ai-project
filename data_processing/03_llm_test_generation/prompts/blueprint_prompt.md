Excellent. Now that we have the Core Essential Public API Contract, I need you to shift your role. You are a **Lead Product Architect**.

Your task is to translate the contract you just wrote into a definitive **Behavioral Specification Blueprint**. If the documentation and the code were deleted tomorrow, this blueprint must serve as the absolute "Source of Truth" for what this library accomplishes.

You will extract a list of "Public Guarantees." A guarantee is a strict, observable rule about how the library behaves from a pure black-box perspective.

**CRITICAL RULES - YOU MUST OBEY THESE STRICTLY:**

1. **Core Scope Only:** You must restrict yourself ONLY to the core features you defined in your previous response. Do not invent features, and do not include obscure edge cases that are not part of the primary workflow.
2. **Absolute Black-Box:** You are forbidden from using function names, class names, variable names, or Python code. Do not write `slugify()` or `jwt.decode()`. Describe the *concept* and the *behavior*, not the implementation.
3. **Cause and Effect:** Every single guarantee must describe a specific input/scenario and the guaranteed outcome. (e.g., "Converts a standard text string with spaces into a fully lowercased string separated by hyphens.")
4. **Domain Rules & Errors:** Include guarantees about how the library handles invalid domain states based on the contract (e.g., "Safely rejects tokens that have passed their expiration date by raising a specific error").

**REQUIRED OUTPUT FORMAT:**

Output **ONLY** a continuous, flat, numbered list. Start at `1.` and list every core guarantee until the contract is fully covered.

