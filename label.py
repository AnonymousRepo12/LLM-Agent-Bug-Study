import json
import re
from typing import Optional, Union
from pydantic import BaseModel, ValidationError
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.chat_models.base import BaseChatModel


class ClassificationResult(BaseModel):
    bug_type: str
    Language: str
    Component: str
    Framework: str
    root_cause: str
    effect: str
    bug_type_rational: str
    root_cause_rational: str
    effect_rational: str


def try_parse_fuzzy_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"raw_response": text}


def classify_post_and_answer(
    post_text: str,
    answer_text: str,
    llm: Optional[Union[BaseChatModel, ChatOpenAI]] = None,
    llm_type: str = "openai"
) -> dict:
    if llm is None:
        raise ValueError("An instantiated LLM must be passed.")
    rational_fields = {
        "bug_type_rational": "A sentence explaining why the selected bug_type was chosen.",
        "root_cause_rational": "A sentence explaining why the selected root_cause was chosen.",
        "effect_rational": "A sentence explaining why the selected effect was chosen."
    }

    classification_fields = {
        "bug_type": [
            'Logic Bug (LB)', 'Configuration Bug (CB)', 'Initialization Bug (IB)', 'Argument Bug (AB)',
            'Parsing Bug (PRB)', 'Prompting Bug (PPB)', 'API Bug (APIB)', 'Reference Bug (RB)', 'Availability Bug (AVB)',
            'Model Bug (MB)', 'Resiyrce Limitation Bug (RLB)'
        ],
        "Language": ['Python', 'Javascript', 'C#'],
        "Component": ['Tools', 'Agent Core', 'Planning', 'Memory'],
        "Framework": [
            'Langchain', 'LlamaIndex', 'CrewAI', 'Semantic Kernel',
            'Autogen', 'LangChain-js', 'Langgraph', 'Custom'
        ],
        "root_cause": [
            'API Misuse-Wrong API Context (AM.WAC)', 'API Misuse-Invalid API Arguments (AM.IAA)',
            'Incorrect or Missing Parameter Value-Incorrect Value (IMP.IV)', 'Incorrect or Missing Parameter Value-Missing Value (IMP.MV)', 
            'Incorrect Data Format-Input Data (IDF.ID)', 'Incorrect Data Format-Output Data (IDF.OD)',
            'Incorrect or Missing Control Flow-Incorrect Flow (IMCF.IF)', 'Incorrect or Missing Control Flow-Missing Flow (IMCF.MF)',
            'Incorrect Instruction-Prompt Specification (II.PS)','Incorrect Instruction-Prompt Orchestration (II.PO)',
            'API Limitation (AL)', 'Component Mismatch (CM)',
            'Requirement Violation (RV)', 'Others'
        ],
        "effect": [
            'Crash', 'Incorrect Output (IO)', 'Empty Response (ER)', 'Output Dump (OD)',
            'Stateless Interaction (SI)', 'Partial Output (PO)', 'Tool Ignored (TI)', 'Slow Output (SO)', 'Warning',
            'Hang', 'Indeterminate Loop (IL)', 'Resource Overuse (RO)', 'Silent Fail (SF)', 'Unknown'
        ]
    }

    BUG_TYPE_DEFINITIONS = {
    "Logic Bug (LB)": "The bug indicates a lack of logical understanding in the pipeline. This bug includes using a function that does not fit the specific task, missing or incorrectly implementing any code segment, or the absence of proper guarding conditions.",
    "Configuration Bug (CB)": "This bug indicates any configuration errors, including parameter misconfiguration or environment misconfiguration.",
    "Initialization Bug (IB)": " Any variable/function may require proper initialization before use. Not initializing the variables/functions correctly before using them or initializing them wrongly (e.g., inside a loop in the wrong way) will cause this error.",
    "Argument Bug (AB)": "This bug indicates issues with the API signature, such as the API expecting specific arguments while the user provides arguments in an incorrect format, or passes extra or missing parameters. It is worth noting that passing an incorrect value to a function that matches its signature will not trigger this bug.",
    "Parsing Bug (PRB)": "This LLM-agent-specific bug occurs while parsing the LLM output. Often, the LLM-generated output format does not align with the parser's structure or the user's expectations, triggering the bug. It mostly occurs in the parser of the LLM agent.",
    "Prompting Bug (PPB)": " This bug is related to the prompts in the LLM. This includes missing prompt variables/components or invoking the LLM with incorrect instructions.",
    "API Bug (APIB)": "This bug is related to the APIs or libraries used to build the agent. Causes include dependency conflicts, incorrect version usage, bugs within the libraries themselves, or trying to use a library without installing it.",
    "Reference Bug (RB)": "In agentic AI, often different libraries implement modules with similar names. This bug occurs when the user refers to a different, deprecated, or missing module from a specific library. This bug mostly occurs in the import stage.",
    "Availability Bug (AVB)": "This bug usually comes from the API or server side, indicating that a particular language model or service is unavailable—either because of a server issue or because the feature has not been released yet.",
    "Model Bug (MB)": "This bug is related to the LLM itself and occurs when a user requests a task the LLM cannot perform, such as asking a chat model to generate an image or using a non-functional model to produce a function call.",
    "Resource Limitation Bug (RLB)": "This bug is related to the user’s local system and its resource usage. It may occur when attempting to run a large LLM with insufficient system resources or limited credits."
    }

    ROOT_CAUSE_DEFINITIONS = {
    "API Misuse-Wrong API Context (AM.WAC)": "The API is used in an inappropriate situation or misunderstanding of its intended purpose. For example, using a translation API to extract sentiment.",
    "API Misuse-Invalid API Arguments (AM.IAA)": "Incorrect types or number of arguments are passed to the API. For instance, passing a string where a JSON object is expected.",
    "Incorrect or Missing Parameter Value-Incorrect Value (IMP.IV)": "A valid parameter is passed, but its value is logically wrong, like using a learning rate of 10 instead of 0.01.",
    "Incorrect or Missing Parameter Value-Missing Value (IMP.MV)": " One or more optional parameters are omitted entirely, often leading to unexpected default behavior.",
    "Incorrect Data Format-Input Data (IDF.ID)": "An error that occurs when the data from an external resource provided to the LLM is not in the expected type, structure, or schema. For example, the input text contains a stop sequence that causes the LLM to terminate its response early.",
    "Incorrect Data Format-Output Data (IDF.OD)": "The expected output format from the LLM is not met. For example, when prompted for structured output, the LLM-generated response may miss required keys or deviate from the format, causing the parser to fail when processing it.",
    "Incorrect or Missing Control Flow-Missing Flow (IMCF.MF)": "A required logical code segment is not implemented, such as a missing if condition or function call.",
    "Incorrect or Missing Control Flow-Incorrect Flow (IMCF.IF)": "This occurs when the logic is present in the code but implemented incorrectly, such as using an if condition that checks the wrong variable.",
    "Incorrect Instruction-Prompt Specification (II.PS)": "Errors in constructing the prompt, such as ambiguous language, poor formatting, or missing instruction cues. It includes four issues in the prompt, including missing context, missing specifications, multiple contexts, and unclear instructions.",
    "Incorrect Instruction-Prompt Orchestration (II.PO)": "Logical flaws in the prompt, such as not passing variables correctly or providing a plain string when a JSON-formatted input is required.",
    "API Limitation (AL)": "Task failure due to limitations of the API or Library, such as unsupported capabilities or service downtime. Users typically cannot control this.",
    "Component Mismatch (CM)": " Incorrect usage or selection of components like LLM, tools, or memory modules, resulting in integration failure.",
    "Requirement Violation (RV)": "Dependency conflicts or missing requirements, such as incompatible library versions or unmet prerequisites.",
    "Others": "Issues not related to LLM agents, often caused by the user’s machine, environment, or external components."
    }

    EFFECT_DEFINITIONS = {
    "Crash": "The program throws an error and stops working.",
    "Incorrect Output (IO)": "LLM generates a complete output, but it does not align with the expected output.",
    "Empty Response (ER)": "The system does not generate an output at all.",
    "Output Dump (OD)": "This effect indicates that the LLM generated the entire output at once instead of streaming it gradually.",
    "Stateless Interaction (SI)": "The agent does not remember the past conversations and answers only the current question without understanding the full context.",
    "Partial Output (PO)": "The LLM generates incomplete or truncated output.",
    "Tool Ignored (TI)": "The effect indicates that the system does not invoke tool(s) during the process.",
    "Slow Output (SO)": "The output is generated slowly.",
    "Warning": "This means the program does not terminate but instead issues a warning.",
    "Hang": "The system ceases to respond to an output.",
    "Indeterminate Loop (IL)": "The system runs into a loop indefinitely.",
    "Resource Overuse (RO)": "This effect indicates that the system consumed high resources like RAM.",
    "Silent Fail (SF)": "This effect illustrates that the agent has failed to perform a task, but did not provide any log that the task failed.",
    "Unknown": "The post does not mention the effect of the problem."
    }
    definations = "Bug Type Definitions:\n" + "\n".join(
        f"{key}: {value}" for key, value in BUG_TYPE_DEFINITIONS.items()
    ) + "\n\n" + \
        "Root Cause Definitions:\n" + "\n".join(
            f"{key}: {value}" for key, value in ROOT_CAUSE_DEFINITIONS.items()
        ) + "\n\n" + \
        "Effect Definitions:\n" + "\n".join(
            f"{key}: {value}" for key, value in EFFECT_DEFINITIONS.items()
        )
    component_definitions = """Tools are external functions or APIs the agent invokes to perform tasks, for example calling a calculator tool to compute 17 × 23.

Agent Core is the orchestrator that interprets user input and directs actions, such as receiving “What’s 5 + 7?” and routing it to the calculator tool before returning “12.”

Planning decomposes complex requests into ordered subtasks, for instance breaking down “Book me a flight” into searching routes, selecting dates, and confirming payment.

Memory stores previous interactions or user preferences to maintain context, like recalling that you’re vegan so it suggests only plant-based recipes later."""
    if llm_type.lower() == "openai":
        function_schema = {
            "name": "classify_post_result",
            "description": "Classify a Stack Overflow post...",
            "parameters": {
                "type": "object",
                "properties": {
                    # Enum-based fields
                    **{
                        key: {
                            "type": "string",
                            "enum": options,
                            "description": f"{key} of the bug"
                        } for key, options in classification_fields.items()
                    },
                    # Free-text rational fields
                    **{
                        key: {
                            "type": "string",
                            "description": desc
                        } for key, desc in rational_fields.items()
                    }
                },
                "required": list(classification_fields.keys()) + list(rational_fields.keys())
            }
        }
        




        system_message = SystemMessage(content=(
            "You are an assistant that reads a Stack Overflow <Post> and its <Answer> "
            "and must call the function 'classify_post_result' with the parameters:\n"
            + ", ".join(classification_fields.keys()) + "\n\n" + definations +"\n\n Component of the LLM agent where the bug occured." + component_definitions 
            +"You also have to provide a rational, a single sentence explaining why you choosed the label, for each classification field in these keys: ["+ ", ".join(rational_fields.keys())+"]\n\n"
        ))
        user_message = HumanMessage(content=f"<Post>{post_text}</Post>\n<Answer>{answer_text}</Answer>")
        response = llm(
            messages=[system_message, user_message],
            functions=[function_schema],
            function_call={"name": "classify_post_result"}
        )
        
        func_call = response.additional_kwargs.get("function_call")
        if func_call and "arguments" in func_call:
            try:
                parsed = json.loads(func_call["arguments"])
                validated = ClassificationResult(**parsed)
                return validated.dict()
            except (json.JSONDecodeError, ValidationError) as e:
                return {"error": str(e), "raw": func_call["arguments"]}
        else:
            return {"raw_response": response.content}

    elif llm_type.lower() == "claude":
        prompt = (
            "You're an assistant that reads a Stack Overflow <Post> and its <Answer>.\n"
            "Return only valid JSON with keys:\n"
            + ", ".join(classification_fields.keys()) + "\n"
            "Example:\n"
            '{ "bug_type": "Prompting Bug (PB)", "Language": "Python", "Component": "Planning", '
            '"Framework": "Langchain", "root_cause": "Incorrect Instruction-Instruction Logic(II.IL)", "effect": "Incorrect Outpu (IO)" } \n\n'+ definations

        )
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"<Post>{post_text}</Post>\n<Answer>{answer_text}</Answer>")
        ]
        response = llm(messages=messages)
        raw = try_parse_fuzzy_json(response.content)

        try:
            validated = ClassificationResult(**raw)
            return validated.dict()
        except ValidationError as e:
            return {"error": str(e), "raw_response": response.content}

    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")
