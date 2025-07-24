import json
import re
import copy
import uuid
import base64
from openai import OpenAI
from django.conf import settings
from rest_framework import status
from .models import UserRequestTrack, PromptUpdateTrack
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import PromptSerializer, GptResponseSerializer


class GptRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GptResponseSerializer(data=request.data)

        content_type_map = {
            "ca_mcq_cpp": "CPP CODE ANALYSIS MCQ",
            "ca_mcq_python": "PYTHON CODE ANALYSIS MCQ",
            "ca_mcq_java": "JAVA CODE ANALYSIS MCQ",
            "ca_mcq_c": "C CODE ANALYSIS MCQ",
            "ca_mcq_javascript": "JAVASCRIPT CODE ANALYSIS MCQ",
            "ca_mcq_sql": "SQL CODE ANALYSIS MCQ",
            "ca_mcq_html_css": "HTML & CSS CODE ANALYSIS MCQ",

            "theory_mcq_html_css": "HTML & CSS THEORY MCQ",
            "theory_mcq_python": "PYTHON THEORY MCQ",
            "theory_mcq_javascript": "JAVASCRIPT THEORY MCQ",
            "theory_mcq_cpp": "CPP THEORY MCQ",
            "theory_mcq_react": "REACT THEORY MCQ",
            "theory_mcq_sql": "SQL THEORY MCQ",
            "theory_mcq_node": "NODE.JS THEORY MCQ",

            "theory_cs_mcq_python": "PYTHON THEORY WITH CODE SNIPPET",
            "theory_cs_mcq_javascript": "JAVASCRIPT THEORY WITH CODE SNIPPET",
            "theory_cs_mcq_cpp": "CPP THEORY WITH CODE SNIPPET",
            "theory_cs_mcq_react": "REACT THEORY WITH CODE SNIPPET",
            "theory_cs_mcq_sql": "SQL THEORY WITH CODE SNIPPET",
            "theory_cs_mcq_node": "NODE.JS THEORY WITH CODE SNIPPET",
        }

        if serializer.is_valid():
            prompt = serializer.validated_data.get("prompt")
            if len(prompt.strip()) > 10:
                response = self.get_response_from_gpt(prompt)

                if response.get("finish_reason", "") != 'stop':
                    return Response({
                                        "error": "GPT was unable to complete the request due to an internal error or because the output exceeded the maximum token limit."},
                                    status=status.HTTP_503_SERVICE_UNAVAILABLE)

                self.save_data(request.user, serializer.validated_data, response, content_type_map)

                return Response({
                    "message": response.get("message"),
                    "input_token": response.get("input_token"),
                    "output_token": response.get("output_token"),
                    "total_token": response.get("total_token"),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid prompt data"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid request body"}, status=status.HTTP_400_BAD_REQUEST)

    def save_data(self, user, request_data, gpt_response_data, content_type_map):

        user_data = UserRequestTrack(
            user=user,
            difficulty=request_data.get("difficulty"),
            question_type=request_data.get("question_type"),
            topic=request_data.get("topic"),
            subtopic=request_data.get("subtopic"),
            question_count=request_data.get("number_of_question"),
            input_token=gpt_response_data.get("input_token"),
            output_token=gpt_response_data.get("output_token")
        )
        user_data.save()

        if request_data.get("is_updated", False) and request_data.get("process_name", None):
            process_name = request_data.get("process_name")
            prompt = request_data.get("prompt")

            prompt_update_data = PromptUpdateTrack(
                user=user,
                original_prompt=self.get_prompt(process_name),
                updated_prompt=prompt,
                content_type=content_type_map.get(process_name)
            )
            prompt_update_data.save()

    def get_prompt(self, request_type):

        file_name = {
            "mcq": "temp.txt",
            "ca_mcq_cpp": "ca_mcq_cpp.txt",
            "ca_mcq_python": "ca_mcq_python.txt",
            "ca_mcq_java": "ca_mcq_java.txt",
            "ca_mcq_c": "ca_mcq_c.txt",
            "ca_mcq_javascript": "ca_mcq_javascript.txt",
            "ca_mcq_sql": "ca_mcq_sql.txt",
            "ca_mcq_html_css": "ca_mcq_html_css.txt",

            "theory_mcq_html_css": "mcq_html_css.txt",
            "theory_mcq_python": "mcq_python.txt",
            "theory_mcq_javascript": "mcq_javascripts.txt",
            "theory_mcq_cpp": "mcq_cpp.txt",
            "theory_mcq_react": "mcq_react.txt",
            "theory_mcq_sql": "mcq_sql.txt",
            "theory_mcq_node": "mcq_node.txt",

            "theory_cs_mcq_python": "cs_mcq_python.txt",
            "theory_cs_mcq_javascript": "cs_mcq_javascript.txt",
            "theory_cs_mcq_cpp": "cs_mcq_cpp.txt",
            "theory_cs_mcq_react": "cs_mcq_react.txt",
            "theory_cs_mcq_sql": "cs_mcq_sql.txt",
            "theory_cs_mcq_node": "cs_mcq_node.txt",
        }

        with open(settings.BASE_DIR / 'prompts' / file_name.get(request_type, 'no_file.txt')) as f:
            return f.read()

    def get_response_from_gpt(self, prompt):

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = {
            "message": completion.choices[0].message.content,
            "input_token": completion.usage.prompt_tokens,
            "output_token": completion.usage.completion_tokens,
            "total_token": completion.usage.total_tokens,
            "finish_reason": completion.choices[0].finish_reason
        }

        return result


class PromptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PromptSerializer(data=request.data)


        if serializer.is_valid():
            try:
                prompt = self.get_prompt(serializer.validated_data.get("process_name"))
                return Response({"prompt": prompt}, status=status.HTTP_200_OK)
            except:
                return Response({"error": "Prompt file not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Invalid Data Passed"}, status=status.HTTP_400_BAD_REQUEST)


    def get_prompt(self, request_type):

        file_name = {
            "mcq": "temp.txt",
            "ca_mcq_cpp": "ca_mcq_cpp.txt",
            "ca_mcq_python": "ca_mcq_python.txt",
            "ca_mcq_java": "ca_mcq_java.txt",
            "ca_mcq_c": "ca_mcq_c.txt",
            "ca_mcq_javascript": "ca_mcq_javascript.txt",
            "ca_mcq_sql": "ca_mcq_sql.txt",
            "ca_mcq_html_css": "ca_mcq_html_css.txt",

            "theory_mcq_html_css": "mcq_html_css.txt",
            "theory_mcq_python": "mcq_python.txt",
            "theory_mcq_javascript": "mcq_javascripts.txt",
            "theory_mcq_cpp": "mcq_cpp.txt",
            "theory_mcq_react": "mcq_react.txt",
            "theory_mcq_sql": "mcq_sql.txt",
            "theory_mcq_node": "mcq_node.txt",

            "theory_cs_mcq_python": "cs_mcq_python.txt",
            "theory_cs_mcq_javascript": "cs_mcq_javascript.txt",
            "theory_cs_mcq_cpp": "cs_mcq_cpp.txt",
            "theory_cs_mcq_react": "cs_mcq_react.txt",
            "theory_cs_mcq_sql": "cs_mcq_sql.txt",
            "theory_cs_mcq_node": "cs_mcq_node.txt",
        }

        with open(settings.BASE_DIR / 'prompts' / file_name.get(request_type, 'no_file.txt')) as f:
            return f.read()


class CodingReplicatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = json.loads(request.body)
        base_questions = data.get('data', None)

        with open(settings.BASE_DIR / 'prompts' / 'coding_replication.txt') as f:
            base_prompt = f.read().strip()

        with open(settings.BASE_DIR / 'prompts' / 'code_refractor.txt') as f:
            code_prompt = f.read().strip()

        if base_questions is not None or not isinstance(base_questions, list):

            replicas = {f"question{i + 1}": [base_questions[i]] for i in range(len(base_questions))}
            input_token, output_token = 0, 0
            try:
                for i, question in enumerate(base_questions):
                    question_text = question['question_text']
                    question_short_text = question['short_text']

                    prompt = base_prompt.format(QUESTION=question_text, SHORT_TEXT=question_short_text)

                    response = self.get_response_from_gpt(prompt)

                    if response.get("finish_reason", "") != 'stop':
                        return Response({
                                            "error": "GPT was unable to complete the request due to an internal error or because the output exceeded the maximum token limit."},
                                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

                    input_token += response.get("input_token")
                    output_token += response.get("output_token")
                    # print(response.get("message"))
                    replicated_questions = json.loads(self.clean_json_string(response.get("message")))
                    print(f"________________________[{request.user.username} {i + 1}]______________________")
                    question_code_data = self.get_code_data(question)
                    for key in replicated_questions.keys():
                        code_data = copy.deepcopy(question_code_data)
                        code_data[0]['question'] = replicated_questions[key][0]

                        code_data_prompt = f"{code_prompt}\n{code_data}"

                        code_response = self.get_response_from_gpt(code_data_prompt)
                        if code_response.get("finish_reason", "") != 'stop':
                            return Response({
                                "error": "GPT was unable to complete the request due to an internal error or because the output exceeded the maximum token limit."},
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)

                        # with open(f'l_{i}_{key}.json', 'w') as f:
                        #     json.dump(code_response.get("message"), f)

                        response_code_data = json.loads(self.clean_json_string(code_response.get("message")))

                        input_token += code_response.get("input_token")
                        output_token += code_response.get("output_token")

                        new_question = copy.deepcopy(question)
                        new_question['question_text'] = replicated_questions[key][0]
                        new_question['short_text'] = replicated_questions[key][1]

                        self.set_code_data(new_question, response_code_data)

                        replicas[f"question{i + 1}"].append(new_question)

                self.save_data(request.user, len(base_questions) * 4, input_token, output_token)

                for key in replicas.keys():
                    for q in replicas.get(key):
                        q_id = str(uuid.uuid4())
                        q['question_id'] = q_id

                        tag_names = [item for item in q['tag_names'] if not self.is_uuid(item)]
                        tag_names.append(q_id)
                        q['tag_names'] = tag_names

                return Response({
                    "message": replicas,
                    "input_token": input_token,
                    "output_token": output_token,
                    "total_token": input_token + output_token,
                }, status=status.HTTP_200_OK)

            except json.JSONDecodeError as e:
                return Response({"error": f"JSONDecodeError: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid request body"}, status=status.HTTP_400_BAD_REQUEST)

    def save_data(self, user, question_count, input_token, output_token):

        user_data = UserRequestTrack(
            user=user,
            question_type="Coding",
            topic="REPLICATION",
            question_count=question_count,
            input_token=input_token,
            output_token=output_token
        )
        user_data.save()

    def get_response_from_gpt(self, prompt):

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = {
            "message": completion.choices[0].message.content,
            "input_token": completion.usage.prompt_tokens,
            "output_token": completion.usage.completion_tokens,
            "total_token": completion.usage.total_tokens,
            "finish_reason": completion.choices[0].finish_reason
        }

        return result

    def clean_json_string(self, raw_str):
        cleaned = re.sub(r'^\s*\w+\s*=\s*', '', raw_str, flags=re.IGNORECASE)
        cleaned = re.sub(r'^```[a-zA-Z]*', '', cleaned)
        cleaned = re.sub(r'```$', '', cleaned)
        cleaned = cleaned.replace('`', '')
        cleaned = cleaned.strip()
        return cleaned

    def is_uuid(self, val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    def encode(self, s):
        return base64.b64encode(str(s).encode('utf-8'))

    def decode(self, s):
        return base64.b64decode(s).decode('utf-8')

    def get_code_data(self, question):
        solutions = {}
        for sol in question.get('solutions')[0].get('code_details'):
            solutions[sol.get('language', 'key')] = (sol.get('code_content', ''))

        prefilled_code = {}
        for sol in question.get('code_metadata'):
            prefilled_code[sol.get('language', 'key')] = sol.get('code_data', '')

        backend_code = {}

        for sol in question.get('language_code_repository_details'):
            file_content = self.decode(sol.get('code_repository')[0].get('file_content'))
            backend_code[sol.get('language', 'key')] = file_content

        return [{
            "question": question.get('question_text'),
            "solutions": solutions,
            "prefilled_code": prefilled_code,
            "backend_code": backend_code,
        }]

    def set_code_data(self, question, code_data):
        for sol in question.get('solutions')[0].get('code_details'):
            sol["code_content"] = code_data[0].get('solutions', 'key').get(sol.get('language', 'key'))

        for sol in question.get('code_metadata'):
            sol["code_data"] = code_data[0].get('prefilled_code', 'key').get(sol.get('language', 'key'))

        for sol in question.get('language_code_repository_details'):
            sol["code_repository"][0]["file_content"] = self.encode(code_data[0].get('backend_code', 'key').get(sol.get('language', 'key')))
