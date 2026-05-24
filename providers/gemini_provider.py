import time
import json
from google import genai
from google.genai import types
from .base_provider import BaseProvider

class GeminiProvider(BaseProvider):
    def _format_messages(self, messages):
        """Translates and strictly groups OpenAI messages into Gemini's alternating structure."""
        system_instruction = None
        gemini_contents = []
        
        current_role = None
        current_parts = []
        
        for msg in messages:
            role = msg.get("role")
            
            # Extract system instructions
            if role == "system":
                system_instruction = msg.get("content")
                continue
            
            # Map OpenAI roles to Gemini roles
            gemini_role = "user" if role in ["user", "tool"] else "model"
            new_parts = []
            
            # 1. Handle Tool Execution Results
            if role == "tool":
                new_parts.append(
                    types.Part.from_function_response(
                        name=msg.get("name", "unknown_tool"),
                        response={"result": msg.get("content", "")}
                    )
                )
            else:
                # 2. Handle Text Content
                content = msg.get("content")
                if content:
                    new_parts.append(types.Part.from_text(text=str(content)))
                
                # 3. Handle Tool Calls made by the assistant
                if role == "assistant" and "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        args = func.get("arguments", "{}")
                        # Safely parse JSON arguments
                        args_dict = json.loads(args) if isinstance(args, str) else args
                        new_parts.append(
                            types.Part.from_function_call(
                                name=func.get("name"),
                                args=args_dict
                            )
                        )
            
            if not new_parts:
                continue

            # Grouping logic: If the role is the same as the current block, combine them!
            if gemini_role == current_role:
                current_parts.extend(new_parts)
            else:
                # Role changed: Save the previous block and start a new one
                if current_role is not None:
                    gemini_contents.append(types.Content(role=current_role, parts=current_parts))
                current_role = gemini_role
                current_parts = new_parts

        # Don't forget to append the final accumulated block
        if current_role is not None:
            gemini_contents.append(types.Content(role=current_role, parts=current_parts))

        return system_instruction, gemini_contents
        
    def _parse_tools(self, tools_list):
        """Translates OpenAI tool schemas into Gemini FunctionDeclarations."""
        if not tools_list:
            return None
            
        declarations = []
        for tool in tools_list:
            if tool.get("type") == "function":
                func = tool["function"]
                declarations.append(
                    types.FunctionDeclaration(
                        name=func["name"],
                        description=func.get("description", ""),
                        parameters=func.get("parameters") # Gemini accepts the standard JSON schema dict
                    )
                )
        return [types.Tool(function_declarations=declarations)] if declarations else None

    def chat_completion(self, messages, model, **kwargs):
        client = genai.Client(api_key=self.api_key)
        sys_inst, contents = self._format_messages(messages)
        gemini_tools = self._parse_tools(kwargs.get("tools"))
        
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_inst,
                temperature=kwargs.get("temperature", 0.7),
                tools=gemini_tools
            )
        )
        
        # Build standard response
        choice_data = {
            "index": 0,
            "message": {"role": "assistant", "content": None},
            "finish_reason": "stop"
        }

        tool_calls = []
        text_content = []

        # Extract text and/or function calls from Gemini's response
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    text_content.append(part.text)
                if part.function_call:
                    tool_calls.append({
                        "id": f"call_{int(time.time())}_{part.function_call.name}",
                        "type": "function",
                        "function": {
                            "name": part.function_call.name,
                            "arguments": json.dumps(part.function_call.args)
                        }
                    })

        if text_content:
            choice_data["message"]["content"] = "".join(text_content)
        if tool_calls:
            choice_data["message"]["tool_calls"] = tool_calls
            choice_data["finish_reason"] = "tool_calls"

        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "model": model,
            "choices": [choice_data]
        }

    def stream_completion(self, messages, model, **kwargs):
        client = genai.Client(api_key=self.api_key)
        sys_inst, contents = self._format_messages(messages)
        gemini_tools = self._parse_tools(kwargs.get("tools"))
        
        stream = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_inst,
                temperature=kwargs.get("temperature", 0.7),
                tools=gemini_tools
            )
        )
        
        for chunk in stream:
            delta = {}
            finish_reason = None

            # 1. Yield any text tokens
            if chunk.text:
                delta["content"] = chunk.text
            
            # 2. Yield any tool calls
            if chunk.function_calls:
                tool_calls_formatted = []
                for index, fc in enumerate(chunk.function_calls):
                    tool_calls_formatted.append({
                        "index": index,
                        "id": f"call_{int(time.time())}_{fc.name}",
                        "type": "function",
                        "function": {
                            "name": fc.name,
                            "arguments": json.dumps(fc.args)
                        }
                    })
                delta["tool_calls"] = tool_calls_formatted
                finish_reason = "tool_calls"

            if delta:
                data = {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion.chunk",
                    "model": model,
                    "choices": [{"delta": delta, "finish_reason": finish_reason}]
                }
                yield f"data: {json.dumps(data)}\n\n"
        
        yield "data: [DONE]\n\n"