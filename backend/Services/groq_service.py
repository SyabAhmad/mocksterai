import json
import groq
import time
import traceback

class GroqService:
    def __init__(self, api_key=None):
        if not api_key:
            raise ValueError("Groq API key is required")

        self.api_key = api_key
        # Ensure the client is initialized correctly
        self.client = groq.Groq(api_key=self.api_key) # Use groq.Groq for newer versions

    def MCP(self, role, prompt, token, model="llama3-70b-8192"):
        """
        Makes a call to the Groq Chat Completion API.

        Args:
            role (str): The system message content (defines the AI's role).
            prompt (str): The user's prompt.
            token (int): The maximum number of tokens for the response.
            model (str): The model to use for the completion.

        Returns:
            str: The content of the response message.

        Raises:
            Exception: If the API call fails.
        """
        try:
            print(f"--- Calling Groq MCP ---")
            print(f"Model: {model}")
            print(f"Role: {role}")
            # print(f"Prompt: {prompt[:200]}...") # Optionally print truncated prompt
            print(f"Max Tokens: {token}")
            print(f"------------------------")

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": role},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=token,
                temperature=0.5, # Keep temperature for controlled generation
                response_format={"type": "json_object"} # Ensure JSON output
            )

            content = response.choices[0].message.content
            print(f"--- Groq MCP Response ---")
            # print(f"Content: {content[:200]}...") # Optionally print truncated content
            print(f"-------------------------")
            return content

        except Exception as e:
            print(f"Error in MCP call: {str(e)}")
            traceback.print_exc() # Print full traceback for debugging
            raise # Re-raise the exception to be handled by the caller

    def generate_interview_questions(self, job_data, user_profile=None, max_retries=2):
        print(f"Starting question generation for {job_data.get('jobTitle')}, {job_data.get('interviewType')} interview")

        # Supported models - prioritize larger models first if retrying
        models_to_try = ["llama3-70b-8192", "llama3-8b-8192", "gemma-7b-it"]
        system_role = "You are an expert interview question generator. Create insightful questions based on the job details provided. Ensure your output is strictly a valid JSON object following the specified structure, with no extra text or explanations."

        for retry_count in range(max_retries + 1):
            selected_model = models_to_try[min(retry_count, len(models_to_try)-1)]
            print(f"Attempt {retry_count + 1}/{max_retries + 1}: Using model: {selected_model}")

            try:
                # Use the build_prompt method to create the prompt
                prompt = self.build_prompt(job_data, user_profile) # Pass user_profile if needed by build_prompt

                # Call MCP with the defined role, prompt, token limit, and selected model
                content = self.MCP(
                    role=system_role,
                    prompt=prompt,
                    token=2000, # Adjust token limit as needed
                    model=selected_model
                )

                # Strip potential leading/trailing whitespace before parsing
                content = content.strip()

                # Parse and validate the JSON response
                json_response = json.loads(content)
                questions = json_response.get('questions', [])

                if not questions or not isinstance(questions, list) or len(questions) == 0:
                    raise ValueError("API returned invalid or empty questions array")

                # Basic validation and default filling (can be enhanced)
                required_fields = ["id", "question", "importance", "tips", "interviewer_expectations", "complexity"]
                validated_questions = []
                for i, q in enumerate(questions):
                    if not isinstance(q, dict):
                        print(f"Warning: Question item {i} is not a dictionary, skipping.")
                        continue
                    # Ensure ID is present and unique (or assign one)
                    q['id'] = q.get('id', i + 1)
                    for field in required_fields:
                        if field not in q or not q[field]:
                             # Provide more specific defaults or handle as error
                            q[field] = q.get(field, f"Default value for {field}")
                    # Ensure complexity is set
                    q['complexity'] = q.get('complexity', 'medium')
                    validated_questions.append(q)

                if not validated_questions:
                     raise ValueError("No valid questions found after validation.")

                print(f"Successfully generated {len(validated_questions)} questions.")
                return validated_questions # Return the validated list

            except json.JSONDecodeError as json_e:
                print(f"Attempt {retry_count + 1}: Failed to parse JSON response: {str(json_e)}")
                print(f"Raw content received: {content}") # Log raw content on JSON error
                # traceback.print_exc() # Optional: print traceback for JSON errors
            except Exception as e:
                print(f"Attempt {retry_count + 1}: Error in GroqService question generation: {str(e)}")
                traceback.print_exc() # Print traceback for other errors

            # Wait before retrying only if it's not the last attempt
            if retry_count < max_retries:
                wait_time = 2 * (retry_count + 1) # Exponential backoff (simple version)
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print(f"Failed to generate questions after {max_retries + 1} attempts.")
                # Return a default error structure or raise a more specific error
                raise ValueError(f"Failed to generate questions after {max_retries + 1} attempts. Last error: {str(e)}")


    def analyze_interview_response(self, question, answer, job_context):
        """
        Analyze an interview answer and provide feedback using MCP.
        """
        system_role = "You are an expert interview coach. Analyze the candidate's answer based on the question, context, and interviewer expectations. Provide constructive feedback formatted strictly as the requested JSON object, with no additional text."
        prompt = f"""
Analyze this interview response for the following question:

Question: {question.get('question', 'N/A')}
Context: This is for a {job_context.get('jobTitle', 'professional')} position, {job_context.get('interviewType', 'general')} interview.
What the interviewer is looking for: {question.get('interviewer_expectations', 'N/A')}

Candidate's answer:
{answer}

Provide constructive feedback including:
1. Exactly 3 specific strengths of the answer (or fewer if not applicable, but aim for 3).
2. Exactly 3 specific areas for improvement (or fewer if not applicable, but aim for 3).
3. A score from 0-100, reflecting the quality of the answer in the given context.
4. A concise summary paragraph (2-4 sentences) with an overall assessment and key advice.

Format your response strictly as a JSON object with NO extra text before or after the JSON:
{{
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "score": <integer_score>,
  "summary": "Overall assessment and advice text here."
}}
Ensure the JSON is valid. Strings must be enclosed in double quotes.
"""
        try:
            # Call MCP for analysis
            content = self.MCP(
                role=system_role,
                prompt=prompt,
                token=1000, # Adjust token limit as needed for feedback
                model="llama3-70b-8192" # Or choose another appropriate model
            )

            # Parse the JSON response
            feedback = json.loads(content.strip())

            # Basic validation (optional but recommended)
            if not all(k in feedback for k in ["strengths", "improvements", "score", "summary"]):
                 raise ValueError("Analysis response missing required keys.")
            if not isinstance(feedback["score"], int):
                 raise ValueError("Analysis score is not an integer.")

            print("Successfully analyzed response.")
            return feedback

        except json.JSONDecodeError as json_e:
            print(f"Error decoding analysis JSON: {str(json_e)}")
            print(f"Raw content received: {content}")
            # Provide a default error feedback structure
            return {
                "strengths": [],
                "improvements": ["Failed to analyze response due to formatting error."],
                "score": 0,
                "summary": "Could not generate feedback due to an internal error."
            }
        except Exception as e:
            print(f"Error generating feedback: {str(e)}")
            traceback.print_exc()
            # Provide a default error feedback structure or re-raise
            raise # Re-raise the exception for the caller to handle


    def build_prompt(self, job_data, user_profile=None):
        """
        Builds the prompt for generating interview questions.
        (user_profile is currently unused but kept for potential future use)
        """
        # Constructing the prompt with clear instructions for JSON structure
        prompt = f"""
Generate exactly 5 interview questions tailored for a candidate applying for the role of '{job_data.get('jobTitle', 'a professional')}'
in the '{job_data.get('companyIndustry', 'relevant')}' industry.
The interview type is '{job_data.get('interviewType', 'general')}'.

Return ONLY a valid JSON object (no introductory text, no explanations, just the JSON) with the following exact structure:
{{
  "questions": [
    {{
      "id": 1,
      "question": "The text of the first interview question.",
      "importance": "Explain why this question is relevant for the role/interview type.",
      "tips": "Provide actionable tips for the candidate on how to approach answering this question.",
      "interviewer_expectations": "Describe what qualities or information the interviewer is looking for in the answer.",
      "complexity": "Estimate the complexity (e.g., 'low', 'medium', 'high')."
    }},
    {{
      "id": 2,
      "question": "The text of the second interview question.",
      "importance": "...",
      "tips": "...",
      "interviewer_expectations": "...",
      "complexity": "..."
    }},
    {{
      "id": 3,
      "question": "The text of the third interview question.",
      "importance": "...",
      "tips": "...",
      "interviewer_expectations": "...",
      "complexity": "..."
    }},
    {{
      "id": 4,
      "question": "The text of the fourth interview question.",
      "importance": "...",
      "tips": "...",
      "interviewer_expectations": "...",
      "complexity": "..."
    }},
    {{
      "id": 5,
      "question": "The text of the fifth interview question.",
      "importance": "...",
      "tips": "...",
      "interviewer_expectations": "...",
      "complexity": "..."
    }}
  ]
}}

Ensure the JSON is strictly valid:
- Keys and string values must be enclosed in double quotes.
- No trailing commas are allowed.
- The output must start with `{{` and end with `}}`.
"""
        return prompt