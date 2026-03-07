"""
training/alpaca_prompt.py
AfriLearn — Alpaca prompt formatter.

Converts dataset rows into the training text format consumed by SFTTrainer.
Imported by train.py and evaluate.py.
"""

ALPACA_TEMPLATE = """\
Below is an instruction for AfriLearn, an offline AI tutor for primary school children in Ghana and Nigeria.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""


def format_prompt(instruction: str, input_text: str, output: str, eos_token: str = "") -> str:
    """
    Format a single dataset row into the full training string.

    Args:
        instruction: The task contract string (includes curriculum anchor).
        input_text:  The runtime student context string.
        output:      The ground truth response.
        eos_token:   Tokenizer EOS token appended to signal end of sequence.

    Returns:
        Fully formatted training string.
    """
    return ALPACA_TEMPLATE.format(
        instruction=instruction.strip(),
        input=input_text.strip(),
        output=output.strip(),
    ) + eos_token


def format_inference_prompt(instruction: str, input_text: str) -> str:
    """
    Format a prompt for inference (no output section — model generates this).

    Args:
        instruction: Task contract.
        input_text:  Runtime context.

    Returns:
        Prompt string ending after '### Response:' — model completes from here.
    """
    return (
        "Below is an instruction for AfriLearn, an offline AI tutor for primary school children in Ghana and Nigeria.\n\n"
        f"### Instruction:\n{instruction.strip()}\n\n"
        f"### Input:\n{input_text.strip()}\n\n"
        "### Response:\n"
    )


def batch_format(examples: dict, tokenizer) -> dict:
    """
    Map function for HuggingFace datasets.map() — formats a batch of rows.

    Args:
        examples: Dict of lists (batched dataset format from datasets.map).
        tokenizer: Loaded tokenizer (for eos_token).

    Returns:
        Dict with 'text' field containing formatted strings.
    """
    texts = [
        format_prompt(inst, inp, out, eos_token=tokenizer.eos_token)
        for inst, inp, out in zip(
            examples["instruction"],
            examples["input"],
            examples["output"],
        )
    ]
    return {"text": texts}
